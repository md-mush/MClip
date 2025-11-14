#!/usr/bin/env python3
"""
Google Colab Setup Script for SupoClip
Installs all required system dependencies and Python packages
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}")
    print(f"   Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def main():
    print("🚀 SupoClip Google Colab Setup")
    print("=" * 50)
    
    # Update package lists
    run_command("apt-get update -y", "Updating package lists")
    
    # Install system dependencies
    print("\n📦 Installing system dependencies...")
    
    # Install ImageMagick (critical for MoviePy text rendering)
    run_command("apt-get install -y imagemagick", "Installing ImageMagick")
    
    # Install FFmpeg (for video processing)
    run_command("apt-get install -y ffmpeg", "Installing FFmpeg")
    
    # Install additional media libraries
    run_command("apt-get install -y libsm6 libxext6 libxrender-dev libfontconfig1", 
                "Installing additional media libraries")
    
    # Configure ImageMagick policy (remove security restrictions for MoviePy)
    print("\n🔧 Configuring ImageMagick...")
    policy_file = "/etc/ImageMagick-6/policy.xml"
    if os.path.exists(policy_file):
        # Backup original policy
        run_command(f"cp {policy_file} {policy_file}.backup", "Backing up ImageMagick policy")
        
        # Remove PDF/video restrictions that can interfere with MoviePy
        run_command(f'sed -i \'s/<policy domain="path" rights="none" pattern="@\\*"/<policy domain="path" rights="read|write" pattern="@*"/g\' {policy_file}',
                   "Updating ImageMagick policy for MoviePy compatibility")
    
    # Install Python dependencies
    print("\n🐍 Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                   "Installing Python packages from requirements.txt")
    else:
        print("⚠️  requirements.txt not found, installing core packages...")
        core_packages = [
            "fastapi==0.115.2",
            "uvicorn==0.34.0", 
            "openai-whisper==20250625",
            "moviepy==1.0.3",
            "opencv-python==4.12.0.88",
            "yt-dlp==2025.7.21",
            "ollama==0.6.0",
            "sqlalchemy==2.0.44",
            "asyncpg==0.29.0",
            "python-dotenv==1.0.0",
            "aiofiles==24.1.0",
            "srt==3.5.3",
            "srt-equalizer==0.1.10",
            "mediapipe==0.10.21",
            "numpy==2.0.2"
        ]
        for package in core_packages:
            run_command(f"{sys.executable} -m pip install {package}", f"Installing {package}")
    
    # Verify installations
    print("\n✅ Verifying installations...")
    
    # Check ImageMagick
    if run_command("convert -version", "Checking ImageMagick"):
        print("   ✅ ImageMagick is working")
    else:
        print("   ❌ ImageMagick installation failed")
    
    # Check FFmpeg
    if run_command("ffmpeg -version", "Checking FFmpeg"):
        print("   ✅ FFmpeg is working")
    else:
        print("   ❌ FFmpeg installation failed")
    
    # Test MoviePy with ImageMagick
    print("\n🎬 Testing MoviePy with ImageMagick...")
    test_code = '''
import moviepy.editor as mp
try:
    # Test TextClip creation
    clip = mp.TextClip("Test", fontsize=24, color="white", font="Arial")
    print("✅ MoviePy TextClip creation successful")
    clip.close()
except Exception as e:
    print(f"❌ MoviePy TextClip creation failed: {e}")
'''
    
    try:
        exec(test_code)
    except Exception as e:
        print(f"❌ MoviePy test failed: {e}")
    
    print("\n🎉 Setup complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Start your FastAPI server: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
    print("2. Make sure Ollama is running and accessible")
    print("3. Test the /health/db endpoint to verify database connectivity")

if __name__ == "__main__":
    main()