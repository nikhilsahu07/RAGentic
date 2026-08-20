from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.logger import get_logger

log = get_logger(__name__)


class S3Client:
    """Thin boto3 wrapper that works with both real AWS S3 and local MinIO.

    Set S3_ENDPOINT_URL=http://minio:9000 for MinIO; leave None for real AWS.
    """

    def __init__(self) -> None:
        kwargs: dict = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.S3_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the bucket if it doesn't exist (mainly for MinIO local dev)."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code in ("404", "NoSuchBucket"):
                try:
                    if settings.AWS_REGION == "us-east-1" or settings.S3_ENDPOINT_URL:
                        self._client.create_bucket(Bucket=self._bucket)
                    else:
                        self._client.create_bucket(
                            Bucket=self._bucket,
                            CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
                        )
                    log.info("s3_bucket_created", bucket=self._bucket)
                except ClientError as create_exc:
                    log.error("s3_bucket_create_failed", error=str(create_exc))
            else:
                log.error("s3_head_bucket_failed", error=str(exc))

    def upload_file(self, local_path: str, s3_key: str) -> None:
        """Upload a local file to S3 under the given key."""
        self._client.upload_file(Filename=local_path, Bucket=self._bucket, Key=s3_key)
        log.info("s3_uploaded", key=s3_key, bucket=self._bucket)

    def upload_fileobj(self, fileobj, s3_key: str, content_type: str = "application/pdf") -> None:
        """Upload a file-like object to S3."""
        self._client.upload_fileobj(
            fileobj,
            self._bucket,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        log.info("s3_uploaded_fileobj", key=s3_key, bucket=self._bucket)

    def generate_presigned_url(self, s3_key: str, expiry: int = 3600) -> str:
        """Generate a pre-signed GET URL valid for expiry seconds."""
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": s3_key},
            ExpiresIn=expiry,
        )
        return url

    def is_connected(self) -> bool:
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return True
        except Exception:
            return False


# Module-level singleton
s3_client = S3Client()
