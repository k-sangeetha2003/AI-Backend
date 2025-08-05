#!/usr/bin/env python3
"""
Debug script to check environment variable loading.
"""

import os
from dotenv import load_dotenv

def debug_environment():
    """Debug environment variable loading."""
    print("🔍 Environment Variable Debug")
    print("=" * 40)
    
    # Check if .env file exists
    env_file_path = os.path.join(os.getcwd(), '.env')
    print(f"📁 .env file path: {env_file_path}")
    print(f"📁 .env file exists: {os.path.exists(env_file_path)}")
    
    # Load environment variables
    print("\n🔄 Loading environment variables...")
    load_dotenv()
    
    # Check required variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENROUTER_API_KEY']
    
    print("\n📋 Environment Variables Status:")
    print("-" * 30)
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first few characters for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    # Check all environment variables (for debugging)
    print("\n🔍 All Environment Variables:")
    print("-" * 30)
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['SUPABASE', 'OPENROUTER', 'API']):
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"{key}: {display_value}")

if __name__ == "__main__":
    debug_environment() 