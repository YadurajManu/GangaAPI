import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gangadrsihti")  # Your database name
DB_USER = os.getenv("DB_USER", "sujeetkumarsingh")  # Default PostgreSQL user
DB_PASSWORD = os.getenv("DB_PASSWORD", "Yadu@1234")  # Update with your actual password

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Image Storage
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./images")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB

# Database URL - URL encode the password to handle special characters
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
