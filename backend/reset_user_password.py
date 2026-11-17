from getpass import getpass

from app.database import SessionLocal
from app.models.user import User
from app.security.password import hash_password


def reset_user_password():

    db = SessionLocal()

    try:
        print("\n===== MAATRICARE.AI PASSWORD RESET =====\n")

        # Get registered user's email
        email = input("Enter registered email: ").strip().lower()

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            print("\nError: No registered user found with this email.")
            return

        print(f"\nUser found: {user.full_name}")
        print(f"Role: {user.role.name}")

        # Get new password securely
        new_password = getpass("\nEnter new password: ")

        if len(new_password) < 8:
            print("\nError: Password must contain at least 8 characters.")
            return

        confirm_password = getpass("Confirm new password: ")

        if new_password != confirm_password:
            print("\nError: Passwords do not match.")
            return

        # Generate secure password hash
        user.password_hash = hash_password(new_password)

        # Save changes
        db.commit()

        print("\nPassword updated successfully!")

    except Exception as e:
        db.rollback()
        print(f"\nAn error occurred: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    reset_user_password()