"""
Google Colab script to test the /split-video endpoint
This script splits a video into multiple clips of specified duration
"""

import requests
import json
from pathlib import Path
import time

# Configuration - UPDATE THESE VALUES
LOCAL_VIDEO_PATH = "/content/your_video.mp4"  # Update this to your video path
DURATION_SECONDS = 30  # Duration in seconds for each clip (e.g., 30 seconds)
API_BASE_URL = "http://localhost:8000"  # Update if your API is on a different host/port

def split_video(video_path: str, duration: int):
    """
    Split a video into multiple clips of specified duration
    
    Args:
        video_path: Path to the video file on the local system
        duration: Duration in seconds for each clip
    """
    print(f"🎬 Starting video split operation")
    print(f"📹 Video path: {video_path}")
    print(f"⏱️  Duration per clip: {duration} seconds")
    print(f"🌐 API URL: {API_BASE_URL}")
    
    # Verify video file exists
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Prepare request payload
    payload = {
        "video_path": video_path,
        "duration": duration
    }
    
    print("\n📤 Sending request to API...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/split-video",
            json=payload,
            timeout=3600  # 1 hour timeout for long videos
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✅ Video split successfully!")
        print(f"📊 Total clips created: {result['total_clips']}")
        print(f"⏱️  Duration per clip: {result['duration_per_clip_seconds']} seconds")
        print(f"📁 Output directory: {result['output_directory']}")
        
        print("\n📋 Clips created:")
        for i, clip in enumerate(result['clips'], 1):
            print(f"\n  Clip {i}:")
            print(f"    Filename: {clip['filename']}")
            print(f"    Duration: {clip['duration']:.2f} seconds")
            print(f"    Time range: {clip['start_time']:.2f}s - {clip['end_time']:.2f}s")
            print(f"    Download URL: {clip['download_url']}")
            print(f"    Full path: {clip['path']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Error response: {e.response.text}")
        raise

def download_clip(download_url: str, output_path: str):
    """
    Download a clip from the API
    
    Args:
        download_url: URL path from the API response (e.g., "/download-split-clip/abc123/clip_0001.mp4")
        output_path: Local path to save the downloaded clip
    """
    full_url = f"{API_BASE_URL}{download_url}"
    print(f"📥 Downloading clip from: {full_url}")
    
    try:
        response = requests.get(full_url, stream=True)
        response.raise_for_status()
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path_obj, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Clip saved to: {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading clip: {e}")
        raise

# Main execution
if __name__ == "__main__":
    # Update these variables
    LOCAL_VIDEO_PATH = "/content/your_video.mp4"  # CHANGE THIS to your video path
    DURATION_SECONDS = 30  # CHANGE THIS to desired clip duration in seconds
    
    print("=" * 80)
    print("VIDEO SPLIT TEST SCRIPT")
    print("=" * 80)
    
    # Split the video
    result = split_video(LOCAL_VIDEO_PATH, DURATION_SECONDS)
    
    # Optional: Download all clips to Colab
    print("\n" + "=" * 80)
    print("DOWNLOADING CLIPS TO COLAB")
    print("=" * 80)
    
    download_dir = Path("/content/downloaded_clips")
    download_dir.mkdir(exist_ok=True)
    
    for clip in result['clips']:
        output_path = download_dir / clip['filename']
        try:
            download_clip(clip['download_url'], str(output_path))
        except Exception as e:
            print(f"⚠️  Failed to download {clip['filename']}: {e}")
    
    print("\n" + "=" * 80)
    print("✅ ALL DONE!")
    print("=" * 80)
    print(f"📁 Clips saved to: {download_dir}")
