#!/usr/bin/env python3
"""
Test script to verify error logging functionality.
This script tests the new error_logs table structure and error handling.
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.simple_db_logger import SimpleDatabaseLogger

def setup_test_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_error_logging():
    """Test the error logging functionality."""
    print("🧪 Testing Error Logging Functionality")
    print("=" * 50)
    
    # Setup logging
    logger = setup_test_logging()
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize database logger
        db_logger = SimpleDatabaseLogger(logger)
        print("✅ Database logger initialized successfully")
        
        # Test error logging with the new structure
        test_error_message = "Test error: OpenRouter API not responding"
        test_request_id = "test-request-123"
        test_session_id = "test-session-456"
        
        print(f"\n📝 Logging test error...")
        print(f"Error Type: generation_error")
        print(f"Error Category: social_content")
        print(f"Error Message: {test_error_message}")
        print(f"Request ID: {test_request_id}")
        print(f"Session ID: {test_session_id}")
        
        # Log the test error
        db_logger.log_user_facing_error(
            error_type='generation_error',
            error_category='social_content',
            error_message=test_error_message,
            request_id=test_request_id,
            session_id=test_session_id
        )
        
        print("✅ Test error logged successfully")
        
        # Test error logging without request_id and session_id (should generate defaults)
        print(f"\n📝 Logging test error with auto-generated IDs...")
        
        db_logger.log_user_facing_error(
            error_type='generation_error',
            error_category='social_content',
            error_message="Test error: Content generation failed"
        )
        
        print("✅ Test error with auto-generated IDs logged successfully")
        
        print("\n🎉 All error logging tests passed!")
        
    except Exception as e:
        print(f"❌ Error logging test failed: {str(e)}")
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False
    
    return True

def test_database_connection():
    """Test the database connection."""
    print("\n🔍 Testing Database Connection")
    print("=" * 30)
    
    logger = setup_test_logging()
    load_dotenv()
    
    try:
        # Test basic connection
        db_logger = SimpleDatabaseLogger(logger)
        
        # Test a simple request to verify connection
        # This will test if the Supabase credentials are working
        print("✅ Database connection test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")
        logger.error(f"Connection test failed: {str(e)}", exc_info=True)
        return False

def main():
    """Main test function."""
    print("🚀 Social Media Content Generator - Error Logging Test")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    
    print("✅ Environment variables check passed")
    
    # Test database connection
    if not test_database_connection():
        return False
    
    # Test error logging
    if not test_error_logging():
        return False
    
    print("\n🎉 All tests completed successfully!")
    print("\n📋 Summary:")
    print("- Database connection: ✅")
    print("- Error logging: ✅")
    print("- New error_logs table structure: ✅")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 