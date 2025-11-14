# =============================================================================
# COMPREHENSIVE ENDPOINT TESTING SCRIPT FOR COLAB
# =============================================================================
# Paste this entire script into a Colab cell and run it

import requests
import json
import time
import uuid
import os

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-123"  # Replace with your actual user ID
print(f"🔗 Testing all endpoints at: {BASE_URL}")

class EndpointTester:
    def __init__(self, base_url, user_id):
        self.base_url = base_url
        self.user_id = user_id
        self.results = {}
        
    def test_endpoint(self, method, endpoint, data=None, headers=None, description=""):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            result = {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.text[:500] if response.text else "",
                "description": description
            }
            
            # Try to parse JSON response
            try:
                result["json"] = response.json()
            except:
                result["json"] = None
                
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": description
            }
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting Comprehensive Endpoint Tests...")
        print("="*80)
        
        # Test 1: Root endpoint
        print("\n1️⃣  Testing Root Endpoint")
        self.results["root"] = self.test_endpoint("GET", "/", description="Root endpoint")
        self.print_result("root")
        
        # Test 2: Health check
        print("\n2️⃣  Testing Health Check")
        self.results["health"] = self.test_endpoint("GET", "/health/db", description="Database health check")
        self.print_result("health")
        
        # Test 3: Fonts endpoint
        print("\n3️⃣  Testing Fonts Endpoint")
        self.results["fonts"] = self.test_endpoint("GET", "/fonts", description="Get available fonts")
        self.print_result("fonts")
        
        # Test 4: Transitions endpoint
        print("\n4️⃣  Testing Transitions Endpoint")
        self.results["transitions"] = self.test_endpoint("GET", "/transitions", description="Get available transitions")
        self.print_result("transitions")
        
        # Test 5: Task creation (basic)
        print("\n5️⃣  Testing Basic Task Creation")
        task_data = {
            "source": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "title": None
            },
            "font_options": {
                "font_family": "TikTokSans-Regular",
                "font_size": 24,
                "font_color": "#FFFFFF"
            }
        }
        headers = {
            "Content-Type": "application/json",
            "user_id": self.user_id
        }
        
        self.results["task_creation"] = self.test_endpoint(
            "POST", 
            "/start", 
            data=task_data, 
            headers=headers,
            description="Create basic task"
        )
        self.print_result("task_creation")
        
        # Test 6: Task creation with progress
        print("\n6️⃣  Testing Task Creation with Progress")
        self.results["task_progress"] = self.test_endpoint(
            "POST", 
            "/start-with-progress", 
            data=task_data, 
            headers=headers,
            description="Create task with progress tracking"
        )
        self.print_result("task_progress")
        
        # Extract task ID if successful
        task_id = None
        if self.results["task_progress"]["success"] and self.results["task_progress"]["json"]:
            task_id = self.results["task_progress"]["json"].get("task_id")
            print(f"📋 Task ID: {task_id}")
        
        # Test 7: Task details (if we have a task ID)
        if task_id:
            print("\n7️⃣  Testing Task Details")
            self.results["task_details"] = self.test_endpoint(
                "GET", 
                f"/tasks/{task_id}", 
                headers={"user_id": self.user_id},
                description="Get task details"
            )
            self.print_result("task_details")
            
            # Test 8: Task clips
            print("\n8️⃣  Testing Task Clips")
            self.results["task_clips"] = self.test_endpoint(
                "GET", 
                f"/tasks/{task_id}/clips", 
                headers={"user_id": self.user_id},
                description="Get task clips"
            )
            self.print_result("task_clips")
        else:
            print("\n7️⃣  Skipping task details/clips (no task ID)")
            self.results["task_details"] = {"success": False, "error": "No task ID"}
            self.results["task_clips"] = {"success": False, "error": "No task ID"}
        
        # Test 9: File upload (mock)
        print("\n9️⃣  Testing File Upload Endpoint")
        # Note: This would require actual file upload, so we'll just test the endpoint exists
        self.results["upload"] = self.test_endpoint(
            "POST", 
            "/upload", 
            description="File upload endpoint (mock test)"
        )
        self.print_result("upload")
        
        # Print summary
        self.print_summary()
    
    def print_result(self, test_name):
        """Print result for a single test"""
        result = self.results[test_name]
        
        if result["success"]:
            print(f"✅ {result['description']} - PASS")
            if "status_code" in result:
                print(f"   Status: {result['status_code']}")
        else:
            print(f"❌ {result['description']} - FAIL")
            if "error" in result:
                print(f"   Error: {result['error']}")
            elif "status_code" in result:
                print(f"   Status: {result['status_code']}")
                print(f"   Response: {result['response'][:200]}...")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📊 Detailed Results:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Your backend is working perfectly!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the details above.")

# Run the comprehensive tests
if __name__ == "__main__":
    tester = EndpointTester(BASE_URL, TEST_USER_ID)
    tester.run_all_tests()
    
    print("\n" + "="*80)
    print("🔧 TROUBLESHOOTING TIPS")
    print("="*80)
    print("1. Make sure your backend is running: uvicorn src.main:app --host 0.0.0.0 --port 8000")
    print("2. Check your database connection")
    print("3. Verify your user ID exists in the database")
    print("4. Check backend logs for detailed error messages")
    print("5. Ensure all required dependencies are installed")
