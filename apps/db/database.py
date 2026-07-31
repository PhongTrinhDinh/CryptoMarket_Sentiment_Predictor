import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "phong")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "18082005")
POSTGRES_DB = os.getenv("POSTGRES_DB", "market_sentiment_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                SELECT create_hypertable('market_data', 'timestamp', if_not_exists => TRUE);
                """))
            conn.commit()
            print("TimescaleDB Hypertable successfully set up!")
        except Exception as e:
            print(f"Note (Skip if not using TimescaleDB): {e}")
            
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()