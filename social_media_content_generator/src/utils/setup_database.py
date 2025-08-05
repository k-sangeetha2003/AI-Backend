#!/usr/bin/env python3
"""
Database Setup Utility for Social Media Content Generator
This script helps set up the Supabase database tables and test the logging functionality.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.database_logger import DatabaseLogger

def setup_logging():
    """Setup basic logging for the utility."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_database_connection():
    """Test the database connection and basic operations."""
    logger = setup_logging()
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if Supabase credentials are available
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found!")
            print("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
            return False
        
        print("✅ Supabase credentials found")
        
        # Initialize database logger
        db_logger = DatabaseLogger(logger)
        print("✅ Database logger initialized successfully")
        
        # Test basic operations
        print("\n🧪 Testing database operations...")
        
        # Test session creation
        session_id = db_logger.start_generation_session(
            idea="Test content generation",
            platform="instagram",
            tones=["casual"],
            audiences=["general audience"]
        )
        print(f"✅ Session created: {session_id}")
        
        # Test agent execution logging
        execution_id = db_logger.log_agent_execution(
            agent_name="test_agent",
            execution_order=1,
            input_data={"test": "data"},
            model_used="openai/gpt-3.5-turbo",
            temperature=0.7
        )
        print(f"✅ Agent execution logged: {execution_id}")
        
        # Test API call logging
        db_logger.log_api_call(
            agent_execution_uuid=execution_id,
            api_provider="openrouter",
            endpoint="/v1/chat/completions",
            model_used="openai/gpt-3.5-turbo",
            request_data={"test": "request"},
            response_data={"test": "response"},
            status_code=200,
            tokens_used=150,
            cost_usd=0.003,
            response_time_ms=1200
        )
        print("✅ API call logged")
        
        # Test error logging
        db_logger.log_error(
            agent_execution_uuid=execution_id,
            error_type="test_error",
            error_message="This is a test error",
            severity="info"
        )
        print("✅ Error logged")
        
        # Test performance metric logging
        db_logger.log_performance_metric(
            metric_name="test_metric",
            metric_value=1.5,
            metric_unit="seconds"
        )
        print("✅ Performance metric logged")
        
        # Complete the session
        db_logger.complete_generation_session(
            status="completed",
            total_tokens_used=150,
            total_cost_usd=0.003
        )
        print("✅ Session completed")
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        logger.error(f"Database test failed: {str(e)}", exc_info=True)
        return False

def create_database_schema():
    """Provide the SQL commands to create the database schema."""
    schema_sql = """
-- Complete Database Schema for Social Media Content Generator Logging

-- Step 1: Create all tables first
CREATE TABLE generation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    original_idea TEXT NOT NULL,
    target_platform VARCHAR(20) NOT NULL,
    requested_tones TEXT[],
    requested_audiences TEXT[],
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES generation_sessions(id),
    agent_name VARCHAR(50) NOT NULL,
    execution_order INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    input_data JSONB,
    output_data JSONB,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,4) DEFAULT 0,
    model_used VARCHAR(100),
    temperature DECIMAL(3,2),
    execution_time_ms INTEGER,
    error_message TEXT,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES generation_sessions(id),
    agent_execution_id UUID REFERENCES agent_executions(id),
    api_provider VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    model_used VARCHAR(100),
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,4) DEFAULT 0,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE image_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES generation_sessions(id),
    agent_execution_id UUID REFERENCES agent_executions(id),
    prompt TEXT NOT NULL,
    generated_image_url TEXT,
    image_size VARCHAR(20),
    model_used VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    cost_usd DECIMAL(10,4) DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES generation_sessions(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE error_logs (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID,
    session_id UUID REFERENCES generation_sessions(id),
    error_type VARCHAR(100) NOT NULL,
    error_category VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    billing_period VARCHAR(20) NOT NULL,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,
    successful_generations INTEGER DEFAULT 0,
    failed_generations INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    platform VARCHAR(20),
    tone VARCHAR(50),
    audience VARCHAR(100),
    generation_count INTEGER DEFAULT 0,
    avg_tokens_per_generation INTEGER DEFAULT 0,
    avg_cost_per_generation DECIMAL(10,4) DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Create indexes AFTER all tables are created
CREATE INDEX idx_generation_sessions_user_id ON generation_sessions(user_id);
CREATE INDEX idx_generation_sessions_status ON generation_sessions(status);
CREATE INDEX idx_generation_sessions_created_at ON generation_sessions(created_at);
CREATE INDEX idx_agent_executions_session_id ON agent_executions(session_id);
CREATE INDEX idx_agent_executions_agent_name ON agent_executions(agent_name);
CREATE INDEX idx_api_calls_session_id ON api_calls(session_id);
CREATE INDEX idx_error_logs_session_id ON error_logs(session_id);
CREATE INDEX idx_billing_summary_user_id ON billing_summary(user_id);
CREATE INDEX idx_usage_analytics_user_id ON usage_analytics(user_id);

-- Additional useful indexes
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
CREATE INDEX idx_api_calls_api_provider ON api_calls(api_provider);
CREATE INDEX idx_api_calls_created_at ON api_calls(created_at);
CREATE INDEX idx_image_generations_status ON image_generations(status);
CREATE INDEX idx_error_logs_error_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_severity ON error_logs(severity);
CREATE INDEX idx_billing_summary_period ON billing_summary(billing_period, period_start_date);
CREATE INDEX idx_usage_analytics_date ON usage_analytics(date);
"""
    
    print("📋 Database Schema SQL Commands:")
    print("=" * 50)
    print(schema_sql)
    print("=" * 50)
    print("\n📝 Instructions:")
    print("1. Copy the SQL commands above")
    print("2. Go to your Supabase dashboard")
    print("3. Navigate to SQL Editor")
    print("4. Paste and execute the commands")
    print("5. Run this script again to test the connection")

def main():
    """Main function to run the database setup utility."""
    print("🔧 Social Media Content Generator - Database Setup Utility")
    print("=" * 60)
    
    while True:
        print("\nChoose an option:")
        print("1. Show database schema SQL commands")
        print("2. Test database connection")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            create_database_schema()
        elif choice == "2":
            if test_database_connection():
                print("\n✅ Database setup is complete and working!")
            else:
                print("\n❌ Database setup failed. Please check your configuration.")
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main() 