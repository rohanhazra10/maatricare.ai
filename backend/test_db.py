from sqlalchemy import text
from app.database import engine

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")
    except Exception as exc:
        print("Database connection failed:", exc)
        raise
