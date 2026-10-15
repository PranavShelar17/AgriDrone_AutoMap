import uuid
from app.models import (
    User,
    UserRole,
    Farm,
    Field,
    Survey,
    SurveyFile,
    PhotogrammetryTask,
    Algorithm,
    MapProduct,
    Report,
    AuditLog,
)


def test_user_model_instantiation():
    """Verify that User model instantiates with proper defaults and enums."""
    user = User(
        email="farmer@agridrone.local",
        password_hash="hashed_secret",
        full_name="Ramesh Patil",
        role=UserRole.FARMER,
        is_active=True
    )
    assert user.email == "farmer@agridrone.local"
    assert user.role == UserRole.FARMER
    assert user.is_active is True


def test_farm_and_field_instantiation():
    """Verify Farm and Field model structures."""
    user_id = uuid.uuid4()
    farm = Farm(
        owner_id=user_id,
        name="Baramati Precision Sugarcane Farm",
        village="Malegaon Kh",
        district="Pune",
        state="Maharashtra"
    )
    assert farm.name == "Baramati Precision Sugarcane Farm"
    assert farm.owner_id == user_id

    field = Field(
        farm=farm,
        field_name="North Parcel A",
        crop_type="Sugarcane",
        area_hectares=15.64
    )
    assert field.field_name == "North Parcel A"
    assert field.area_hectares == 15.64
    assert field.farm == farm


def test_survey_and_files_instantiation():
    """Verify Survey and SurveyFile model structures."""
    survey = Survey(
        survey_code="SRV-2026-TEST-001",
        flight_date="2026-10-14",
        drone_model="DJI Mavic 3 Enterprise",
        sensor_type="RGB",
        status="DRAFT"
    )
    file_record = SurveyFile(
        survey=survey,
        original_filename="DJI_001.JPG",
        file_type="RAW_IMAGE",
        file_size_bytes=14298100,
        mime_type="image/jpeg",
        blob_uri="raw-surveys/srv-001/DJI_001.JPG",
        ingestion_status="PENDING"
    )
    assert survey.survey_code == "SRV-2026-TEST-001"
    assert file_record.original_filename == "DJI_001.JPG"
    assert file_record.survey == survey
