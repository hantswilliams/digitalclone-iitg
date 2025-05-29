#!/usr/bin/env python3
"""
Reset or create test user for API testing
"""

import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole
from werkzeug.security import generate_password_hash

def reset_test_user():
    """Reset or create test user"""
    app = create_app()
    
    with app.app_context():
        # Delete ALL users with incompatible enum values
        print("Cleaning up database...")
        try:
            # Try to delete users, but catch enum errors
            users_to_delete = db.session.execute(
                db.text("DELETE FROM users WHERE email = 'test@example.com' OR username = 'testuser'")
            )
            db.session.commit()
            print("Deleted users with SQL")
        except Exception as e:
            print(f"SQL deletion failed: {e}")
            # Fallback: recreate the table if needed
            db.session.rollback()
        
        # Create new test user
        print("Creating fresh test user...")
        test_user = User(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            role=UserRole.FACULTY,
            is_active=True
        )
        
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test user created successfully")
        print("Email: test@example.com")
        print("Password: TestPassword123!")

if __name__ == "__main__":
    reset_test_user()
