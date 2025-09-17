#!/usr/bin/env python3
"""
Test database connection
"""

from database import DatabaseManager
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def test_connection():
    print("🔍 Testing database connection...")
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"Password: {'*' * len(DB_PASSWORD)}")
    print("-" * 50)
    
    db = DatabaseManager()
    
    if db.connect():
        print("✅ Database connection successful!")
        
        # Test a simple query
        try:
            db.cursor.execute("SELECT version();")
            version = db.cursor.fetchone()
            print(f"📊 PostgreSQL version: {version[0]}")
            
            # Test if images table exists
            db.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'images'
                );
            """)
            table_exists = db.cursor.fetchone()[0]
            
            if table_exists:
                print("✅ Images table exists!")
                
                # Count records
                db.cursor.execute("SELECT COUNT(*) FROM images;")
                count = db.cursor.fetchone()[0]
                print(f"📈 Images in database: {count}")
            else:
                print("❌ Images table does not exist!")
                
        except Exception as e:
            print(f"❌ Database query failed: {e}")
        
        db.disconnect()
        print("🔌 Database disconnected")
    else:
        print("❌ Database connection failed!")

if __name__ == "__main__":
    test_connection()
