import platform
import os

class Config:
    # Common configurations
    DB_HOST = os.environ.get('DB_HOST', 'bezufa1rhnyqaefkvkqo-mysql.services.clever-cloud.com')  # AWS RDS endpoint
    DB_NAME = 'bezufa1rhnyqaefkvkqo'

    # Detect the operating system
    system = platform.system()

    if system == 'Windows':
        # Windows-specific settings
        DB_USER = os.environ.get('DB_USER', 'udicfm3ei7jpyfx8')  # Default user for Windows
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'h2rq5GfSphPYr7x7gDUJ')  # Default password for Windows
        DB_PORT = '3306'  # Default port
    elif system == 'Darwin':
        # macOS-specific settings
        DB_USER = os.environ.get('DB_USER', 'udicfm3ei7jpyfx8')  # Default user for macOS
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'h2rq5GfSphPYr7x7gDUJ')  # Default password for macOS
        DB_PORT = '3306'  # Default port
    else:
        # Default for Linux or CI/CD environments
        DB_USER = os.environ.get('DB_USER', 'udicfm3ei7jpyfx8')  # Replace with your RDS username
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'h2rq5GfSphPYr7x7gDUJ')  # Replace with your RDS password
        DB_PORT = '3306'  # Keep the same port

    # SQLAlchemy connection URI for MySQL
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class Testconfig:
    TESTING = True
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    # Common configurations
    DB_HOST = 'localhost'
    DB_NAME = 'wfh_test'

    # Detect the operating system
    system = platform.system()

    if system == 'Windows':
        # Windows-specific settings
        DB_USER = 'root' 
        DB_PASSWORD = '' 
        DB_PORT = '3306' 
    elif system == 'Darwin':
        # macOS-specific settings
        DB_USER = 'root'  # Default user for macOS
        DB_PASSWORD ='root'  # Default password for macOS
        DB_PORT = '8889'  # Default port
    else:
        # Default for Linux or CI/CD environments
        DB_USER = os.environ.get('DB_USER', 'root')  # Default user for CI/CD
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root')  # Default password for CI/CD
        DB_PORT = '3306'  # Keep the same port

    # SQLAlchemy connection URI for MySQL
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    