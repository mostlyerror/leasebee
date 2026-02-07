#!/usr/bin/env python3
"""
Create admin user for LeaseBee after deployment
Run via: railway run --service backend python scripts/create_admin_user.py
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from passlib.context import CryptContext
import uuid

def create_admin_user():
    """Create admin user and organization"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.email == "admin@leasebee.com").first()
        if existing_user:
            print("❌ Admin user already exists!")
            print(f"   Email: {existing_user.email}")
            print(f"   User ID: {existing_user.id}")
            return
        
        # Create organization
        org = Organization(
            id=uuid.uuid4(),
            name="LeaseBee Admin",
            slug="leasebee-admin",
            plan="FREE"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        print(f"✅ Created organization: {org.name}")
        print(f"   Org ID: {org.id}")
        
        # Create admin user
        user = User(
            id=uuid.uuid4(),
            email="admin@leasebee.com",
            name="Admin User",
            hashed_password=pwd_context.hash("changeme123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created admin user: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"   Password: changeme123")
        print(f"\n⚠️  IMPORTANT: Change password after first login!")
        
        # Add user to organization
        from sqlalchemy import text
        db.execute(
            text("INSERT INTO organization_members (organization_id, user_id, role) VALUES (:org_id, :user_id, 'ADMIN')"),
            {"org_id": str(org.id), "user_id": str(user.id)}
        )
        db.commit()
        print(f"✅ Added user to organization as ADMIN")
        
        print("\n" + "="*60)
        print("DEPLOYMENT SUCCESSFUL!")
        print("="*60)
        print(f"\nLogin credentials:")
        print(f"  Email: admin@leasebee.com")
        print(f"  Password: changeme123")
        print(f"\n🎉 You can now log in to your LeaseBee application!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
