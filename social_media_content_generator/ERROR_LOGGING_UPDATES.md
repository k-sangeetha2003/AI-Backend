# Social Media Content Generator - Error Logging and Output Format Updates

## Overview

This document outlines the fixes implemented to resolve the output format issues and improve error logging in the social media content generator.

## Issues Fixed

### 1. Output Format Structure

**Problem**: The generated content wasn't following the desired structure:
- Title
- Introduction
- Main Points (with timestamps)
- Caption (with emojis)
- Suggested Hashtags

**Solution**: Updated the content writer task and parsing logic to generate and display content in the exact structure requested.

### 2. Error Logging to Supabase

**Problem**: Errors weren't being properly logged to the `error_logs` table with the required fields.

**Solution**: Updated the error_logs table structure and error handling to log:
- `error_id` (uuid)
- `request_id` (uuid)
- `session_id` (uuid)
- `error_type`: "generation_error"
- `error_category`: "social_content"
- `error_message`: exact error from API or logic
- `timestamp`: current time

## Changes Made

### Database Schema Updates

**File**: `src/utils/setup_database.py`

Updated the `error_logs` table structure:
```sql
CREATE TABLE error_logs (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID,
    session_id UUID REFERENCES generation_sessions(id),
    error_type VARCHAR(100) NOT NULL,
    error_category VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Error Logging Updates

**File**: `src/utils/simple_db_logger.py`

- Updated `log_user_facing_error()` method to match new table structure
- Added proper error_type and error_category defaults
- Improved error message handling

### Content Generation Updates

**File**: `src/crew.py`

- Updated content writer task to generate structured output
- Improved parsing logic to handle Title, Introduction, Main Points, Conclusion format
- Added comprehensive error handling around each agent execution
- Added request_id tracking for better error correlation

### Display Updates

**File**: `src/main.py`

- Updated content display to show structured format
- Improved file saving to match new structure
- Enhanced error handling with proper logging

## New Output Format

The content generator now produces output in this exact structure:

```
📋 Title:
[Engaging title for the video]

🎬 Introduction:
[Compelling introduction that hooks the viewer]

📝 Main Points:
1. [Main Point Title] ([timestamp])
- [Bullet points for this section]
2. [Main Point Title] ([timestamp])
- [Bullet points for this section]

🎯 Conclusion:
[Strong conclusion that wraps up the content]

💭 Caption:
[Engaging caption with emojis that summarizes the video]

🏷️ Suggested Hashtags:
[#hashtags separated by space]

🖼️ Generated Image:
[Image URL if generated]
```

## Error Handling Improvements

### Comprehensive Error Logging

All errors are now logged to Supabase with:
- Unique error_id for each error
- Request tracking for correlation
- Proper error categorization
- Timestamp for debugging

### Error Types Handled

1. **API Failures**: OpenRouter not responding, rate limits, etc.
2. **Content Generation Failures**: Agent execution errors
3. **Validation Errors**: Invalid platform, tones, audiences
4. **Image Generation Failures**: DALL-E API issues
5. **Database Errors**: Connection issues, logging failures

### Error Recovery

- Graceful degradation when database logging fails
- Detailed error messages for debugging
- Request tracking for troubleshooting
- Session correlation for analysis

## Testing

### Test Script

Run the test script to verify error logging:
```bash
python test_error_logging.py
```

This script tests:
- Database connection
- Error logging functionality
- New table structure compatibility

### Manual Testing

1. **Test Error Scenarios**:
   - Invalid API keys
   - Network timeouts
   - Invalid input parameters
   - Content generation failures

2. **Verify Output Format**:
   - Check that content follows the new structure
   - Verify timestamps are included
   - Confirm emojis are properly displayed
   - Ensure hashtags are separated correctly

## Database Setup

### Update Existing Database

If you have an existing database, run this SQL to update the error_logs table:

```sql
-- Drop existing error_logs table
DROP TABLE IF EXISTS error_logs;

-- Create new error_logs table
CREATE TABLE error_logs (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID,
    session_id UUID REFERENCES generation_sessions(id),
    error_type VARCHAR(100) NOT NULL,
    error_category VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_error_logs_session_id ON error_logs(session_id);
CREATE INDEX idx_error_logs_error_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_error_category ON error_logs(error_category);
```

### New Database Setup

For new installations, run the database setup utility:
```bash
python src/utils/setup_database.py
```

## Environment Variables

Ensure these variables are set in your `.env` file:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENROUTER_API_KEY=your_openrouter_key
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Check Supabase credentials
   - Verify network connectivity
   - Ensure database exists and is accessible

2. **Content Generation Failures**:
   - Check OpenRouter API key
   - Verify model availability
   - Check rate limits

3. **Error Logging Issues**:
   - Verify error_logs table exists
   - Check table structure matches
   - Ensure proper permissions

### Debug Information

The system now provides detailed logging:
- Request IDs for tracking
- Session correlation
- Error categorization
- Timestamp information

## Performance Improvements

- Reduced API call failures through better error handling
- Improved content generation success rate
- Better error recovery and retry logic
- Enhanced debugging capabilities

## Future Enhancements

1. **Error Analytics**: Dashboard for error analysis
2. **Retry Logic**: Automatic retry for transient failures
3. **Error Notifications**: Real-time error alerts
4. **Performance Monitoring**: Detailed metrics tracking

## Support

For issues or questions:
1. Check the logs in the `logs/` directory
2. Verify database connectivity
3. Test with the provided test script
4. Review error_logs table for specific error details 