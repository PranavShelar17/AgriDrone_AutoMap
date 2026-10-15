from sqlalchemy import text
from sqlalchemy.orm import Session


def test_postgis_extension_available(db_session: Session):
    """Integration test verifying PostGIS extension functions on the running database."""
    result = db_session.execute(text("SELECT PostGIS_Version();")).fetchone()
    assert result is not None
    version_str = result[0]
    assert "3." in version_str
    assert "USE_GEOS=1" in version_str


def test_spatial_query_execution(db_session: Session):
    """Verify that PostGIS geometry functions execute correctly."""
    query = text("SELECT ST_AsText(ST_MakePoint(74.581, 18.152));")
    result = db_session.execute(query).fetchone()
    assert result is not None
    assert result[0] == "POINT(74.581 18.152)"
