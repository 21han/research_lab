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


def test_s3_get_backtest_data():
    """
    test get backtest date works for sample test data user_id = 0
    """
    backtest_df = rds.get_all_backtests(0)
    assert backtest_df.shape[0] != 0


def test_s3_get_backtest_data_invalid_user():
    """
    test get backtest date should not work for invalid user id (-1)
    """
    backtest_df = rds.get_all_backtests(-1)
    assert backtest_df.shape[0] == 0


def test_s3_get_all_colation():
    """
    test get location of backtest results works for valid test data user_id = 0
    """
    backtest_df = rds.get_all_backtests(0)
    strategy_ids = [str(id) for id in list(backtest_df['strategy_id'])]
    location = rds.get_all_locations(strategy_ids)
    assert location.shape[0] != 0
