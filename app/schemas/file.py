from typing import Optional

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    original_crs: Optional[str] = None
    projected_crs: Optional[str] = None
    status: str


class MeasurementResponse(BaseModel):
    feature_id: int
    geometry_type: str
    measurement: Optional[float] = None
    unit: Optional[str] = None


class MeasurementsListResponse(BaseModel):
    file_id: str
    measurements: list[MeasurementResponse]