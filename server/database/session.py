from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = None  # fourni par étudiant A

engine = None
SessionLocal = None

def init_db():
    global engine, SessionLocal
    if DATABASE_URL is None:
        raise RuntimeError("DATABASE_URL non fournie")

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
