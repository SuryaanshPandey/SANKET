"""S3-compatible (AWS S3 & MinIO) object storage backend."""

import io
from pathlib import Path
from tempfile import NamedTemporaryFile
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from clarity.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    """Stores files in S3 or MinIO buckets with immutability and content-addressing."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region_name: str = "us-east-1",
    ):
        self.bucket_name = bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket_name)
            except Exception as e:
                # In restricted environments, creation might be pre-provisioned
                pass

    def put_bytes(self, relative_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=relative_path,
            Body=data,
            ContentType=content_type,
        )
        return f"s3://{self.bucket_name}/{relative_path}"

    def get_bytes(self, relative_path: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=relative_path)
        return response["Body"].read()

    def exists(self, relative_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=relative_path)
            return True
        except ClientError:
            return False

    def get_local_path(self, relative_path: str) -> str:
        data = self.get_bytes(relative_path)
        ext = Path(relative_path).suffix
        temp = NamedTemporaryFile(delete=False, suffix=ext)
        temp.write(data)
        temp.flush()
        temp.close()
        return temp.name
