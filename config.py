import os
import dotenv


class Config:
    """Base config"""

    dotenv.load_dotenv()

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_URI")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
