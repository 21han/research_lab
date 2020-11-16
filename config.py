import os
import pymysql

SECRET_KEY                      = os.urandom(16)
USER_SERVICE_USER               = os.environ.get('USER_SERVICE_USER')
USER_SERVICE_PASSWORD           = os.environ.get('USER_SERVICE_PASSWORD')
SQLALCHEMY_DATABASE_URI         = f'mysql+pymysql://{USER_SERVICE_USER}:{USER_SERVICE_PASSWORD}@user-service-db.ci3ta0leimzm.us-east-2.rds.amazonaws.com:3306/backtest'
ALLOWED_EXTENSIONS              = {'py'}  # allowed upload file extension
SQLALCHEMY_TRACK_MODIFICATIONS  = False
DEBUG                           = True
PORT                            = 5000
