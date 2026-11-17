from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()

try:
    users = db.query(User).all()

    print("\n===== REGISTERED MAATRICARE USERS =====\n")

    if not users:
        print("No registered users found.")

    for user in users:
        print(f"ID: {user.id}")
        print(f"Name: {user.full_name}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role.name}")
        print(f"Active: {user.is_active}")
        print("-" * 40)

finally:
    db.close()