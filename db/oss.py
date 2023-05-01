import aioboto3


def SessionOSS():
    session = aioboto3.Session()
    return session.client(
        's3',
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )
