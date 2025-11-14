# =============================================================================
# PERSISTENT TASK MONITORING SCRIPT FOR COLAB
# =============================================================================
# This script will monitor your task every 5 minutes for up to 30 minutes
# Paste this entire script into a Colab cell and run it

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-123"
TASK_ID = "df416d63-b090-4770-b75f-24e1896343ea"  # Your current task ID

def check_task_status():
    """Check current task status"""
    try:
        headers = {"user_id": TEST_USER_ID}
        
        response = requests.get(
            f"{BASE_URL}/tasks/{TASK_ID}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
            
    except requests.exceptions.ReadTimeout:
        print("⏰ Request timeout - backend is busy")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def monitor_task():
    """Monitor task every 5 minutes"""
    print("🚀 Starting Persistent Task Monitoring")
    print("=" * 60)
    print(f"📋 Task ID: {TASK_ID}")
    print(f"👤 User ID: {TEST_USER_ID}")
    print(f"🔗 Backend: {BASE_URL}")
    print(f"⏰ Will monitor for up to 30 minutes")
    print(f"🔄 Checking every 5 minutes...")
    print("=" * 60)
    
    start_time = time.time()
    max_wait_time = 1800  # 30 minutes
    check_count = 0
    last_status = None
    
    while time.time() - start_time < max_wait_time:
        check_count += 1
        elapsed_minutes = int((time.time() - start_time) // 60)
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n🔍 Check #{check_count} at {current_time} (after {elapsed_minutes} minutes)")
        
        task_data = check_task_status()
        
        if task_data:
            status = task_data.get("status", "unknown")
            
            if status != last_status:
                print(f"🔄 Status changed: {last_status} → {status}")
                last_status = status
            
            print(f"📊 Current Status: {status}")
            
            if status == "completed":
                print("🎉 TASK COMPLETED!")
                print("📊 Final Data:")
                print(json.dumps(task_data, indent=2))
                
                # Try to get clips
                print("\n🎞️  Attempting to get clips...")
                try:
                    clips_response = requests.get(
                        f"{BASE_URL}/tasks/{TASK_ID}/clips",
                        headers={"user_id": TEST_USER_ID},
                        timeout=30
                    )
                    
                    if clips_response.status_code == 200:
                        clips_data = clips_response.json()
                        clips = clips_data.get("clips", [])
                        print(f"✅ Found {len(clips)} clips!")
                        
                        for i, clip in enumerate(clips):
                            print(f"\n  Clip {i+1}:")
                            print(f"    - Duration: {clip.get('duration', 'N/A')}s")
                            print(f"    - Start: {clip.get('start_time', 'N/A')}")
                            print(f"    - End: {clip.get('end_time', 'N/A')}")
                            print(f"    - Score: {clip.get('relevance_score', 'N/A')}")
                            print(f"    - Text: {clip.get('text', 'N/A')[:100]}...")
                    else:
                        print(f"❌ Failed to get clips: {clips_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error getting clips: {e}")
                
                return True
                
            elif status == "error":
                print("❌ TASK FAILED!")
                print("📊 Error Data:")
                print(json.dumps(task_data, indent=2))
                return False
                
            else:
                print(f"⏳ Still processing... Status: {status}")
        else:
            print("⚠️  Could not get task data")
        
        print(f"⏰ Elapsed: {elapsed_minutes} minutes / {max_wait_time//60} minutes")
        print(f"🔄 Next check in 5 minutes...")
        
        # Wait 5 minutes (300 seconds)
        time.sleep(300)
    
    print(f"\n⏰ Monitoring timeout after {max_wait_time//60} minutes")
    print("📊 Final status check:")
    
    final_data = check_task_status()
    if final_data:
        print(json.dumps(final_data, indent=2))
    
    return False

# Run the monitoring
if __name__ == "__main__":
    success = monitor_task()
    
    if success:
        print("\n🎉 Monitoring completed successfully!")
    else:
        print("\n⚠️  Monitoring ended (timeout or error)")
    
    print("\n💡 Tip: You can run this script again to continue monitoring")
