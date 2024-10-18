#here we will initialize the .env file variables, to be used throughout our code.
# config.py

import os

# Define the storage directory path
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'storage'))
