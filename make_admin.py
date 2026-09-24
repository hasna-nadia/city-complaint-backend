from database import SessionLocal
from models import Users
from passlib.context import CryptContext

db = SessionLocal()

bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

existing_admin = db.query(Users).filter(
    Users.email == "admin@gmail.com"
).first()

if existing_admin:
    print("Admin already exists")
else:
    admin = Users(
        name="Admin",
        email="admin@gmail.com",
        password=bcrypt_context.hash("admin123"),
        role="admin"
    )

    db.add(admin)
    db.commit()

    print("Admin created successfully")

db.close()