import aioboto3

from core.config import settings

session = aioboto3.Session()


def SessionOSS():
    return session.client(
        's3',
        endpoint_url=settings.S3_API_ENDPOINT,
        aws_access_key_id=settings.S3_API_ACCESS_KEY,
        aws_secret_access_key=settings.S3_API_SECRET_KEY,
    )
