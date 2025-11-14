# =============================================================================
# YOUTUBE PROCESSING TEST SCRIPT FOR COLAB
# =============================================================================
# Paste this entire script into a Colab cell and run it

import requests
import json
import time
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
print(f"🔗 Testing YouTube processing at: {BASE_URL}")

# Test data
TEST_USER_ID = "test-user-123"  # Replace with your actual user ID
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
TEST_FONT_OPTIONS = {
    "font_family": "TikTokSans-Regular",
    "font_size": 24,
    "font_color": "#FFFFFF"
}

def test_youtube_task_creation():
    """Test creating a YouTube processing task"""
    print("\n" + "="*60)
    print("🎬 TESTING YOUTUBE TASK CREATION")
    print("="*60)
    
    try:
        payload = {
            "source": {
                "url": TEST_YOUTUBE_URL,
                "title": None
            },
            "font_options": TEST_FONT_OPTIONS
        }
        
        headers = {
            "Content-Type": "application/json",
            "user_id": TEST_USER_ID
        }
        
        print(f"📹 YouTube URL: {TEST_YOUTUBE_URL}")
        print(f"👤 User ID: {TEST_USER_ID}")
        print(f"🎨 Font Options: {json.dumps(TEST_FONT_OPTIONS, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/start-with-progress",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            print("✅ Task created successfully!")
            print(f"📋 Task ID: {task_id}")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return task_id
        else:
            print(f"❌ Task creation failed!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return None

def test_task_status(task_id):
    """Test getting task status"""
    print("\n" + "="*60)
    print("📊 TESTING TASK STATUS")
    print("="*60)
    
    try:
        headers = {"user_id": TEST_USER_ID}
        
        response = requests.get(
            f"{BASE_URL}/tasks/{task_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            print(f"✅ Task status retrieved!")
            print(f"📋 Task ID: {task_id}")
            print(f"📊 Status: {status}")
            print(f"📊 Full Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Failed to get task status!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting task status: {e}")
        return None

def test_task_clips(task_id):
    """Test getting task clips"""
    print("\n" + "="*60)
    print("🎞️  TESTING TASK CLIPS")
    print("="*60)
    
    try:
        headers = {"user_id": TEST_USER_ID}
        
        response = requests.get(
            f"{BASE_URL}/tasks/{task_id}/clips",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            clips = data.get("clips", [])
            print(f"✅ Clips retrieved!")
            print(f"📋 Task ID: {task_id}")
            print(f"🎞️  Number of clips: {len(clips)}")
            
            if clips:
                print("\n📝 Clip details:")
                for i, clip in enumerate(clips[:3]):  # Show first 3 clips
                    print(f"  Clip {i+1}:")
                    print(f"    - Duration: {clip.get('duration', 'N/A')}s")
                    print(f"    - Start: {clip.get('start_time', 'N/A')}")
                    print(f"    - End: {clip.get('end_time', 'N/A')}")
                    print(f"    - Score: {clip.get('relevance_score', 'N/A')}")
                    print(f"    - Text: {clip.get('text', 'N/A')[:50]}...")
            
            return data
        else:
            print(f"❌ Failed to get clips!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting clips: {e}")
        return None

def monitor_task_progress(task_id, max_wait_time=1800):  # 30 minutes
    """Monitor task progress until completion"""
    print("\n" + "="*60)
    print("⏱️  MONITORING TASK PROGRESS")
    print("="*60)
    print(f"🕐 Will monitor for up to {max_wait_time//60} minutes")
    print(f"⏰ Checking every 5 minutes...")
    
    start_time = time.time()
    last_status = None
    check_count = 0
    
    while time.time() - start_time < max_wait_time:
        try:
            check_count += 1
            elapsed_minutes = int((time.time() - start_time) // 60)
            
            print(f"\n🔍 Check #{check_count} (after {elapsed_minutes} minutes)")
            
            task_data = test_task_status(task_id)
            if not task_data:
                print("⚠️  Could not get task data, retrying in 5 minutes...")
                time.sleep(300)  # Wait 5 minutes
                continue
                
            current_status = task_data.get("status", "unknown")
            
            if current_status != last_status:
                print(f"🔄 Status changed: {last_status} → {current_status}")
                last_status = current_status
            
            if current_status == "completed":
                print("🎉 Task completed!")
                return True
            elif current_status == "error":
                print("❌ Task failed!")
                return False
            
            print(f"⏳ Current status: {current_status}")
            print(f"⏰ Elapsed: {elapsed_minutes} minutes / {max_wait_time//60} minutes")
            print(f"🔄 Next check in 5 minutes...")
            
            # Wait 5 minutes before next check
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            break
        except requests.exceptions.ReadTimeout:
            print("⏰ Request timeout - backend is busy processing")
            print("🔄 Will retry in 5 minutes...")
            time.sleep(300)  # Wait 5 minutes
            continue
        except Exception as e:
            print(f"❌ Error monitoring task: {e}")
            print("🔄 Will retry in 5 minutes...")
            time.sleep(300)  # Wait 5 minutes
            continue
    
    print(f"⏰ Monitoring timeout after {max_wait_time//60} minutes")
    return False

# Run tests
if __name__ == "__main__":
    print("🚀 Starting YouTube Processing Tests...")
    
    # Step 1: Create task
    task_id = test_youtube_task_creation()
    
    if not task_id:
        print("❌ Cannot proceed without task ID")
        exit(1)
    
    # Step 2: Monitor progress
    print(f"\n⏱️  Monitoring task {task_id}...")
    completed = monitor_task_progress(task_id, max_wait_time=1800)  # 30 minutes max
    
    # Step 3: Get final status
    final_status = test_task_status(task_id)
    
    # Step 4: Get clips if completed
    if completed:
        clips_data = test_task_clips(task_id)
    else:
        print("⚠️  Task not completed within timeout")
    
    # Summary
    print("\n" + "="*60)
    print("📋 YOUTUBE PROCESSING TEST SUMMARY")
    print("="*60)
    print(f"Task Creation: {'✅ PASS' if task_id else '❌ FAIL'}")
    print(f"Task Completion: {'✅ PASS' if completed else '⚠️  TIMEOUT'}")
    print(f"Clips Retrieved: {'✅ PASS' if completed else '❌ SKIPPED'}")
    
    if task_id:
        print(f"\n📝 Task ID for further testing: {task_id}")
        print(f"🔗 Task URL: {BASE_URL}/tasks/{task_id}")
