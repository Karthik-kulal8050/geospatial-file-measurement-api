# Geospatial File Measurement API

A backend service built with **FastAPI** for uploading and processing geospatial files and calculating measurements for supported geometries.

The API accepts **KML files** and **ZIP files containing Shapefiles**, processes their geometries, handles coordinate reference systems (CRS), calculates polygon areas and LineString lengths, and stores file and measurement information in SQLite.

## Features

- Upload KML files
- Upload ZIP files containing Shapefiles
- Extract and process geospatial features using GeoPandas
- Detect and preserve the original CRS
- Transform geographic CRS data into an appropriate projected CRS before measurement
- Calculate:
  - Polygon → Area in square metres (`m²`)
  - LineString → Length in metres (`m`)
  - Point → No measurement required
- Gracefully handle unsupported geometries
- Store processed file information and measurements in SQLite
- REST API with Swagger/OpenAPI documentation
- Automated tests using pytest
- Docker support

## Technology Stack

- **Python 3.13**
- **FastAPI** — REST API framework
- **GeoPandas** — geospatial data processing
- **Shapely** — geometry operations
- **PyProj** — CRS and coordinate transformations
- **Fiona** — geospatial file I/O
- **SQLAlchemy** — database ORM
- **SQLite** — database
- **Pydantic** — API response validation
- **Pytest** — automated testing
- **Docker** — containerization

## Project Structure

```text
geospatial-file-measurement-api/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       └── files.py
│   │
│   ├── services/
│   │   ├── file_processor.py
│   │   └── measurement.py
│   │
│   ├── schemas/
│   │   └── file.py
│   │
│   └── db/
│       ├── database.py
│       └── models.py
│
├── tests/
│   ├── test_api.py
│   ├── sample.kml
│   └── sample_shapefile.zip
│
├── uploads/
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

## API Endpoints

### 1. Upload and Process File

```http
POST /api/files/
```

Accepts:

- `.kml`
- `.zip` containing a Shapefile

Example response:

```json
{
  "id": "95399665-d7da-4720-a866-79854c64d706",
  "filename": "sample.kml",
  "feature_count": 3,
  "original_crs": "EPSG:4326",
  "projected_crs": "EPSG:32643",
  "status": "COMPLETED"
}
```

### 2. Get File Information

```http
GET /api/files/{file_id}
```

Returns metadata about a previously processed file.

### 3. Get Measurements

```http
GET /api/files/{file_id}/measurements
```

Returns measurements calculated for the features in the file.

Example:

```json
{
  "file_id": "95399665-d7da-4720-a866-79854c64d706",
  "measurements": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "measurement": 1201683.91,
      "unit": "m²"
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "measurement": 1550.42,
      "unit": "m"
    },
    {
      "feature_id": 2,
      "geometry_type": "Point",
      "measurement": null,
      "unit": null
    }
  ]
}
```

## File Processing Flow

The processing pipeline is:

```text
Upload File
     ↓
Validate Extension
     ↓
Save File
     ↓
Check File Content
     ↓
Read KML / Extract ZIP
     ↓
Load Geospatial Data
     ↓
Validate CRS
     ↓
Transform to Projected CRS
     ↓
Calculate Measurements
     ↓
Store Results in SQLite
     ↓
