import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    filename = Column(String, nullable=False)
    original_crs = Column(String, nullable=True)
    projected_crs = Column(String, nullable=True)
    feature_count = Column(Integer, default=0)
    status = Column(String, nullable=False)

    measurements = relationship(
        "Measurement",
        back_populates="file",
        cascade="all, delete-orphan"
    )


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False)

    feature_id = Column(Integer, nullable=False)
    geometry_type = Column(String, nullable=False)

    # Store geometry and feature attributes as JSON text
    geometry = Column(Text, nullable=True)
    properties = Column(Text, nullable=True)

    measurement = Column(Float, nullable=True)
    unit = Column(String, nullable=True)

    file = relationship(
        "FileRecord",
        back_populates="measurements"
    )