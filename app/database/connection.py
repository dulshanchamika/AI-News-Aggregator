import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
        
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ai_news_aggregator")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()

def get_database_info() -> dict:
    env = os.getenv("ENVIRONMENT", "local")
    url = get_database_url()
    
    # Simple masking for display
    # postgresql://user:password@host:port/db
    masked_url = url
    host = "localhost"
    try:
        if "@" in url:
            parts = url.split("@")
            auth_part = parts[0]
            host_part = parts[1]
            
            auth_prefix = auth_part.split(":")[0] + ":****" if ":" in auth_part[13:] else "****"
            masked_url = f"{auth_prefix}@{host_part}"
            host = host_part.split(":")[0]
    except Exception:
        pass

    return {
        "environment": env,
        "url_masked": masked_url,
        "host": host
    }
