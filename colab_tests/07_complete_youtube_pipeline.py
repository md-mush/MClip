# =============================================================================
# COMPLETE YOUTUBE PROCESSING WITH EXTENDED OLLAMA TIMEOUTS & ROBUST MONITORING
# =============================================================================
# This script handles slow Ollama responses in Google Colab and ensures the
# entire pipeline waits at least 30 minutes for AI analysis.
# =============================================================================

import os
import subprocess
import time
import requests
import json
from pathlib import Path

print("🎯 YOUTUBE PROCESSING WITH EXTENDED OLLAMA TIMEOUTS")
print("=" * 70)

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-123"
TEST_VIDEO = "https://www.youtube.com/watch?v=JjvN_hYDp3g"
OLLAMA_URL = "http://localhost:11434"

# Extended timeout configuration
OLLAMA_SIMPLE_TEST_TIMEOUT = 300  # 5 minutes for simple "Hi" test
OLLAMA_ANALYSIS_TIMEOUT = 1800    # 30 minutes for transcript analysis
TOTAL_PROCESSING_TIMEOUT = 3600   # 60 minutes total pipeline (more than enough)
MAX_READ_TIMEOUT_RETRIES = 15     # Allow up to 15 read timeout errors

# =============================================================================
# 1. OLLAMA MANAGER WITH EXTENDED TIMEOUTS
# =============================================================================

