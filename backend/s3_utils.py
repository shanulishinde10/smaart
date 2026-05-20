import os
import boto3
from botocore.exceptions import ClientError

S3_BUCKET = os.environ.get('S3_BUCKET_NAME', '')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def _client():
    return boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    )


def upload_face(file_bytes: bytes, key: str) -> str:
    """Upload face image bytes to S3. Returns the S3 key."""
    _client().put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType='image/jpeg',
    )
    return key


def delete_face(key: str):
    """Delete a face image from S3. Silently ignores missing objects."""
    try:
        _client().delete_object(Bucket=S3_BUCKET, Key=key)
    except ClientError:
        pass


def get_face_url(key: str) -> str:
    """Return the public HTTPS URL for an S3 key."""
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
