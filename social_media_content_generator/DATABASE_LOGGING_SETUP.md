# Database Logging Setup Guide

This guide will help you set up comprehensive database logging for your Social Media Content Generator using Supabase.

## 🎯 What You'll Get

With this setup, you'll have detailed logging that captures:

- **Complete session tracking** - Every content generation from start to finish
- **Agent-level monitoring** - Performance and costs for each AI agent
- **API call tracking** - Detailed API usage for billing justification
- **Error logging** - Comprehensive error tracking with context
- **Performance metrics** - System health and optimization insights
- **Billing support** - Detailed cost breakdown for customer invoices

## 📋 Prerequisites

1. **Supabase Account**: You need a Supabase project
2. **Environment Variables**: Configure your `.env` file
3. **Database Tables**: Create the logging schema in Supabase

## 🚀 Setup Steps

### Step 1: Configure Environment Variables

Copy the template and create your `.env` file:

```bash
cp env_template.txt .env
```

Edit your `.env` file and add your Supabase credentials:

```env
# Required API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Supabase Configuration (Required for Database Logging)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# User Configuration (Optional - for multi-tenant support)
USER_ID=default_user

# Agent Model Settings
CONTENT_STRATEGIST_MODEL=openai/gpt-3.5-turbo
CONTENT_WRITER_MODEL=openai/gpt-3.5-turbo
HASHTAG_SPECIALIST_MODEL=openai/gpt-3.5-turbo
VISUAL_DESIGNER_MODEL=openai/gpt-3.5-turbo

# Agent Temperature Settings
CONTENT_STRATEGIST_TEMPERATURE=0.7
CONTENT_WRITER_TEMPERATURE=0.8
HASHTAG_SPECIALIST_TEMPERATURE=0.6
VISUAL_DESIGNER_TEMPERATURE=0.7

# Platform Settings
MAX_HASHTAGS=30
```

### Step 2: Create Database Tables

Run the database setup utility:

```bash
python src/utils/setup_database.py
```

Choose option 1 to get the SQL commands, then:

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy and paste the SQL commands
4. Execute them to create all tables and indexes

### Step 3: Test the Setup

Run the database setup utility again and choose option 2 to test the connection:

```bash
python src/utils/setup_database.py
```

You should see:
```
✅ Supabase credentials found
✅ Database logger initialized successfully
✅ Session created: gen_20241201_12345678_abc12345
✅ Agent execution logged: uuid-here
✅ API call logged
✅ Error logged
✅ Performance metric logged
✅ Session completed
🎉 All database tests passed!
```

## 📊 Database Schema Overview

### Main Tables

1. **`generation_sessions`** - Master session tracking
2. **`agent_executions`** - Individual agent performance
3. **`api_calls`** - Detailed API call tracking
4. **`image_generations`** - Image generation tracking
5. **`performance_metrics`** - System performance data
6. **`error_logs`** - Comprehensive error tracking
7. **`billing_summary`** - Billing aggregation
8. **`usage_analytics`** - Usage patterns

### Key Benefits

- **Complete Traceability**: Every generation session tracked from start to finish
- **Agent-Level Monitoring**: Individual agent performance and costs
- **API Call Tracking**: Detailed API usage for billing justification
- **Error Debugging**: Comprehensive error logging with context
- **Billing Support**: Aggregated billing data for customer invoices
- **Performance Analytics**: Usage patterns and optimization insights

## 🔍 What Gets Logged

### For Each Content Generation Session:

1. **Session Start**: User input, platform, tones, audiences
2. **Content Strategist**: Strategy development with timing and costs
3. **Content Writer**: Content creation with model usage
4. **Hashtag Specialist**: Hashtag generation with optimization
5. **Visual Designer**: Image prompt creation
6. **Image Generation**: DALL-E API calls and results
7. **Session Complete**: Total costs, tokens, and final status

### For Each API Call:

- Provider (OpenRouter, OpenAI, etc.)
- Endpoint and model used
- Request and response data
- Token usage and costs
- Response times
- Error details (if any)

### For Errors:

- Error type and message
- Stack trace
- Context data
- Severity level
- Associated session and agent

## 💰 Billing and Analytics

The system automatically tracks:

- **Token usage** per agent and API call
- **Costs** in USD for each operation
- **Success rates** for different agents
- **Performance metrics** for optimization
- **Usage patterns** for business insights

## 🛠️ Usage Examples

### View Session Details

```python
from src.utils.database_logger import DatabaseLogger

db_logger = DatabaseLogger(logger)
session_summary = db_logger.get_session_summary("gen_20241201_12345678_abc12345")
print(session_summary)
```

### Query Billing Data

```sql
-- Get total costs for a user
SELECT 
    user_id,
    SUM(total_cost_usd) as total_cost,
    COUNT(*) as total_sessions
FROM generation_sessions 
WHERE user_id = 'customer_123'
GROUP BY user_id;
```

### Analyze Performance

```sql
-- Get agent performance metrics
SELECT 
    agent_name,
    AVG(execution_time_ms) as avg_execution_time,
    AVG(cost_usd) as avg_cost,
    COUNT(*) as total_executions
FROM agent_executions 
WHERE status = 'completed'
GROUP BY agent_name;
```

## 🔧 Troubleshooting

### Common Issues

1. **"Supabase credentials not found"**
   - Check your `.env` file has `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Verify the credentials are correct

2. **"Failed to initialize Supabase client"**
   - Check your internet connection
   - Verify your Supabase project is active

3. **"Failed to create session record"**
   - Ensure all database tables are created
   - Check your Supabase permissions

4. **"Column does not exist"**
   - Run the complete SQL schema creation
   - Make sure indexes are created after tables

### Debug Mode

Enable detailed logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Monitoring and Alerts

### Key Metrics to Monitor

- **Success Rate**: Percentage of successful generations
- **Average Cost**: Cost per generation session
- **Agent Performance**: Which agents are slowest/most expensive
- **Error Patterns**: Common error types and frequencies
- **API Response Times**: Performance of external APIs

### Recommended Queries

```sql
-- Daily success rate
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
    ROUND(COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM generation_sessions 
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Cost analysis by platform
SELECT 
    target_platform,
    COUNT(*) as sessions,
    AVG(total_cost_usd) as avg_cost,
    SUM(total_cost_usd) as total_cost
FROM generation_sessions 
WHERE status = 'completed'
GROUP BY target_platform;
```

## 🎉 You're Ready!

Once you've completed the setup:

1. **Test the application**: Run `python src/main.py`
2. **Check your Supabase dashboard**: You should see data in the tables
3. **Monitor performance**: Use the queries above to track usage
4. **Generate reports**: Use the data for billing and analytics

The system will now automatically log every aspect of your content generation process, providing you with comprehensive insights for debugging, billing, and optimization! 