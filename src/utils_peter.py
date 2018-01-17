import json
import os

def load_json(path):
    with open(path, 'r') as f:
        obj = json.load(f)
    return obj


def save_json(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=4, sort_keys=True)


def base_name(path):
    base = os.path.basename(path)
    return os.path.splitext(base)[0]
