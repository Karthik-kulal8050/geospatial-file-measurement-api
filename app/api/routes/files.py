from pathlib import Path
import shutil
import json
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import FileRecord, Measurement

from app.services.file_processor import (
    read_geospatial_file,
    prepare_projected_gdf,
)

from app.services.measurement import calculate_measurements

from app.schemas.file import (
    FileResponse,
    MeasurementResponse,
    MeasurementsListResponse,
)


router = APIRouter(
    prefix="/api/files",
    tags=["Files"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".kml", ".zip"}


@router.post("/", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required."
        )
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .kml and .zip files are supported"
        )

    file_path = UPLOAD_DIR / file.filename

    try:

        # 1. Save physical file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if file_path.stat().st_size == 0:
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )
        # 2. Read geospatial file
        gdf = read_geospatial_file(str(file_path))

        # 3. Handle CRS
        projected_gdf, original_crs = prepare_projected_gdf(gdf)

        # 4. Calculate measurements
        measurements = calculate_measurements(projected_gdf)

        # 5. Create file database record
        file_record = FileRecord(
            filename=file.filename,
            original_crs=original_crs,
            projected_crs=str(projected_gdf.crs),
            feature_count=len(projected_gdf),
            status="COMPLETED",
        )

        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        # 6. Save individual measurements
        for result in measurements:

            measurement_record = Measurement(
                file_id=file_record.id,
                feature_id=result["feature_id"],
                geometry_type=result["geometry_type"],
                geometry=json.dumps(result["geometry"]),
                properties=json.dumps(result["properties"], default=str),
                measurement=result["measurement"],
                unit=result["unit"],
            )

            db.add(measurement_record)

        db.commit()

        return {
            "id": file_record.id,
            "filename": file_record.filename,
            "feature_count": file_record.feature_count,
            "original_crs": file_record.original_crs,
            "projected_crs": file_record.projected_crs,
            "status": file_record.status,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
):
    file_record = (
        db.query(FileRecord)
        .filter(FileRecord.id == file_id)
        .first()
    )

    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return {
        "id": file_record.id,
        "filename": file_record.filename,
        "feature_count": file_record.feature_count,
        "original_crs": file_record.original_crs,
        "projected_crs": file_record.projected_crs,
        "status": file_record.status,
    }


@router.get("/{file_id}/measurements", response_model=MeasurementsListResponse)
def get_measurements(
    file_id: str,
    db: Session = Depends(get_db),
):
    # Check whether the file exists
    file_record = (
        db.query(FileRecord)
        .filter(FileRecord.id == file_id)
        .first()
    )

    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    # Get measurements belonging to this file
    measurements = (
        db.query(Measurement)
        .filter(Measurement.file_id == file_id)
        .all()
    )

    return {
        "file_id": file_id,
        "measurements": [
            {
                "feature_id": m.feature_id,
                "geometry_type": m.geometry_type,
                "geometry": json.loads(m.geometry) if m.geometry else None,
                "properties": json.loads(m.properties) if m.properties else None,
                "measurement": m.measurement,
                "unit": m.unit
            }
            for m in measurements
        ]
    }