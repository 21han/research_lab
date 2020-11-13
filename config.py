import os

# SECRET_KEY               = os.environ.get("DB_SECRET_COMS4156")
SQLALCHEMY_DATABASE_URI     = 'sqlite:///alchemist.db'
ALLOWED_EXTENSIONS          = {'py'}  # allowed upload file extension
SECRET_KEY                  = os.urandom(32)
DEBUG                       = True
PORT                        = 5000
