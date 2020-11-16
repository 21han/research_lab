"""
reference:
    https://stackoverflow.com/questions/42641315/s3-urls-get-bucket-name-and-path
"""

from urllib.parse import urlparse
import os
import boto3


def init_s3():
    """
    uinit s3 resource
    :return:
    """
    s3_resource = boto3.resource(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY")
    )
    return s3_resource


def init_s3_client():
    """
    init s3 client
    :return:
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY")
    )
    return s3_client


class S3Url:
    """
    >>> s = S3Url("s3://bucket/hello/world")
    >>> s.bucket
    'bucket'
    >>> s.key
    'hello/world'
    >>> s.url
    's3://bucket/hello/world'

    >>> s = S3Url("s3://bucket/hello/world?qwe1=3#ddd")
    >>> s.bucket
    'bucket'
    >>> s.key
    'hello/world?qwe1=3#ddd'
    >>> s.url
    's3://bucket/hello/world?qwe1=3#ddd'

    >>> s = S3Url("s3://bucket/hello/world#foo?bar=2")
    >>> s.key
    'hello/world#foo?bar=2'
    >>> s.url
    's3://bucket/hello/world#foo?bar=2'
    """

    def __init__(self, url):
        self._parsed = urlparse(url, allow_fragments=False)

    @property
    def bucket(self):
        """
        get bucket
        :return:
        """
        return self._parsed.netloc

    @property
    def key(self):
        """
        get key
        :return:
        """
        if self._parsed.query:
            return self._parsed.path.lstrip('/') + '?' + self._parsed.query
        return self._parsed.path.lstrip('/')

    @property
    def url(self):
        """
        get url
        :return:
        """
        return self._parsed.geturl()
