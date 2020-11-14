import os

SECRET_KEY                      = os.urandom(16)
SQLALCHEMY_DATABASE_URI         = 'sqlite:///alchemist.db'
ALLOWED_EXTENSIONS              = {'py'}  # allowed upload file extension
SQLALCHEMY_TRACK_MODIFICATIONS  = False
DEBUG                           = True
PORT                            = 5000
