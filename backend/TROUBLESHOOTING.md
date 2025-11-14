# SupoClip Troubleshooting Guide

## Issues Fixed in This Update

### 1. ✅ ImageMagick Missing (Subtitle Creation Failure)

**Problem**: MoviePy can't create subtitles because ImageMagick is not installed or configured properly.

**Error Messages**:
```
MoviePy Error: creation of None failed because of the following error:
[Errno 2] No such file or directory: 'unset'
This error can be due to the fact that ImageMagick is not installed on your computer
```

**Solution**:
1. Run the setup script: `python fix_colab_setup.py`
2. Or manually install ImageMagick:
   ```bash
   apt-get update -y
   apt-get install -y imagemagick imagemagick-dev
   apt-get install -y libfontconfig1-dev libfreetype6-dev fonts-dejavu-core
   ```
3. Fix ImageMagick policy:
   ```bash
   sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<policy domain="path" rights="read|write" pattern="@*"/g' /etc/ImageMagick-6/policy.xml
   ```

### 2. ✅ Ollama Timeout Too Short

**Problem**: Ollama analysis times out after 1 hour, but needs 2 hours for long transcripts.

**Solution**: Updated `OLLAMA_TIMEOUT` from 3600 to 7200 seconds (2 hours).

### 3. ✅ Dependency Version Conflicts

**Problem**: Conflicting package versions causing installation issues.

**Solution**: Created `requirements.txt` with compatible versions:
- numpy==2.0.2 (instead of 1.26.4)
- protobuf compatible versions
- All packages tested to work together

## Quick Setup for Google Colab

### Option 1: Use the Setup Script
```python
# In a Colab cell:
!python fix_colab_setup.py
```

### Option 2: Use the Jupyter Notebook
Upload `SupoClip_Colab_Setup.ipynb` to Colab and run all cells.

### Option 3: Manual Setup
```python
# Install system dependencies
!apt-get update -y
!apt-get install -y imagemagick imagemagick-dev ffmpeg
!apt-get install -y libfontconfig1-dev libfreetype6-dev fonts-dejavu-core

# Fix ImageMagick policy
!sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<policy domain="path" rights="read|write" pattern="@*"/g' /etc/ImageMagick-6/policy.xml

# Install Python packages
!pip install -r requirements.txt

# Set environment variables
import os
os.environ['OLLAMA_TIMEOUT'] = '7200'  # 2 hours
```

## Common Issues and Solutions

### Issue: "No video file found after download"
**Cause**: YouTube download failed or file not found.
**Solution**: Check YouTube URL validity and network connection.

### Issue: "Ollama connection test failed"
**Cause**: Ollama server not running or wrong URL.
**Solution**: 
1. Start Ollama: `ollama serve`
2. Check URL in environment variables
3. Pull model: `ollama pull llama3.1:8b`

### Issue: "Database connection failed"
**Cause**: Wrong database URL or network issues.
**Solution**: Update `DATABASE_URL` environment variable with correct credentials.

### Issue: "Failed to create subtitle"
**Cause**: ImageMagick not properly configured.
**Solution**: Run the ImageMagick setup steps above.

### Issue: "AI analysis returned 0 segments"
**Cause**: Ollama model couldn't parse transcript or returned invalid JSON.
**Solution**: 
1. Check Ollama logs in `logs/ollama_log`
2. Verify model is working: `ollama run llama3.1:8b "Say hello"`
3. Try with shorter video first

## Environment Variables

Set these in your environment or `.env` file:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=7200  # 2 hours

# Whisper Configuration
WHISPER_MODEL=base

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Video Processing
MAX_VIDEO_DURATION=3600
MAX_CLIPS=10
CLIP_DURATION=30
```

## Testing Your Setup

### 1. Test ImageMagick
```python
import moviepy.editor as mp
clip = mp.TextClip("Test", fontsize=24, color="white")
print(f"Success! Clip size: {clip.size}")
clip.close()
```

### 2. Test Ollama
```python
import requests
response = requests.get("http://localhost:11434/api/tags")
print(f"Ollama status: {response.status_code}")
```

### 3. Test Database
```python
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect("your_database_url")
    result = await conn.fetchval("SELECT 1")
    await conn.close()
    print(f"Database test: {result}")

asyncio.run(test_db())
```

### 4. Test Full API
```bash
# Start server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health/db
```

## Performance Tips

1. **Use shorter videos for testing** (< 10 minutes)
2. **Monitor Ollama memory usage** - it can be memory-intensive
3. **Check disk space** - video processing uses temporary files
4. **Use SSD storage** if possible for better video processing performance

## Getting Help

If you're still having issues:

1. Check the logs in `logs/backend.log` and `logs/ollama_log`
2. Verify all environment variables are set correctly
3. Test each component individually (ImageMagick, Ollama, Database)
4. Try with a simple YouTube video first

## File Structure

Your project should look like this:
```
├── src/
│   ├── main.py
│   ├── ai.py
│   ├── video_utils.py
│   ├── youtube_utils.py
│   ├── config.py
│   ├── models.py
│   └── database.py
├── fonts/
│   ├── THEBOLDFONT-FREEVERSION.ttf
│   └── TikTokSans-Regular.ttf
├── transitions/
│   ├── circle_transition.mp4
│   └── flat_transition_1.mp4
├── logs/
├── requirements.txt
├── fix_colab_setup.py
└── SupoClip_Colab_Setup.ipynb
```