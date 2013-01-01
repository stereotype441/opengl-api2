import json
import os.path


JSON_PATH = os.path.join(os.path.dirname(__file__), 'master.json')


# Read the master database
def read_database():
    with open(JSON_PATH, 'r') as f:
        return json.load(f)


def write_database(db):
    with open(JSON_PATH, 'w') as f:
        json.dump(db, f, sort_keys=True, indent=2)
