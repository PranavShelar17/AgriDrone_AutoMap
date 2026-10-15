import io
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import get_current_user, verify_survey_access
from app.models.tenant import User, UserRole
from app.models.survey import Survey
from app.models.file import SurveyFile
from app.services.storage import get_storage_service, build_blob_path, sanitize_filename
from app.services.validation import validator
from app.schemas.ingestion import FileUploadResponse, SurveyFileListResponse

router = APIRouter()


@router.post(
    "/upload/{survey_id}",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and validate a drone photography file or GeoTIFF raster",
)
async def upload_survey_file(
    survey_id: uuid.UUID,
    file: UploadFile = File(..., description="Aerial imagery file (.jpg, .tif, .tiff, .zip)"),
    workflow_mode: str = Form("raw_photos", description="'raw_photos' for photogrammetry or 'geotiff' for direct GIS"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileUploadResponse:
    # 1. Enforce valid relationship: target survey must exist and user must have permission
    if current_user.role == UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers do not have permission to upload survey files.",
        )
    survey = verify_survey_access(survey_id, current_user, db)

    # 2. Read file content safely
    raw_content = await file.read()
    filename = file.filename or "unnamed_upload.dat"
    safe_name = sanitize_filename(filename)

    # 3. Server-side validation (magic bytes, EXIF, GeoTIFF, size, extension)
    validation_res = validator.validate_file(
        file_bytes=raw_content,
        original_filename=safe_name,
        declared_mime=file.content_type,
        expected_workflow=workflow_mode,
    )

    # 4. Stream to configured storage service (Azure Blob or local fallback)
    storage = get_storage_service()
    blob_path = build_blob_path(str(survey_id), safe_name)
    container = settings.AZURE_CONTAINER_RAW

    try:
        storage_res = storage.upload_file(
            file_obj=io.BytesIO(raw_content),
            container=container,
            blob_path=blob_path,
            content_type=validation_res["mime_type"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed: {str(e)}",
        )

    # 5. Persist record in database
    metadata_payload = {
        **validation_res.get("metadata", {}),
        "workflow_route": validation_res["workflow_route"],
        "storage_provider": storage_res["provider"],
        "validation_errors": validation_res["validation_errors"],
    }

    # Check for duplicate file under the same survey
    existing_file = (
        db.query(SurveyFile)
        .filter(SurveyFile.survey_id == survey.id, SurveyFile.original_filename == safe_name)
        .first()
    )

    if existing_file:
        # Update existing record
        existing_file.file_type = validation_res["file_type"]
        existing_file.file_size_bytes = storage_res["file_size_bytes"]
        existing_file.mime_type = validation_res["mime_type"]
        existing_file.blob_uri = storage_res["blob_uri"]
        existing_file.md5_checksum = storage_res["md5_checksum"]
        existing_file.validation_metadata = metadata_payload
        existing_file.ingestion_status = validation_res["ingestion_status"]
        db.commit()
        db.refresh(existing_file)
        file_record = existing_file
    else:
        file_record = SurveyFile(
            survey_id=survey.id,
            original_filename=safe_name,
            file_type=validation_res["file_type"],
            file_size_bytes=storage_res["file_size_bytes"],
            mime_type=validation_res["mime_type"],
            blob_uri=storage_res["blob_uri"],
            md5_checksum=storage_res["md5_checksum"],
            validation_metadata=metadata_payload,
            ingestion_status=validation_res["ingestion_status"],
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)

    # 6. Update survey state if validated
    if validation_res["is_valid"] and survey.status == "DRAFT":
        survey.status = "INGESTED"
        db.commit()

    return FileUploadResponse(
        file_id=file_record.id,
        survey_id=file_record.survey_id,
        original_filename=file_record.original_filename,
        file_type=file_record.file_type,
        file_size_bytes=file_record.file_size_bytes,
        mime_type=file_record.mime_type,
        blob_uri=file_record.blob_uri,
        md5_checksum=file_record.md5_checksum,
        ingestion_status=file_record.ingestion_status,
        workflow_route=validation_res["workflow_route"],
        validation_metadata=metadata_payload,
        validation_errors=validation_res["validation_errors"],
        created_at=file_record.created_at,
    )


@router.get(
    "/surveys/{survey_id}/files",
    response_model=SurveyFileListResponse,
    summary="List all uploaded files for a survey",
)
def list_survey_files(
    survey_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SurveyFileListResponse:
    survey = verify_survey_access(survey_id, current_user, db)

    files = db.query(SurveyFile).filter(SurveyFile.survey_id == survey_id).order_by(SurveyFile.created_at.desc()).all()

    items = []
    total_bytes = 0
    validated_count = 0
    rejected_count = 0

    for f in files:
        total_bytes += f.file_size_bytes
        if f.ingestion_status == "VALIDATED":
            validated_count += 1
        elif f.ingestion_status == "REJECTED":
            rejected_count += 1

        meta = f.validation_metadata or {}
        items.append(
            FileUploadResponse(
                file_id=f.id,
                survey_id=f.survey_id,
                original_filename=f.original_filename,
                file_type=f.file_type,
                file_size_bytes=f.file_size_bytes,
                mime_type=f.mime_type,
                blob_uri=f.blob_uri,
                md5_checksum=f.md5_checksum,
                ingestion_status=f.ingestion_status,
                workflow_route=meta.get("workflow_route", "NONE"),
                validation_metadata=meta,
                validation_errors=meta.get("validation_errors", []),
                created_at=f.created_at,
            )
        )

    return SurveyFileListResponse(
        survey_id=survey_id,
        items=items,
        total_files=len(items),
        total_bytes=total_bytes,
        validated_count=validated_count,
        rejected_count=rejected_count,
    )


@router.delete(
    "/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an uploaded file from storage and database",
)
def delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.query(SurveyFile).filter(SurveyFile.id == file_id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found.",
        )

    if current_user.role == UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers do not have permission to delete survey files.",
        )

    verify_survey_access(file_record.survey_id, current_user, db)

    # Attempt removal from storage
    storage = get_storage_service()
    blob_path = build_blob_path(str(file_record.survey_id), file_record.original_filename)
    try:
        storage.delete_file(settings.AZURE_CONTAINER_RAW, blob_path)
    except Exception:
        pass

    db.delete(file_record)
    db.commit()
    return None


@router.get(
    "/download/{container}/{blob_path:path}",
    summary="Local development direct file download endpoint",
)
def local_download(
    container: str,
    blob_path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    storage = get_storage_service()
    if storage.provider_name != "local_dev":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct local download is only active for local development storage adapter.",
        )

    # Verify authorization for farmer
    if current_user.role == UserRole.FARMER:
        prefix = blob_path.split("/")[0]
        verified = False
        try:
            survey_uuid = uuid.UUID(prefix)
            verify_survey_access(survey_uuid, current_user, db)
            verified = True
        except (ValueError, HTTPException):
            verified = False

        if not verified:
            sf = db.query(SurveyFile).filter(SurveyFile.blob_uri.contains(blob_path)).first()
            if sf:
                verify_survey_access(sf.survey_id, current_user, db)
            else:
                from app.models.product import MapProduct
                mp = db.query(MapProduct).filter(MapProduct.blob_uri.contains(blob_path)).first()
                if mp:
                    from app.api.deps import verify_map_product_access
                    verify_map_product_access(mp.id, current_user, db)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="File not found or unauthorized.",
                    )

    try:
        data = storage.download_file(container, blob_path)
        return Response(content=data, media_type="application/octet-stream")
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found in local storage.")
