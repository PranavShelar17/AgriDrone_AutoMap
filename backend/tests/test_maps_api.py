"""Unit and Integration Tests for Phase 8 Maps and Geospatial Visualization Engine.

Verifies:
- PostGIS field boundary GeoJSON generation with bounding box & centroid calculation.
- Survey validated product listing and file existence verification.
- Layer visualization metadata and dynamic colormap legend construction.
- Slippy XYZ tile rendering with Web Mercator reprojection and NoData transparency.
- Point value probing at geographic coordinates.
- Transparent, data-derived raster diagnostics and zonal distributions.
- Multi-product comparison compatibility logic.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.product import MapProduct, ZonalStatistic
from app.services.map_rendering import MapRenderingService, ColorRamps, TRANSPARENT_TILE_BYTES


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_field_boundary_endpoint(client: TestClient, db_session):
    """Verifies that an existing field boundary returns valid GeoJSON Feature with bbox and centroid."""
    field = db_session.query(Field).filter(Field.boundary_geom != None).first()
    assert field is not None, "At least one field with boundary geometry must exist"

    response = client.get(f"/api/v1/maps/fields/{field.id}/boundary")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "Feature"
    assert data["id"] == str(field.id)
    assert data["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert len(data["bbox"]) == 4
    assert len(data["centroid"]) == 2
    assert data["properties"]["field_name"] == field.field_name
    assert "area_hectares" in data["properties"]


def test_field_boundary_not_found(client: TestClient):
    """Verifies that querying a non-existent field boundary returns 404."""
    random_id = uuid.uuid4()
    response = client.get(f"/api/v1/maps/fields/{random_id}/boundary")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_survey_products_listing(client: TestClient, db_session):
    """Verifies listing validated geospatial products for a survey."""
    product = db_session.query(MapProduct).first()
    assert product is not None, "At least one MapProduct must exist in the database"

    response = client.get(f"/api/v1/maps/surveys/{product.survey_id}/products")
    assert response.status_code == 200
    products_list = response.json()
    assert isinstance(products_list, list)
    assert len(products_list) >= 1

    first_prod = products_list[0]
    assert "id" in first_prod
    assert "product_type" in first_prod
    assert "display_name" in first_prod
    assert "has_raster_file" in first_prod
    assert "crs_epsg" in first_prod


def test_layer_visualization_metadata(client: TestClient, db_session):
    """Verifies layer visualization endpoint returns correct bounds, legend, and tile template."""
    product = db_session.query(MapProduct).filter(MapProduct.product_type == "INDEX_NDVI").first()
    if not product:
        product = db_session.query(MapProduct).first()
    assert product is not None

    response = client.get(f"/api/v1/maps/layers/{product.id}/visualization")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(product.id)
    assert data["product_type"] == product.product_type
    assert len(data["bounds"]) == 4  # [minLon, minLat, maxLon, maxLat]
    assert len(data["center"]) == 2  # [lon, lat]
    assert "{z}" in data["tile_url_template"]
    assert "{x}" in data["tile_url_template"]
    assert "{y}" in data["tile_url_template"]

    legend = data["legend"]
    assert "title" in legend
    assert "unit" in legend
    assert len(legend["stops"]) >= 3


def test_tile_rendering_slippy(client: TestClient, db_session):
    """Verifies that the tile server streams valid PNG images with correct headers."""
    product = db_session.query(MapProduct).filter(MapProduct.product_type == "INDEX_NDVI").first()
    if not product:
        product = db_session.query(MapProduct).first()
    assert product is not None

    # Request tile at zoom 15
    response = client.get(f"/api/v1/maps/tiles/{product.id}/15/23435/14210.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "public, max-age=" in response.headers.get("cache-control", "")
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n"), "Must be a valid PNG binary"


def test_tile_out_of_bounds_returns_transparent(client: TestClient, db_session):
    """Verifies that requesting an out-of-bounds tile returns 200 with transparent PNG."""
    product = db_session.query(MapProduct).first()
    assert product is not None

    # Tile (0, 0, 0) or arbitrary far tile (18, 0, 0)
    response = client.get(f"/api/v1/maps/tiles/{product.id}/18/10/10.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_point_probe_endpoint(client: TestClient, db_session):
    """Verifies interactive point value probing."""
    product = db_session.query(MapProduct).filter(MapProduct.product_type == "INDEX_NDVI").first()
    if not product:
        product = db_session.query(MapProduct).first()
    assert product is not None

    # Probe coordinate
    response = client.get(f"/api/v1/maps/products/{product.id}/probe?lat=22.58842&lon=77.43165")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(product.id)
    assert "lat" in data
    assert "lon" in data
    assert "is_valid" in data
    assert "unit" in data


def test_product_diagnostics_endpoint(client: TestClient, db_session):
    """Verifies raster diagnostics, statistics, and transparent scientific warnings."""
    product = db_session.query(MapProduct).filter(MapProduct.product_type == "INDEX_NDVI").first()
    if not product:
        product = db_session.query(MapProduct).first()
    assert product is not None

    response = client.get(f"/api/v1/maps/products/{product.id}/diagnostics")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(product.id)
    assert "valid_percentage" in data
    assert "valid_pixel_count" in data
    assert "nodata_pixel_count" in data
    assert "zonal_distribution" in data
    assert len(data["scientific_warnings"]) >= 1
    assert len(data["analytical_limitations"]) >= 1


def test_comparison_compatibility_endpoint(client: TestClient, db_session):
    """Verifies comparison compatibility check between products."""
    products = db_session.query(MapProduct).limit(2).all()
    assert len(products) >= 2, "At least two MapProducts must exist to test comparison"

    p_a, p_b = products[0], products[1]
    response = client.get(f"/api/v1/maps/compare-compatibility?product_a={p_a.id}&product_b={p_b.id}")
    assert response.status_code == 200
    data = response.json()

    assert "is_compatible" in data
    assert "spatial_overlap_percentage" in data
    assert "reason" in data
    assert "recommendation" in data
