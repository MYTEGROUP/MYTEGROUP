# helpers/helper.py

import json
import os
from config import STORAGE_DIR
from threading import Lock

# Lock to prevent race conditions during file writes
write_lock = Lock()

# Helper to load data from a JSON file
def load_json(filename):
    filepath = os.path.join(STORAGE_DIR, filename)
    with open(filepath, 'r') as file:
        return json.load(file)

# Helper to save data to a JSON file with thread-safe access
def save_json(filename, data):
    filepath = os.path.join(STORAGE_DIR, filename)
    with write_lock:
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)
