import os
import uuid
import boto3
from fastapi import UploadFile
from botocore.exceptions import ClientError


class S3Service:
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.region = os.getenv("AWS_REGION", "ap-south-1")

        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME is not configured")

        self.client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def upload_file(self, file: UploadFile) -> dict:
        try:
            extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
            s3_key = f"uploads/{uuid.uuid4()}.{extension}"

            self.client.upload_fileobj(
                file.file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": file.content_type or "application/octet-stream"
                },
            )

            return {
                "original_filename": file.filename,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "content_type": file.content_type,
            }

        except ClientError as error:
            raise RuntimeError(f"S3 upload failed: {str(error)}")