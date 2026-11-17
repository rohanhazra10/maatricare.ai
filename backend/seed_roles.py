from app.database import SessionLocal
from app.models import Role

DEFAULT_ROLES = [
    ("ASHA", "Accredited Social Health Activist"),
    ("ANM", "Auxiliary Nurse Midwife"),
    ("MEDICAL_OFFICER", "Medical Officer responsible for clinical supervision"),
    ("ADMIN", "System administrator"),
]

def seed_roles():
    db = SessionLocal()
    try:
        for name, description in DEFAULT_ROLES:
            if not db.query(Role).filter(Role.name == name).first():
                db.add(Role(name=name, description=description))
        db.commit()
        print("Default roles are ready.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_roles()
