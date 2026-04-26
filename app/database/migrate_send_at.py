import os
import sys
from pathlib import Path
from sqlalchemy import text
from dotenv import load_dotenv

# Ensure the root directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()

from app.database.connection import get_session, get_database_info

def run_migration():
    db_info = get_database_info()
    
    if db_info['environment'] == 'production' or db_info['url_masked'] != 'localhost':
        print("\n⚠️  WARNING: You are about to migrate the PRODUCTION database.")
        print(f"Host: {db_info['host']}")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Migration cancelled.")
            return

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
