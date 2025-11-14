# =============================================================================
# QUICK TASK STATUS CHECK SCRIPT FOR COLAB
# =============================================================================
# Paste this script to check your current task status

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-123"  # Your user ID
TASK_ID = "df416d63-b090-4770-b75f-24e1896343ea"  # Your current task ID

def check_task_status():
    """Check current task status"""
    print(f"🔍 Checking task: {TASK_ID}")
    print(f"👤 User ID: {TEST_USER_ID}")
    print(f"🔗 Backend: {BASE_URL}")
    print("=" * 60)
    
    try:
        headers = {"user_id": TEST_USER_ID}
        
        response = requests.get(
            f"{BASE_URL}/tasks/{TASK_ID}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            
            print(f"✅ Task Status: {status}")
            print(f"📊 Full Response:")
            print(json.dumps(data, indent=2))
            
            if status == "completed":
                print("\n🎉 Task completed! Checking clips...")
                check_clips()
            elif status == "error":
                print("\n❌ Task failed!")
            else:
                print(f"\n⏳ Task still processing... Status: {status}")
                
        else:
            print(f"❌ Failed to get task status!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking task: {e}")

def check_clips():
    """Check task clips if completed"""
    try:
        headers = {"user_id": TEST_USER_ID}
        
        response = requests.get(
            f"{BASE_URL}/tasks/{TASK_ID}/clips",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            clips = data.get("clips", [])
            
            print(f"🎞️  Found {len(clips)} clips:")
            for i, clip in enumerate(clips):
                print(f"\n  Clip {i+1}:")
                print(f"    - Duration: {clip.get('duration', 'N/A')}s")
                print(f"    - Start: {clip.get('start_time', 'N/A')}")
                print(f"    - End: {clip.get('end_time', 'N/A')}")
                print(f"    - Score: {clip.get('relevance_score', 'N/A')}")
                print(f"    - Text: {clip.get('text', 'N/A')[:100]}...")
                print(f"    - Video URL: {clip.get('video_url', 'N/A')}")
        else:
            print(f"❌ Failed to get clips: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking clips: {e}")

# Run the check
if __name__ == "__main__":
    check_task_status()
