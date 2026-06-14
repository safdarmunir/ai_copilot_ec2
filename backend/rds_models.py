from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from rds_database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())