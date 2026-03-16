import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
RES_DATA_DIR = os.path.join(PROJECT_ROOT, "res", "data")


def load_data_file(filename: str) -> list:
    filepath = os.path.join(RES_DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []
