import os
import pymysql

S3_BUCKET                       = "coms4156-strategies"
S3_LOCATION                     = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)
SECRET_KEY                      = os.urandom(16)
USER_SERVICE_USER               = os.environ.get('USER_SERVICE_USER')
USER_SERVICE_PASSWORD           = os.environ.get('USER_SERVICE_PASSWORD')
S3_ACCESS_KEY                   = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY                   = os.environ.get('S3_SECRET_KEY')
S3_REGION                       = 'us-east-1'
SQLALCHEMY_DATABASE_URI         = f'mysql+pymysql://{USER_SERVICE_USER}:{USER_SERVICE_PASSWORD}@user-service-db.ci3ta0leimzm.us-east-2.rds.amazonaws.com:3306/backtest'
ALLOWED_EXTENSIONS              = {'py'}  # allowed upload file extension
SQLALCHEMY_TRACK_MODIFICATIONS  = False
DEBUG                           = True
PORT                            = 5000