Return API Response
```

### KML Processing

For a KML file, GeoPandas reads the file directly and creates a GeoDataFrame containing the features and their geometries.

### Shapefile Processing

For a ZIP file:

1. The ZIP archive is validated.
2. The archive is safely extracted.
3. The application searches for `.shp` files.
4. A single Shapefile is required.
5. The Shapefile is loaded using GeoPandas.

ZIP files containing unsafe paths, invalid archives, no Shapefile, or multiple Shapefiles are rejected.

## CRS Handling

Coordinate Reference Systems are important because geographic coordinates such as latitude and longitude are generally represented in degrees.

For example:

```text
EPSG:4326
```

is a geographic CRS using latitude/longitude coordinates.

Area and distance should not be calculated directly using degree-based coordinates.

The application therefore:

1. Reads the original CRS.
2. Checks whether it is geographic.
3. Estimates a suitable UTM projected CRS.
4. Transforms the GeoDataFrame into that projected CRS.
5. Performs area and length calculations using the projected coordinates.

For example, the sample data uses:

```text
Original CRS: EPSG:4326
Projected CRS: EPSG:32643
```

The projected CRS provides metre-based coordinates suitable for the measurement calculations.

If the uploaded file does not contain a CRS, processing is rejected rather than guessing the coordinate system.

## Measurement Calculation

The application supports the following geometry types:

| Geometry | Calculation | Unit |
|---|---|---|
| Polygon | Area | m² |
| LineString | Length | m |
| Point | No measurement | — |
| Other/unsupported | No measurement | — |

Unsupported geometries are handled gracefully and do not cause the entire request to fail.

## Database Design

The application uses SQLite with SQLAlchemy.

### Files Table

Stores information about uploaded files:

- File ID
- Filename
- Original CRS
- Projected CRS
- Feature count
- Processing status

### Measurements Table

Stores measurements associated with each processed file:

- Measurement ID
- File ID
- Feature ID
- Geometry type
- Measurement
- Unit

The relationship is:

```text
Files
  │
  └── 1 ──────────── N ── Measurements
```

## Error Handling

The API handles invalid input and processing errors including:

- Unsupported file extension
- Empty uploaded file
- Invalid/corrupted ZIP file
- ZIP without a Shapefile
- ZIP containing multiple Shapefiles
- Unsafe ZIP paths
- Missing CRS
- File ID not found
- Unsupported geometry types

Appropriate HTTP status codes are returned for client errors and server errors.

## Testing

Automated tests are implemented using pytest.

The test suite covers:

- Root endpoint
- Invalid file type
- File not found
- Measurements endpoint for missing file
- KML upload and processing
- Polygon/LineString/Point measurements
- ZIP/Shapefile upload
- Invalid ZIP
- Empty file
- Missing CRS

Run the tests with:

```bash
pytest
```

Expected result:

```text
9 passed
```

## Running Locally

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd geospatial-file-measurement-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

### 5. Open Swagger

```text
http://127.0.0.1:8000/docs
```

## Running with Docker

Build the image:

```bash
docker build -t geospatial-api .
```

Run the container:

```bash
docker run -d -p 8000:8000 --name geospatial-api geospatial-api
```

Then open:

```text
http://localhost:8000/docs
```

## Design Decisions

### FastAPI

FastAPI was selected because it provides:

- Simple REST API development
- Automatic OpenAPI/Swagger documentation
- Pydantic-based request/response validation
- Good support for Python-based services

### GeoPandas

GeoPandas provides a convenient abstraction for reading and processing geospatial datasets while working naturally with Shapely geometries and CRS transformations.

### SQLite

SQLite was selected because the assignment requires persistence but does not require a separate database server. It keeps the project simple while demonstrating database modelling and relationships.

### UTM Projection

When the source CRS is geographic, the application estimates an appropriate UTM CRS instead of hardcoding a single projection. This makes the measurement logic more suitable for data from different geographic locations.

## Future Scope

Possible improvements include:

- Support for additional geospatial formats such as GeoJSON
- Support for MultiPolygon and MultiLineString measurements
- Asynchronous/background processing for large files
- File size limits and streaming uploads
- PostgreSQL/PostGIS for production-scale geospatial storage
- Authentication and authorization
- Cloud object storage for uploaded files
- Pagination for large measurement results
- More detailed processing status tracking
- Deployment using a cloud platform

## Learning Outcomes

This project provided practical experience with:

- REST API development using FastAPI
- Geospatial data processing
- CRS and coordinate transformations
- Geometry-based measurements
- File upload and validation
- ZIP archive handling
- SQLAlchemy database modelling
- Automated API testing
- Docker containerization
- API documentation using Swagger/OpenAPI
- Designing a modular backend architecture