from database import engine, SessionLocal
import models
from models import Base, User, UserRole
from auth import get_password_hash

print("Resetting database...")
try:
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped.")
    Base.metadata.create_all(bind=engine)
    print("Tables recreated.")
    
    db = SessionLocal()
    admin_email = "admin@senzor.com"
    if not db.query(User).filter(User.email == admin_email).first():
        print("Creating admin user...")
        admin = User(
            email=admin_email,
            username="Admin",
            hashed_password=get_password_hash("Senzor2026"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created: admin@senzor.com / Senzor2026")
    db.close()
except Exception as e:
    print(f"Error: {e}")
