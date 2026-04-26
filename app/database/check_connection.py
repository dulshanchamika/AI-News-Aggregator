import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.connection import get_database_info, engine
from sqlalchemy import text

if __name__ == "__main__":
    db_info = get_database_info()

    print(f"\n{'=' * 60}")
    print(f"Database Connection Check")
    print(f"{'=' * 60}")
    print(f"Environment: {db_info['environment']}")
    print(f"Database_URL: {db_info['url_masked']}")
    print(f"Host: {db_info['host']}")
    print(f"{'=' * 60}\n")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Connection successful!")
                print(f"Successfully connected to the {db_info['environment']} database.")
            else:
                print("❌ Connection successful, but query failed.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")