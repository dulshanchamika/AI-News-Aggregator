import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Ensure the app directory is in the path
sys.path.insert(0, os.getcwd())
load_dotenv()

from app.database.connection import get_session

def run_migration():
    session = get_session()
    try:
        # Check if column exists
        # This is a bit engine specific, assuming sqlite or postgres
        # We can just run ALTER TABLE and catch the error if it already exists
        session.execute(text("ALTER TABLE digests ADD COLUMN sent_at TIMESTAMP;"))
        session.commit()
        print("Migration successful: added sent_at column to digests table.")
    except Exception as e:
        session.rollback()
        print(f"Migration error (column might already exist): {e}")

if __name__ == "__main__":
    run_migration()
