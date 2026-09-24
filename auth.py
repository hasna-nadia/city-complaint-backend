from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

from database import SessionLocal
from models import Users


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


SECRET_KEY = "city-complaint-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


class CreateUser(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)


class LoginUser(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)


class ForgotPassword(BaseModel):
    email: str = Field(min_length=5)
    new_password: str = Field(min_length=6)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def create_access_token(email: str, role: str):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": email,
        "role": role,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(Users).filter(
        Users.email == email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


@router.post("/signup")
def signup(
    user: CreateUser,
    db: Session = Depends(get_db)
):

    try:
        existing_user = db.query(Users).filter(
            Users.email == user.email
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        new_user = Users(
            name=user.name,
            email=user.email,
            password=bcrypt_context.hash(
                user.password
            ),
            role="user"
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Signup is temporarily unavailable"
        )

    return {
        "message": "User created successfully"
    }


@router.post("/login")
def login(
    user: LoginUser,
    db: Session = Depends(get_db)
):

    db_user = db.query(Users).filter(
        Users.email == user.email
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not bcrypt_context.verify(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        db_user.email,
        db_user.role
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role
    }


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPassword,
    db: Session = Depends(get_db)
):

    user = db.query(Users).filter(
        Users.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.password = bcrypt_context.hash(
        data.new_password
    )

    db.commit()

    return {
        "message": "Password updated successfully"
    }


@router.get("/me")
def get_me(
    current_user: Users = Depends(
        get_current_user
    )
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }