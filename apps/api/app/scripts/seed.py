from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User

SEED_USERS = [
    {
        "email": "admin@example.com",
        "full_name": "Demo Admin",
        "password": "Password123!",
        "role": UserRole.ADMIN,
    },
    {
        "email": "reviewer@example.com",
        "full_name": "Demo Reviewer",
        "password": "Password123!",
        "role": UserRole.REVIEWER,
    },
    {
        "email": "user@example.com",
        "full_name": "Demo User",
        "password": "Password123!",
        "role": UserRole.USER,
    },
]


def run_seed() -> None:
    db = SessionLocal()
    try:
        for item in SEED_USERS:
            exists = db.scalar(select(User).where(User.email == item["email"]))
            if exists:
                continue

            db.add(
                User(
                    email=item["email"],
                    full_name=item["full_name"],
                    hashed_password=get_password_hash(item["password"]),
                    role=item["role"],
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
    print("Seed data created (or already exists) for local demo users.")
