"""
test utils
"""
from utils import rds
from utils import s3_util
from config import S3_BUCKET


def test_rds_connection():
    """
    test rds connection opened
    """
    conn = rds.get_connection()
    assert conn.open
    # do we need to do close?


def test_s3_client_connection():
    """
    test s3 client is opened and the bucket exists
    """
    s3_client = s3_util.init_s3_client()
    response = s3_client.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]
    assert S3_BUCKET in bucket_names


def test_s3_resource_connection():
    """
    test s3 resource is opened and the bucket exists
    """
    s3_resource = s3_util.init_s3()
    assert s3_resource.Bucket(S3_BUCKET) in s3_resource.buckets.all()