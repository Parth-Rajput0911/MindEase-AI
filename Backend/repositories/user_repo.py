"""
Repository for User database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from Backend.models.user import User
from Backend.schemas.user import UserCreate, UserUpdate


class UserRepository:
    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            full_name=user_in.full_name,
            hashed_password=user_in.password,  # In real auth, hash before storing
            is_active=user_in.is_active,
            emergency_contact_name=user_in.emergency_contact_name,
            emergency_contact_phone=user_in.emergency_contact_phone,
            emergency_contact_email=user_in.emergency_contact_email,
        )
        db.add(db_user)
        db.flush()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
        user = db.get(User, user_id)
        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.flush()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        user = db.get(User, user_id)
        if not user:
            return False
        db.delete(user)
        db.flush()
        return True
