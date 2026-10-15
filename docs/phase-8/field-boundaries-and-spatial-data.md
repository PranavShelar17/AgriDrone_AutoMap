# Field Boundaries & Spatial Data Architecture

## 1. Overview
Field boundaries define the legal, agronomic, and spatial perimeter of agricultural operations. AgriDrone AutoMap avoids hardcoded coordinates and synthetic polygon assumptions by leveraging native **PostgreSQL + PostGIS** vector geometries.

---

## 2. PostGIS Database Schema
Field spatial boundaries are stored in the `fields` table using GeoAlchemy2:

```python
class Field(Base):
    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    farm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("farms.id"))
    field_name: Mapped[str] = mapped_column(String(150), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(100), nullable=True)
    area_hectares: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    boundary_geom = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
```

Surveys also maintain optional flight coverage geometry (`coverage_geom`).

---

## 3. Boundary GeoJSON API (`/api/v1/maps/fields/{field_id}/boundary`)
The endpoint retrieves the spatial boundary using native PostGIS JSON serialization (`ST_AsGeoJSON`):

```sql
SELECT ST_AsGeoJSON(boundary_geom) FROM fields WHERE id = :field_id;
```

### Response Structure (`FieldBoundaryGeoJSON`):
```json
{
  "type": "Feature",
  "id": "8343f2b0-90cf-4a30-b688-97e47a4a3a3b",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[74.58, 18.15], [74.59, 18.15], [74.59, 18.16], [74.58, 18.16], [74.58, 18.15]]]
  },
  "bbox": [74.58, 18.15, 74.59, 18.16],
  "centroid": [74.585, 18.155],
  "properties": {
    "field_id": "8343f2b0-90cf-4a30-b688-97e47a4a3a3b",
    "field_name": "Sugarcane North Block 1",
    "crop_type": "Sugarcane Co 86032",
    "area_hectares": 12.5,
    "farm_id": "31fcdc9c-702d-4509-b10d-8900be80cb9c",
    "farm_name": "Shree Ganesh Agro Farm"
  }
}
```

---

## 4. MapLibre Vector Styling
On the MapLibre canvas, the boundary is rendered as two synchronized layers:
1. **Translucent Fill (`field-boundary-fill`)**:
   - `fill-color`: Emerald `#10b981`
   - `fill-opacity`: `0.12` (subtle tinting that does not obscure underlying crop pixels)
2. **Dashed Stroke (`field-boundary-line`)**:
   - `line-color`: High-contrast emerald `#059669`
   - `line-width`: `2.5px`
   - `line-dasharray`: `[3, 2]`
   - Drawn on top of the raster layer so boundary lines remain crisp and distinct.

---

## 5. Handling Missing or Invalid Boundaries
- If a field record does not have a boundary geometry in PostGIS, the API returns a structured `404 Not Found` with detail: `"Field 'Name' does not have a recorded spatial boundary."`
- The frontend gracefully displays `"No Geometry Recorded"` and centers the map based on the raster product's GeoTIFF bounds instead of fabricating fake coordinates.
