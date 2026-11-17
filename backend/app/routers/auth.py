from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.role import Role

from app.schemas.auth import UserRegister, UserLogin, TokenResponse

from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.security.dependencies import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================
# USER REGISTRATION
# ==========================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    # Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Prevent public Medical Officer registration
    requested_role = user_data.role.strip().upper()

    if requested_role == "MEDICAL_OFFICER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Medical Officer accounts must be created by an administrator"
        )

    # Find requested role
    role = db.query(Role).filter(
        Role.name == requested_role
    ).first()

    if not role or requested_role not in ["ASHA", "ANM"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Allowed roles: ASHA, ANM"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password,
        role_id=role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "full_name": new_user.full_name,
        "email": new_user.email,
        "role": role.name
    }


# ==========================================
# USER LOGIN
# ==========================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):

    # Find user by email
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Verify credentials
    if not user or not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive"
        )

    # Generate JWT access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.name
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==========================================
# GET CURRENT LOGGED-IN USER
# ==========================================

@router.get(
    "/me",
    status_code=status.HTTP_200_OK
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):

    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role.name,
        "is_active": current_user.is_active
    }