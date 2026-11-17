"""
Create a Medical Officer account.

Run from the backend folder:
    python create_medical_officer.py
"""
import getpass

from app.database import SessionLocal
from app.models import Role, User
from app.security.password import hash_password


def main():
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password (min 8 characters): ")

    if len(full_name) < 2 or "@" not in email or len(password) < 8:
        print("Invalid input. Nothing was created.")
        return

    db = SessionLocal()

    try:
        if db.query(User).filter(User.email == email).first():
            print("That email is already registered.")
            return

        role = db.query(Role).filter(Role.name == "MEDICAL_OFFICER").first()

        if not role:
            print("Role MEDICAL_OFFICER not found. Run: python seed_roles.py")
            return

        db.add(User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role_id=role.id
        ))
        db.commit()

        print(f"Medical Officer created: {email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
