"""
test utils
"""
from utils import rds
from utils import s3_util
from utils import mock_historical_data
from config import S3_BUCKET
import pytest
import logging


def test_rds_connection():
    """
    test rds connection opened
    """
    conn = rds.get_connection()
    assert conn.open
    conn.close()


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

def test_mock_data_basics():
    """
    test mock data has
    (1) none empty universe
    (2) reasonable balance
    :return:
    """
    mock = mock_historical_data.MockData()
    assert(len(mock.universe) > 0)
    logging.info("we have valid mock universe length")
    assert(mock.balance > 0)
    logging.info("we have valid balance amount")


def test_mock_data_get_balance():
    """
    test if the mock data has a balance that makes sense
    :return:
    """
    mock = mock_historical_data.MockData()
    assert(mock.get_balance() > 0)
    logging.info("mock balance is not negative")


def test_mock_data_get_price():
    """
    test if mock data return valid price
    :return:
    """
    mock = mock_historical_data.MockData()

    with pytest.raises(ValueError):
        mock.get_price(None, "BTC")

    with pytest.raises(ValueError):
        mock.get_price('2020-11-12', None)

    with pytest.raises(ValueError):
        mock.get_price('2020-11-12', "MYSTERY")

    assert(mock.get_price('2020-11-12', 'BTC') > 0)
    assert(mock.get_price('2020-11-12', 'ETH') > 0)
    assert(mock.get_price('2020-11-12', 'BNB') > 0)
    assert(mock.get_price('2020-11-12', 'EOS') > 0)
    assert(mock.get_price('2020-11-12', 'ATOM') > 0)
    assert(mock.get_price('2020-11-12', 'USDT') > 0)


def test_get_all_strategies():
    """
    to test `get_all_strategies` method.
    :return:
    """
    all_strats = rds.get_all_strategies(0)
    assert(len(all_strats) >= 0)
    assert(len(all_strats.columns) == 5)


def test_get_all_backtests():
    """
    to test all backtests
    :return:
    """
    all_backtests = rds.get_all_backtests(0)
    assert(len(all_backtests) >= 0)
    assert(len(all_backtests.columns) == 5)


def test_get_all_locations():
    """
    to test get all locations
    :return:
    """
    all_locations = rds.get_all_locations([0, 1, 2])
    assert(len(all_locations) >= 0)
    assert(len(all_locations.columns) == 2)


def test_init_s3():
    """
    test if we can init s3
    :return:
    """
    s3 = s3_util.init_s3()
    assert("Bucket" in s3.get_available_subresources())
    s3_client = s3_util.init_s3_client()
    buckets = s3_client.list_buckets()
    assert(type(buckets) == dict)
    assert(len(buckets['Buckets']) >= 0)
    buckets_name = s3_client.list_buckets()['Buckets']
    buckets_name = [i['Name'] for i in buckets_name]
    assert("coms4156-strategies" in buckets_name)


def test_s3_url():
    """
    test s3 url
    :return:
    """
    s3 = s3_util.S3Url("s3://bucket/hello/world")
    assert(s3.bucket == 'bucket')
    assert(s3.key == 'hello/world')
    assert(s3.url == 's3://bucket/hello/world')
    s3 = s3_util.S3Url("s3://bucket/hello/world#foo?bar=2")
    assert(s3.key == 'hello/world#foo?bar=2')
    assert(s3.url == 's3://bucket/hello/world#foo?bar=2')
