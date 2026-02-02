#!/usr/bin/env python3
"""
Create an admin user and organization.
Run this in Railway shell: railway run --service backend python scripts/create_admin_user.py
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(email, password, org_name):
    """Create admin user and organization."""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            return False
        
        # Create organization
        org = Organization(
            id=uuid.uuid4(),
            name=org_name,
            slug=org_name.lower().replace(' ', '-'),
            plan="FREE"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        print(f"✅ Created organization: {org.name} ({org.id})")
        
        # Create admin user
        user = User(
            id=uuid.uuid4(),
            email=email,
            name="Admin User",
            hashed_password=pwd_context.hash(password),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created user: {user.email} ({user.id})")
        
        # Add user to organization as admin
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="ADMIN"
        )
        db.add(member)
        db.commit()
        print(f"✅ Added user to organization as ADMIN")
        
        print("\n" + "="*60)
        print("🎉 Admin user created successfully!")
        print("="*60)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Organization: {org.name}")
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    # Default values
    email = input("Admin email [admin@leasebee.com]: ").strip() or "admin@leasebee.com"
    password = input("Admin password [ChangeMe123!]: ").strip() or "ChangeMe123!"
    org_name = input("Organization name [Admin Organization]: ").strip() or "Admin Organization"
    
    create_admin_user(email, password, org_name)
