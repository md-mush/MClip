# =============================================================================
# QUICK SETUP SCRIPT FOR COLAB
# =============================================================================
# Paste this entire script into a Colab cell and run it first

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing required packages...")
    
    packages = [
        "requests",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "asyncpg",
        "python-dotenv",
        "pydantic",
        "openai-whisper",
        "yt-dlp",
        "moviepy",
        "opencv-python",
        "numpy",
        "aiofiles"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
    
    print("✅ All packages installed!")

def setup_environment():
    """Set up environment variables"""
    print("\n🔧 Setting up environment...")
    
    # Create .env file with default values
    env_content = """# Database Configuration
DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_jIbRz93SfctW@ep-mute-night-ad9zcd4p-pooler.c-2.us-east-1.aws.neon.tech/neondb

# Video Processing Configuration
WHISPER_MODEL=base
MAX_VIDEO_DURATION=3600
OUTPUT_DIR=outputs
MAX_CLIPS=10
CLIP_DURATION=30
TEMP_DIR=temp

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Environment file created!")

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "outputs",
        "temp",
        "temp/clips",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def check_colab_environment():
    """Check if running in Colab"""
    print("\n🔍 Checking environment...")
    
    try:
        import google.colab
        print("✅ Running in Google Colab")
        return True
    except ImportError:
        print("⚠️  Not running in Google Colab")
        return False

def main():
    """Main setup function"""
    print("🚀 SupoClip Backend Setup for Colab")
    print("="*50)
    
    # Check environment
    is_colab = check_colab_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    print("\n" + "="*50)
    print("✅ Setup Complete!")
    print("="*50)
    print("\nNext steps:")
    print("1. Upload your backend code to Colab")
    print("2. Run: uvicorn src.main:app --host 0.0.0.0 --port 8000")
    print("3. Use the test scripts to verify everything works")
    print("\nTest scripts available:")
    print("- 01_database_test.py")
    print("- 02_authentication_test.py") 
    print("- 03_youtube_processing_test.py")
    print("- 04_comprehensive_test.py")

if __name__ == "__main__":
    main()
