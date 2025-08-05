#!/usr/bin/env python3
"""
Simple test script for database logging functionality
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_supabase_connection():
    """Test basic Supabase connection."""
    try:
        # Check environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')  # Using the existing key name
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found!")
            print(f"SUPABASE_URL: {bool(supabase_url)}")
            print(f"SUPABASE_KEY: {bool(supabase_key)}")
            return False
        
        print("✅ Supabase credentials found")
        print(f"URL: {supabase_url}")
        print(f"Key: {supabase_key[:20]}...")
        
        # Try to import and create client
        try:
            from supabase import create_client, Client
            supabase: Client = create_client(supabase_url, supabase_key)
            print("✅ Supabase client created successfully")
            
            # Test a simple query
            result = supabase.table('generation_sessions').select('count').execute()
            print("✅ Database connection successful")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create Supabase client: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Database Logging Setup")
    print("=" * 40)
    
    if test_supabase_connection():
        print("\n✅ Basic connection test passed!")
        print("\n📝 Next steps:")
        print("1. Create the database tables in Supabase")
        print("2. Run the main application to see logs")
    else:
        print("\n❌ Connection test failed!")
        print("Please check your Supabase credentials and try again.")

if __name__ == "__main__":
    main() 