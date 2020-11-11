import os

SECRET_KEY                  = os.environ.get("DB_SECRET_COMS4156")
SQLALCHEMY_DATABASE_URI     = 'sqlite:///alchemist.db'
ALLOWED_EXTENSIONS          = {'py'}  # allowed upload file extension
GITHUB_TOKEN                = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO                 = '4156-test-upload'
GITHUB_PREFIX               = 'https://github.com/linxiaow/'