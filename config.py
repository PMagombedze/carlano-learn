import os


class Config:
    """Base config"""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_URI")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    UPLOADS_FOLDER = os.environ.get("UPLOAD_FOLDER")
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_APP_PASSWORD")
    MINIFY_HTML = True
    CACHE_TYPE = "SimpleCache"
