import os

SECRET_KEY                  = os.urandom(16)
SQLALCHEMY_DATABASE_URI     = 'jdbc:mysql://user-service-db.ci3ta0leimzm.us-east-2.rds.amazonaws.com:3306'
ALLOWED_EXTENSIONS          = {'py'}  # allowed upload file extension
DEBUG                       = True
PORT                        = 5000
