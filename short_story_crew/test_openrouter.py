#!/usr/bin/env python3
"""Simple test to verify OpenRouter API connectivity with enhanced logging."""

import os

import requests
from dotenv import load_dotenv

from utils.logger import (
    log_error,
    log_info,
    log_user_interaction,
    log_warning,
    setup_logging,
)

# Load environment variables
load_dotenv()


def test_openrouter_api():
    """Test OpenRouter API connectivity with detailed logging."""
    log_info("Starting OpenRouter API connectivity test")

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        error_msg = "OPENROUTER_API_KEY not found in environment"
        log_error(error_msg)
        print("❌ OPENROUTER_API_KEY not found in environment")
        return False

    # Log API key info (safely truncated)
    key_display = f"{api_key[:10]}...{api_key[-10:]}"
    log_info(f"API Key loaded: {key_display}")
    print(f"🔑 API Key: {key_display}")

    # Prepare test request
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 10,
    }

    log_info(f"Testing with model: {data['model']}")

    try:
        log_info("Sending test request to OpenRouter API")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30,
        )

        status_code = response.status_code
        log_info(f"API response status: {status_code}")
        print(f"📡 Status Code: {status_code}")

        if status_code == 200:
            result = response.json()
            message = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "No content")
            )
            log_info(f"API test successful - Response: {message}")
            print(f"✅ Response: {message}")
            return True
        else:
            error_text = response.text
            log_error(
                f"API test failed - Status: {status_code}, Response: {error_text}"
            )
            print(f"❌ Error: {error_text}")
            return False

    except requests.exceptions.Timeout:
        error_msg = "API request timeout after 30 seconds"
        log_error(error_msg)
        print(f"❌ Timeout: {error_msg}")
        return False
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error - check internet connectivity"
        log_error(error_msg)
        print(f"❌ Connection Error: {error_msg}")
        return False
    except Exception as e:
        log_error(f"Unexpected error during API test: {str(e)}", exc_info=True)
        print(f"❌ Exception: {e}")
        return False


def main():
    """Main function with logging setup."""
    # Initialize logging system
    setup_logging()
    log_user_interaction("OpenRouter API test started")

    print("🧪 Testing OpenRouter API Connection...")
    print("=" * 50)

    try:
        success = test_openrouter_api()

        # Log final result
        result_msg = "SUCCESS" if success else "FAILED"
        if success:
            log_info("OpenRouter API test completed successfully")
        else:
            log_warning("OpenRouter API test failed")

        print("=" * 50)
        print(f"🎯 Result: {result_msg}")

        return success

    except KeyboardInterrupt:
        log_user_interaction("API test interrupted by user")
        print("\n👋 Test interrupted. Goodbye!")
        return False
    except Exception as e:
        log_error(f"Unexpected error in main: {str(e)}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    main()
