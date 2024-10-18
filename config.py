import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the storage directory path
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'storage'))

# Notification service configurations
EMAIL_API_KEY = os.getenv('EMAIL_API_KEY')  # API key for email notification service
SMS_API_KEY = os.getenv('SMS_API_KEY')      # API key for SMS notification service

# Fact-checking service configurations
FACT_CHECKING_API_KEY = os.getenv('FACT_CHECKING_API_KEY')  # API key for fact-checking service

# Frontend-backend communication configurations
FRONTEND_URL = os.getenv('FRONTEND_URL')  # URL for the frontend application
BACKEND_URL = os.getenv('BACKEND_URL')    # URL for the backend application

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # API key for OpenAI services

# Additional configurations can be added here as needed

# Ensure all required environment variables are set
required_vars = [
    'EMAIL_API_KEY',
    'SMS_API_KEY',
    'FACT_CHECKING_API_KEY',
    'FRONTEND_URL',
    'BACKEND_URL',
    'OPENAI_API_KEY'
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configuration settings are now accessible throughout the application

# End of config.py