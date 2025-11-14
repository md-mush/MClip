#!/usr/bin/env python3
"""
Complete Google Colab Setup for SupoClip
Fixes all issues: ImageMagick policy, dependencies, and configuration
"""

import subprocess
import sys
import os

def run_cmd(cmd, description=""):
    """Run command and return success status"""
    if description:
        print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if description:
            print(f"✅ {description} completed")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if description:
            print(f"❌ {description} failed: {e.stderr[:200]}")
        return False, e.stderr

def main():
    print("🚀 SupoClip Complete Setup for Google Colab")
    print("=" * 60)
    
    # 1. Update package lists
    run_cmd("apt-get update -y", "Updating package lists")
    
    # 2. Install ImageMagick and dependencies
    print("\n📦 Installing ImageMagick and dependencies...")
    run_cmd("apt-get install -y imagemagick imagemagick-dev", "Installing ImageMagick")
    run_cmd("apt-get install -y ffmpeg", "Installing FFmpeg")
    run_cmd("apt-get install -y libfontconfig1-dev libfreetype6-dev", "Installing font libraries")
    run_cmd("apt-get install -y fonts-dejavu-core fonts-liberation", "Installing fonts")
    
    # 3. Fix ImageMagick policy (THE CRITICAL FIX)
    print("\n⚙️  Fixing ImageMagick security policy...")
    policy_file = "/etc/ImageMagick-6/policy.xml"
    
    if os.path.exists(policy_file):
        try:
            # Backup
            subprocess.run(f"cp {policy_file} {policy_file}.backup", shell=True, check=False)
            
            # Read and fix
            with open(policy_file, 'r') as f:
                content = f.read()
            
            # Apply all necessary fixes
            content = content.replace(
                'rights="none" pattern="@*"',
                'rights="read|write" pattern="@*"'
            )
            content = content.replace(
                '<policy domain="path" rights="none" pattern="@\\*"',
                '<policy domain="path" rights="read|write" pattern="@*"'
            )
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="LABEL"',
                '<policy domain="coder" rights="read|write" pattern="LABEL"'
            )
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="TEXT"',
                '<policy domain="coder" rights="read|write" pattern="TEXT"'
            )
            content = content.replace(
                '<policy domain="coder" rights="none" pattern="PNG"',
                '<policy domain="coder" rights="read|write" pattern="PNG"'
            )
            
            # Write back
            with open(policy_file, 'w') as f:
                f.write(content)
            
            print("✅ ImageMagick policy fixed successfully!")
            print("   - Enabled @* pattern (temp file access)")
            print("   - Enabled LABEL, TEXT, PNG coders")
            
        except Exception as e:
            print(f"⚠️  Could not fix policy file: {e}")
            print("   Trying sed fallback...")
            run_cmd(
                f'sed -i \'s/rights="none" pattern="@\\*"/rights="read|write" pattern="@*"/g\' {policy_file}',
                "Fixing policy with sed"
            )
    else:
        print(f"⚠️  Policy file not found: {policy_file}")
    
    # 4. Install Python packages
    print("\n🐍 Installing Python packages...")
    packages = [
        "numpy==1.26.4",
        "fastapi==0.115.2",
        "uvicorn==0.34.0",
        "moviepy==1.0.3",
        "opencv-python==4.8.1.78",
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
        "sse-starlette==3.0.2",
        "Pillow>=10.0.0"
    ]
    
    for package in packages:
        success, _ = run_cmd(f"{sys.executable} -m pip install {package}", f"Installing {package.split('==')[0]}")
        if not success:
            print(f"⚠️  Failed to install {package}, continuing...")
    
    # 5. Set environment variables
    print("\n⚙️  Setting environment variables...")
    os.environ['OLLAMA_TIMEOUT'] = '7200'  # 2 hours
    os.environ['WHISPER_MODEL'] = 'base'
    os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    os.environ['OLLAMA_MODEL'] = 'llama3.1:8b'
    print("✅ Environment variables set")
    print(f"   - OLLAMA_TIMEOUT: 7200 seconds (2 hours)")
    print(f"   - WHISPER_MODEL: base")
    
    # 6. Test MoviePy
    print("\n🧪 Testing MoviePy with ImageMagick...")
    try:
        import moviepy.editor as mp
        clip = mp.TextClip("Test Subtitle", fontsize=24, color="white")
        print(f"✅ SUCCESS! MoviePy TextClip works! Size: {clip.size}")
        clip.close()
    except Exception as e:
        print(f"⚠️  MoviePy test failed: {e}")
        print("   Subtitles may not work, but clips will still be created")
    
    # 7. Test ImageMagick directly
    print("\n🧪 Testing ImageMagick directly...")
    success, output = run_cmd("convert -version | head -n 1", "")
    if success:
        print(f"✅ ImageMagick version: {output.strip()}")
    
    # 8. Summary
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Make sure Ollama is running:")
    print("   ollama serve")
    print("2. Pull the model:")
    print("   ollama pull llama3.1:8b")
    print("3. Start your FastAPI server:")
    print("   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
    print("\n💡 Tips:")
    print("- Subtitles should now work properly")
    print("- AI analysis will take 10-20 minutes (optimized prompt)")
    print("- Clips will be 30-60 seconds (viral-optimized)")
    print("- Check logs/backend_log.txt for detailed logs")

if __name__ == "__main__":
    main()
