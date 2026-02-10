#!/usr/bin/env python3
"""
Admin Initialization Script
Creates the default admin user for the Senzor platform.
Run this once during deployment: python backend/init_admin.py
"""

import sys
import os

# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
import auth

def init_admin():
    """Create the default admin user if it doesn't exist."""
    
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(models.User).filter(
            models.User.email == "admin@senzor.com"
        ).first()
        
        if admin:
            print("✅ Admin user already exists: admin@senzor.com")
            return
        
        # Create admin user
        hashed_password = auth.get_password_hash("Senzor2026")
        admin_user = models.User(
            email="admin@senzor.com",
            hashed_password=hashed_password,
            role=models.UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@senzor.com")
        print(f"   Password: Senzor2026")
        print(f"   Role: {admin_user.role}")
        print(f"   ID: {admin_user.id}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Initializing Senzor Admin User...")
    init_admin()
    print("✨ Done!")
