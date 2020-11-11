import os

SECRET_KEY                  = os.environ.get("DB_SECRET_COMS4156")
SQLALCHEMY_DATABASE_URI     = 'sqlite:///alchemist.db'
