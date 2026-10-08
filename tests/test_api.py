from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Geospatial File Measurement API is running"
    )


def test_invalid_file_type():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.txt",
                b"This is not a geospatial file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only .kml and .zip files are supported"
    )


def test_file_not_found():
    response = client.get(
        "/api/files/non-existent-id"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_measurements_file_not_found():
    response = client.get(
        "/api/files/non-existent-id/measurements"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_kml_upload_and_measurements():
    with open("tests/sample.kml", "rb") as file:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "sample.kml",
                    file,
                    "application/vnd.google-earth.kml+xml",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "sample.kml"
    assert data["feature_count"] == 3
    assert data["original_crs"] == "EPSG:4326"
    assert data["status"] == "COMPLETED"

    file_id = data["id"]

    measurement_response = client.get(
        f"/api/files/{file_id}/measurements"
    )

    assert measurement_response.status_code == 200

    measurement_data = measurement_response.json()

    assert len(measurement_data["measurements"]) == 3

    for item in measurement_data["measurements"]:
        assert "geometry" in item
        assert "properties" in item
        assert item["geometry"] is not None
        assert item["properties"] is not None

    measurements = measurement_data["measurements"]

    polygon = next(
        item for item in measurements
        if item["geometry_type"] == "Polygon"
    )

    line = next(
        item for item in measurements
        if item["geometry_type"] == "LineString"
    )

    point = next(
        item for item in measurements
        if item["geometry_type"] == "Point"
    )

    assert polygon["measurement"] is not None
    assert polygon["unit"] == "m²"

    assert line["measurement"] is not None
    assert line["unit"] == "m"

    assert point["measurement"] is None
    assert point["unit"] is None


def test_shapefile_zip_upload():
    with open("tests/test_shapefile.zip", "rb") as file:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "sample_shapefile.zip",
                    file,
                    "application/zip",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "sample_shapefile.zip"
    assert data["feature_count"] == 3
    assert data["original_crs"] == "EPSG:4326"
    assert data["status"] == "COMPLETED"

    file_id = data["id"]

    measurement_response = client.get(
        f"/api/files/{file_id}/measurements"
    )

    assert measurement_response.status_code == 200

    measurement_data = measurement_response.json()

    assert len(measurement_data["measurements"]) == 3


def test_invalid_zip_file():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "invalid.zip",
                b"This is not a real ZIP file",
                "application/zip",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "The uploaded ZIP file is invalid or corrupted."
    )


def test_empty_file():
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "empty.kml",
                b"",
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Uploaded file is empty."
    )


def test_missing_crs():
    import geopandas as gpd
    from shapely.geometry import Polygon

    gdf = gpd.GeoDataFrame(
        {
            "name": ["Test Polygon"]
        },
        geometry=[
            Polygon([
                (77.59, 12.97),
                (77.60, 12.97),
                (77.60, 12.98),
                (77.59, 12.98),
            ])
        ],
        crs=None,
    )

    assert gdf.crs is None

    from app.services.file_processor import prepare_projected_gdf

    try:
        prepare_projected_gdf(gdf)
        assert False, "Expected ValueError for missing CRS"
    except ValueError as e:
        assert str(e) == "The uploaded file does not contain a CRS."


