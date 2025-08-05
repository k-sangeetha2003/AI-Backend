#!/usr/bin/env python3
"""
Setup script for Short Story Crew
Helps users install dependencies and configure the environment.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version {sys.version.split()[0]} is compatible")
        return True


def check_virtual_environment():
    """Check if running in a virtual environment."""
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print("✅ Running in virtual environment")
        return True
    else:
        print("⚠️  Not running in a virtual environment")
        print("It's recommended to use a virtual environment for this project")
        response = input("Continue anyway? (y/n): ").strip().lower()
        return response in ["y", "yes"]


def install_dependencies():
    """Install Python dependencies."""
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False

    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies",
    )


def setup_environment():
    """Set up environment configuration."""
    env_file = Path(".env")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    print("🔑 Setting up environment configuration...")
    api_key = input("Enter your OpenAI API key: ").strip()

    if not api_key:
        print("⚠️  No API key provided. You'll need to set OPENAI_API_KEY later.")
        return True

    try:
        with open(".env", "w") as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
            f.write("MAX_STORY_DURATION=15\n")
            f.write("PROJECT_NAME=short_story_crew\n")

        print("✅ Environment configuration saved to .env")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ["outputs", "logs"]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Error creating directory {directory}: {e}")
            return False

    return True


def test_installation():
    """Test if the installation works."""
    print("\n🧪 Testing installation...")

    try:
        # Test imports
        from config import Config  # noqa: F401

        print("✅ All imports successful")

        # Test crew info (doesn't require API key)
        test_command = f"{sys.executable} main.py --info"
        if run_command(test_command, "Testing crew information"):
            print("✅ Installation test passed!")
            return True
        else:
            print("⚠️  Installation test failed, but basic setup is complete")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Some dependencies may not be installed correctly")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def main():
    """Main setup function."""
    print("🎬 Short Story Crew Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check virtual environment
    if not check_virtual_environment():
        print("Setup cancelled by user")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Set up environment
    if not setup_environment():
        print("❌ Failed to set up environment")
        sys.exit(1)

    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        sys.exit(1)

    # Test installation
    test_installation()

    print("\n🎉 Setup completed!")
    print("\n📖 Quick start:")
    print("   python main.py                    # Interactive mode")
    print("   python main.py --info             # Show crew info")
    print('   python main.py --idea "your idea" # Single story generation')
    print("\n📚 Read README.md for detailed usage instructions")


if __name__ == "__main__":
    main()
