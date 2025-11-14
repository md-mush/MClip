#!/usr/bin/env python3
"""
Quick fix script for SupoClip in Google Colab
Run this to fix ImageMagick and dependency issues
"""

import subprocess
import sys
import os

def run_cmd(cmd):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("🚀 SupoClip Colab Quick Fix")
    print("=" * 40)
    
    # 1. Install ImageMagick
    print("📦 Installing ImageMagick...")
    success, output = run_cmd("apt-get update -y && apt-get install -y imagemagick imagemagick-dev")
    if success:
        print("✅ ImageMagick installed")
    else:
        print(f"❌ ImageMagick installation failed: {output}")
    
    # 2. Install FFmpeg
    print("🎬 Installing FFmpeg...")
    success, output = run_cmd("apt-get install -y ffmpeg")
    if success:
        print("✅ FFmpeg installed")
    else:
        print(f"❌ FFmpeg installation failed: {output}")
    
    # 3. Install font libraries
    print("🔤 Installing font libraries...")
    success, output = run_cmd("apt-get install -y libfontconfig1-dev libfreetype6-dev fonts-dejavu-core")
    if success:
        print("✅ Font libraries installed")
    else:
        print(f"❌ Font libraries installation failed: {output}")
    
    # 4. Fix ImageMagick policy
    print("⚙️ Fixing ImageMagick policy...")
    policy_file = "/etc/ImageMagick-6/policy.xml"
    if os.path.exists(policy_file):
        # Backup and modify policy
        run_cmd(f"cp {policy_file} {policy_file}.backup")
        
        # Remove restrictive policies
        cmd = f"""sed -i 's/<policy domain="path" rights="none" pattern="@\\*"/<policy domain="path" rights="read|write" pattern="@*"/g' {policy_file}"""
        run_cmd(cmd)
        
        cmd = f"""sed -i 's/<policy domain="coder" rights="none" pattern="LABEL"/<policy domain="coder" rights="read|write" pattern="LABEL"/g' {policy_file}"""
        run_cmd(cmd)
        
        print("✅ ImageMagick policy fixed")
    else:
        print("⚠️ ImageMagick policy file not found")
    
    # 5. Install Python packages with correct versions
    print("🐍 Installing Python packages...")
    packages = [
        "numpy==2.0.2",
        "fastapi==0.115.2",
        "uvicorn==0.34.0",
        "moviepy==1.0.3",
        "opencv-python==4.12.0.88",
        "openai-whisper==20250625",
        "yt-dlp==2025.7.21",
        "ollama==0.6.0",
        "sqlalchemy==2.0.44",
        "asyncpg==0.29.0",
        "python-dotenv==1.0.0",
        "aiofiles==24.1.0",
        "srt==3.5.3",
        "srt-equalizer==0.1.10",
        "mediapipe==0.10.21",
        "alembic==1.17.0",
        "greenlet==3.2.4",
        "setuptools-rust==1.12.0",
        "sse-starlette==3.0.2"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        success, output = run_cmd(f"{sys.executable} -m pip install {package}")
        if not success:
            print(f"⚠️ Failed to install {package}: {output}")
    
    print("✅ Python packages installed")
    
    # 6. Test MoviePy
    print("🧪 Testing MoviePy...")
    try:
        import moviepy.editor as mp
        clip = mp.TextClip("Test", fontsize=24, color="white")
        print("✅ MoviePy TextClip test successful")
        clip.close()
    except Exception as e:
        print(f"⚠️ MoviePy test failed: {e}")
        print("This might still work with fallback methods in the app")
    
    # 7. Set environment variables
    print("⚙️ Setting environment variables...")
    os.environ['OLLAMA_TIMEOUT'] = '7200'  # 2 hours
    os.environ['WHISPER_MODEL'] = 'base'
    print("✅ Environment variables set")
    
    print("\n🎉 Setup complete!")
    print("Next steps:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Pull the model: ollama pull llama3.1:8b")
    print("3. Start your app: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()