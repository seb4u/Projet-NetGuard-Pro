from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from models import Base

# Créer la base SQLite
DATABASE_URL = "sqlite:///netguard.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Créer toutes les tables
Base.metadata.create_all(bind=engine)

print("✅ Base de données netguard.db créée avec succès.")

# ✅ Fonction utilisée dans les endpoints FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