class OllamaManagerExtended:
    def __init__(self):
        self.base_url = OLLAMA_URL
        self.process = None
        
    def is_ollama_running(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def start_ollama(self):
        """Start Ollama service"""
        print("🚀 Starting Ollama service...")
        
        # Kill any existing Ollama processes
        try:
            subprocess.run(['pkill', '-f', 'ollama'], capture_output=True)
            time.sleep(3)
        except:
            pass
        
        # Set environment for Drive storage
        os.environ['OLLAMA_MODELS'] = '/content/drive/MyDrive/ollama_models'
        
        # Start Ollama
        self.process = subprocess.Popen(['ollama', 'serve'], 
                                      stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL)
        
        print(f"📦 Ollama starting with PID: {self.process.pid}")
        
        # Wait for Ollama to be ready (longer wait)
        for i in range(40):  # Increased to 40 attempts
            time.sleep(3)    # Increased sleep time
            if self.is_ollama_running():
                print("✅ Ollama started successfully!")
                return True
            if i % 5 == 0:
                print(f"⏳ Waiting for Ollama... ({i+1}/40)")
        
        print("❌ Ollama failed to start within 2 minutes")
        return False
    
    def test_ollama_simple(self, max_wait=OLLAMA_SIMPLE_TEST_TIMEOUT):
        """Test Ollama with a simple 'Hi' request with extended timeout"""
        print(f"🔍 Testing Ollama with simple request (timeout: {max_wait}s)...")
        
        test_payload = {
            "model": "llama3.1:8b",
            "prompt": "Just say 'Hi' and nothing else.",
            "stream": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=test_payload,
                timeout=max_wait
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', 'No response').strip()
                print(f"✅ Ollama responded in {response_time:.2f}s: '{response_text}'")
                return True, response_time
            else:
                print(f"❌ Ollama returned error: {response.status_code}")
                return False, response_time
                
        except requests.exceptions.Timeout:
            print(f"❌ Ollama test timeout after {max_wait}s - Ollama is not responsive")
            return False, max_wait
        except Exception as e:
            print(f"❌ Ollama test failed: {e}")
            return False, 0
    
    def ensure_ollama_responsive(self, max_retries=2):
        """Ensure Ollama is responsive with extended timeouts"""
        print("🔧 Ensuring Ollama is responsive...")
        
        for attempt in range(max_retries):
            print(f"🔄 Responsiveness check attempt {attempt + 1}/{max_retries}")
            
            # First check if running
            if not self.is_ollama_running():
                print("⚠️ Ollama not running, starting...")
                if not self.start_ollama():
                    continue
                time.sleep(10)  # Give it more time to stabilize
            
            # Test with simple request (5 minute timeout)
            is_working, response_time = self.test_ollama_simple(max_wait=OLLAMA_SIMPLE_TEST_TIMEOUT)
            
            if is_working:
                if response_time > 60:
                    print(f"⚠️ Ollama is slow (took {response_time:.2f}s) but working")
                    print(f"💡 Actual analysis will take 20-30 minutes. Be patient!")
                else:
                    print("✅ Ollama is responsive!")
                return True
            else:
                print("🔧 Ollama not responsive, restarting...")
                self.start_ollama()
                time.sleep(10)  # Wait after restart
        
        print("❌ Ollama failed to become responsive after all retries")
        return False

# =============================================================================
# 2. SERVER MANAGER
# =============================================================================

class ServerManager:
    def __init__(self):
        self.base_url = BASE_URL
        self.process = None
        
    def is_server_running(self):
        """Check if FastAPI server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting FastAPI server...")
        
        # Kill any existing processes
        try:
            subprocess.run(['fuser', '-k', '8000/tcp'], capture_output=True)
            subprocess.run(['pkill', '-f', 'uvicorn'], capture_output=True)
            time.sleep(3)
        except:
            pass
        
        # Start server
        self.process = subprocess.Popen([
            'uvicorn', 'src.main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000',
            '--workers', '1'
        ], 
        cwd='/content/drive/MyDrive/my_project/backend',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
        
        # Wait for server to be ready (longer wait)
        for i in range(40):
            time.sleep(3)
            if self.is_server_running():
                print("✅ FastAPI server started successfully!")
                return True
            if i % 5 == 0:
                print(f"⏳ Waiting for server... ({i+1}/40)")
        
        print("❌ Server failed to start within 2 minutes")
        return False
    
    def ensure_server_running(self):
        """Ensure server is running"""
        if self.is_server_running():
            print("✅ FastAPI server is already running")
            return True
        else:
            print("🔧 Server not running, starting...")
            return self.start_server()

# =============================================================================
# 3. AI STAGE MANAGER WITH EXTENDED PATIENCE
# =============================================================================

class AIStageManagerExtended:
    def __init__(self, ollama_manager):
        self.ollama = ollama_manager
        self.ai_stage_start_time = None
        
    def monitor_ai_stage_with_patience(self, task_id, timeout=OLLAMA_ANALYSIS_TIMEOUT):
        """Monitor AI analysis stage with extended patience - waits up to 30 minutes"""
        print(f"🎯 Starting AI stage monitoring (timeout: {timeout//60} minutes)...")
        
        start_time = time.time()
        last_status_print = time.time()
        ai_stage_entered = False
        read_timeout_count = 0
        
        while time.time() - start_time < timeout:
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Get task status
                response = requests.get(
                    f"{BASE_URL}/tasks/{task_id}",
                    headers={"user_id": TEST_USER_ID},
                    timeout=30
                )
                
                if response.status_code == 200:
                    task_data = response.json()
                    current_step = task_data.get("current_step", "")
                    status = task_data.get("status", "")
                    
                    # Reset read timeout counter on successful response
                    read_timeout_count = 0
                    
                    # Check if we're in AI analysis stage (status contains the step info)
                    if "AI analyzing" in status or "AI analyzing" in current_step or "AI analysis" in status or "AI analysis" in current_step:
                        if not ai_stage_entered:
                            ai_stage_entered = True
                            self.ai_stage_start_time = current_time
                            print("🎯 AI ANALYSIS STAGE DETECTED!")
                            print("⏳ This will take 20-30 minutes. Please be patient...")
                            print("⏳ Do not interrupt the process!")
                        
                        # Print progress every 5 minutes
                        if current_time - last_status_print > 300:  # Every 5 minutes
                            ai_duration = current_time - self.ai_stage_start_time
                            elapsed_min = int(elapsed // 60)
                            ai_min = int(ai_duration // 60)
                            print(f"🕐 Total: {elapsed_min}m | AI Stage: {ai_min}m - Still processing...")
                            print(f"💡 Expected time: 20-30 minutes. Current: {ai_min}m")
                            last_status_print = current_time
                    
                    # Check if AI stage completed
                    elif ai_stage_entered and "AI analyzing" not in status and "AI analyzing" not in current_step:
                        ai_total_time = current_time - self.ai_stage_start_time if self.ai_stage_start_time else 0
                        print(f"✅ AI analysis completed in {ai_total_time//60:.0f}m {ai_total_time%60:.0f}s!")
                        return True
                    
                    # Check task completion
                    if status == "completed":
                        print("✅ Task completed!")
                        return True
                    elif status == "error":
                        error_msg = task_data.get("error", "Unknown error")
                        print(f"❌ Task failed: {error_msg}")
                        return False
                
                # Wait 30 seconds between checks during AI stage
                wait_time = 30 if ai_stage_entered else 15
                time.sleep(wait_time)
                
            except requests.exceptions.ReadTimeout:
                read_timeout_count += 1
                if ai_stage_entered:
                    print(f"⏰ Read timeout #{read_timeout_count} during AI analysis - this is normal, continuing...")
                    print(f"💡 Will continue checking for up to {MAX_READ_TIMEOUT_RETRIES} read timeouts")
                else:
                    print(f"⏰ Read timeout #{read_timeout_count} - continuing...")
                
                if read_timeout_count >= MAX_READ_TIMEOUT_RETRIES:
                    print(f"⚠️ Too many read timeouts ({read_timeout_count}). Continuing anyway...")
                    read_timeout_count = 0  # Reset but continue
                
                time.sleep(30)
            except Exception as e:
                print(f"⚠️ AI stage monitoring error: {e}")
                time.sleep(30)
        
        print(f"⏰ AI stage monitoring timeout after {timeout//60} minutes")
        return False

# =============================================================================
# 4. MAIN PROCESSING PIPELINE WITH EXTENDED TIMEOUTS
# =============================================================================

class ExtendedYouTubePipeline:
    def __init__(self):
        self.server_manager = ServerManager()
        self.ollama_manager = OllamaManagerExtended()
        self.ai_manager = AIStageManagerExtended(self.ollama_manager)
        
    def setup_environment(self):
        """Setup complete environment"""
        print("\n" + "="*70)
        print("🔧 SETTING UP ENVIRONMENT")
        print("="*70)
        
        # Step 1: Ensure server is running
        if not self.server_manager.ensure_server_running():
            print("❌ Failed to start server")
            return False
        
        # Step 2: Ensure Ollama is responsive (with extended timeouts)
        print("\n🧪 TESTING OLLAMA RESPONSIVENESS...")
        if not self.ollama_manager.ensure_ollama_responsive():
            print("❌ Ollama failed responsiveness test")
            return False
        
        print("✅ Environment setup complete!")
        return True
    
    def create_processing_task(self):
        """Create YouTube processing task"""
        print("\n" + "="*70)
        print("🎬 CREATING PROCESSING TASK")
        print("="*70)
        
        payload = {
            "source": {
                "url": TEST_VIDEO,
                "title": "Extended Timeout Test"
            },
            "font_options": {
                "font_family": "TikTokSans-Regular",
                "font_size": 24,
                "font_color": "#FFFFFF"
            }
        }
        
        try:
            print(f"📹 Processing video: {TEST_VIDEO}")
            response = requests.post(
                f"{BASE_URL}/start-with-progress",
                json=payload,
                headers={
                    "user_id": TEST_USER_ID,
                    "Content-Type": "application/json"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                print(f"✅ Task created successfully: {task_id}")
                return task_id
            else:
                print(f"❌ Task creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating task: {e}")
            return None
    
    def monitor_task_with_extended_patience(self, task_id, timeout=TOTAL_PROCESSING_TIMEOUT):
        """Monitor task with extended patience for Ollama - handles read timeouts robustly"""
        print("\n" + "="*70)
        print("📊 MONITORING TASK PROGRESS")
        print("="*70)
        print(f"⏰ Maximum wait time: {timeout//60} minutes")
        print("💡 AI analysis may take 20-30 minutes. Please be patient...")
        print(f"💡 Will allow up to {MAX_READ_TIMEOUT_RETRIES} read timeout errors")
        
        start_time = time.time()
        last_status = ""
        last_step = ""
        last_print = time.time()
        read_timeout_count = 0
        
        while time.time() - start_time < timeout:
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                elapsed_min = int(elapsed // 60)
                
                # Get task status
                response = requests.get(
                    f"{BASE_URL}/tasks/{task_id}",
                    headers={"user_id": TEST_USER_ID},
                    timeout=30
                )
                
                # Reset read timeout counter on successful response
                read_timeout_count = 0
                
                if response.status_code == 200:
                    task_data = response.json()
                    status = task_data.get("status", "unknown")
                    current_step = task_data.get("current_step", "")
                    progress = task_data.get("progress", 0)
                    
                    # Print status if changed or every 2 minutes
                    if (status != last_status or current_step != last_step or 
                        current_time - last_print > 120):
                        
                        print(f"\n🕐 [{elapsed_min:02d}:{int(elapsed%60):02d}] Status: {status}")
                        print(f"📈 Progress: {progress}%")
                        print(f"🔧 Step: {current_step}")
                        last_status = status
                        last_step = current_step
                        last_print = current_time
                    
                    # Handle AI analysis stage with extended patience (status contains the step info)
                    if "AI analyzing" in status or "AI analyzing" in current_step or "AI analysis" in status or "AI analysis" in current_step:
                        print("🎯 ENTERING AI ANALYSIS STAGE...")
                        ai_success = self.ai_manager.monitor_ai_stage_with_patience(task_id)
                        if not ai_success:
                            print("❌ AI stage failed")
                            return False
                        # If we get here, AI stage completed successfully
                        continue
                    
                    # Check completion
                    if status == "completed":
                        total_time = time.time() - start_time
                        print(f"\n🎉 TASK COMPLETED SUCCESSFULLY!")
                        print(f"⏱️ Total processing time: {total_time//60:.0f}m {total_time%60:.0f}s")
                        return True
                    elif status == "error":
                        error_msg = task_data.get("error", "Unknown error")
                        print(f"\n❌ TASK FAILED: {error_msg}")
                        return False
                
                # Wait between checks
                time.sleep(20)
                
            except requests.exceptions.ReadTimeout:
                read_timeout_count += 1
                print(f"⏰ Read timeout #{read_timeout_count} - continuing...")
                print(f"💡 Will continue for up to {MAX_READ_TIMEOUT_RETRIES} read timeouts")
                
                if read_timeout_count >= MAX_READ_TIMEOUT_RETRIES:
                    print(f"⚠️ Reached {read_timeout_count} read timeouts. Continuing anyway...")
                    read_timeout_count = 0  # Reset but continue
                
                time.sleep(20)
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(20)
        
        total_time = time.time() - start_time
        print(f"\n⏰ Monitoring timeout after {total_time//60:.0f} minutes")
        return False
    
    def get_results(self, task_id):
        """Get final results"""
        print("\n" + "="*70)
        print("📋 GETTING FINAL RESULTS")
        print("="*70)
        
        try:
            # Get task final status
            response = requests.get(
                f"{BASE_URL}/tasks/{task_id}",
                headers={"user_id": TEST_USER_ID},
                timeout=30
            )
            
            if response.status_code == 200:
                task_data = response.json()
                print(f"✅ Final Status: {task_data.get('status')}")
                print(f"📊 Final Progress: {task_data.get('progress', 0)}%")
            
            # Get clips
            clips_response = requests.get(
                f"{BASE_URL}/tasks/{task_id}/clips",
                headers={"user_id": TEST_USER_ID},
                timeout=30
            )
            
            if clips_response.status_code == 200:
                clips_data = clips_response.json()
                clips = clips_data.get('clips', [])
                print(f"\n🎬 GENERATED CLIPS: {len(clips)}")
                
                if clips:
                    print("\n📋 CLIP DETAILS:")
                    for i, clip in enumerate(clips):
                        print(f"\nClip {i+1}:")
                        print(f"  📝 Text: {clip.get('text', 'N/A')}")
                        print(f"  ⏱️ Duration: {clip.get('duration', 'N/A')}s")
                        print(f"  🎯 Score: {clip.get('relevance_score', 'N/A')}")
                        print(f"  🕐 Start: {clip.get('start_time', 'N/A')}")
                        print(f"  🛑 End: {clip.get('end_time', 'N/A')}")
                    return True
                else:
                    print("❌ No clips were generated")
                    return False
            else:
                print(f"❌ Failed to get clips: {clips_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting results: {e}")
            return False
    
    def run_extended_pipeline(self):
        """Run the complete pipeline with extended timeouts"""
        print("🎯 STARTING YOUTUBE PROCESSING WITH EXTENDED TIMEOUTS")
        print("⏰ Estimated time: 30-45 minutes")
        print("💡 Ollama is slow - allowing 30 minutes for AI analysis")
        print("💡 Will handle up to 15 read timeout errors")
        print("=" * 70)
        
        start_time = time.time()
        
        # Step 1: Setup environment
        if not self.setup_environment():
            print("❌ Pipeline failed at environment setup")
            return False
        
        # Step 2: Create processing task
        task_id = self.create_processing_task()
        if not task_id:
            print("❌ Pipeline failed at task creation")
            return False
        
        print(f"\n📋 Task ID: {task_id}")
        print("⏳ Starting monitoring with extended patience...")
        
        # Step 3: Monitor with extended patience
        completed = self.monitor_task_with_extended_patience(task_id)
        
        # Step 4: Get results
        if completed:
            success = self.get_results(task_id)
            total_time = time.time() - start_time
            
            print("\n" + "=" * 70)
            print("🎯 PIPELINE COMPLETE")
            print("=" * 70)
            print(f"⏱️ Total time: {total_time//60:.0f}m {total_time%60:.0f}s")
            
            if success:
                print("✅ SUCCESS - Clips generated!")
            else:
                print("❌ FAILED - No clips generated")
            return success
        else:
            total_time = time.time() - start_time
            print(f"\n❌ Pipeline failed after {total_time//60:.0f}m {total_time%60:.0f}s")
            return False

# =============================================================================
# 5. RUN THE EXTENDED PIPELINE
# =============================================================================

if __name__ == "__main__":
    # Create and run extended pipeline
    pipeline = ExtendedYouTubePipeline()
    pipeline.run_extended_pipeline()

