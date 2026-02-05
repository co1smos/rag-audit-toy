from sqlalchemy import text
from db.session import engine
from db.models import Base

def init_db():
    with engine.begin() as conn:
        print("DEBUG: db engine started")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    Base.metadata.create_all(bind=engine)
