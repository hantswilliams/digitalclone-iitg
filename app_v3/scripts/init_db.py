#!/usr/bin/env python3
"""
Database initialization script for the Voice-Cloned Talking-Head Lecturer application
"""
import os
import sys
from flask import Flask
from flask_migrate import init, migrate, upgrade

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from app import create_app
from app.extensions import db
from app.models import User, Asset, Job, Video, UserRole


def init_database():
    """Initialize the database with tables and migrations"""
    print("🚀 Initializing database...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if we have any users
            user_count = User.query.count()
            print(f"📊 Current user count: {user_count}")
            
            # Create a default admin user if none exists
            if user_count == 0:
                print("👤 Creating default admin user...")
                
                admin_user = User(
                    email="admin@voiceclone.edu",
                    username="admin",
                    password="AdminPass123",
                    first_name="System",
                    last_name="Administrator",
                    department="IT",
                    title="System Administrator",
                    role=UserRole.ADMIN,
                    is_verified=True
                )
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Default admin user created!")
                print("📧 Email: admin@voiceclone.edu")
                print("🔑 Password: AdminPass123")
                print("⚠️  Please change the default password after first login!")
            
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {str(e)}")
            return False


def reset_database():
    """Reset the database (drop and recreate all tables)"""
    print("⚠️  Resetting database...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables
            print("🗑️  Dropping all tables...")
            db.drop_all()
            
            # Recreate tables
            print("📋 Recreating tables...")
            db.create_all()
            
            print("✅ Database reset successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database reset failed: {str(e)}")
            return False


def check_database():
    """Check database connection and tables"""
    print("🔍 Checking database...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            if result:
                print("✅ Database connection successful!")
            
            # Check tables
            tables = db.inspect(db.engine).get_table_names()
            print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
            
            # Check user count
            user_count = User.query.count()
            print(f"👤 User count: {user_count}")
            
            # Check other model counts
            asset_count = Asset.query.count()
            job_count = Job.query.count()
            video_count = Video.query.count()
            
            print(f"📁 Asset count: {asset_count}")
            print(f"⚙️  Job count: {job_count}")
            print(f"🎬 Video count: {video_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database check failed: {str(e)}")
            return False


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    if command == "init":
        success = init_database()
    elif command == "reset":
        confirm = input("⚠️  Are you sure you want to reset the database? This will delete all data! (yes/no): ")
        if confirm.lower() == "yes":
            success = reset_database() and init_database()
        else:
            print("❌ Database reset cancelled.")
            success = False
    elif command == "check":
        success = check_database()
    else:
        print("Usage: python init_db.py [init|reset|check]")
        print("  init  - Initialize database tables and create default admin user")
        print("  reset - Reset database (drop and recreate all tables)")
        print("  check - Check database connection and table status")
        success = False
    
    sys.exit(0 if success else 1)
