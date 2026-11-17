"""Create all current model tables for a local/demo database.

For managed deployments use `alembic upgrade head` instead.
"""
from app.database import Base, engine
import app.models  # noqa: F401 - registers every model

def init_db():
    Base.metadata.create_all(bind=engine)
    print("MAATRICARE database tables are ready.")

if __name__ == "__main__":
    init_db()
