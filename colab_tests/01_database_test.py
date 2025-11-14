# =============================================================================
# DATABASE CONNECTION TEST SCRIPT FOR COLAB
# =============================================================================
# Paste this entire script into a Colab cell and run it

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"  # Your backend URL
print(f"🔗 Testing backend at: {BASE_URL}")

def test_database_connection():
    """Test database connectivity"""
    print("\n" + "="*60)
    print("🗄️  TESTING DATABASE CONNECTION")
    print("="*60)
    
    try:
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/health/db", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Database connection successful!")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Database connection failed!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server!")
        print("Make sure your backend is running with: uvicorn src.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\n" + "="*60)
    print("🏠 TESTING ROOT ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working!")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Root endpoint failed!")
            print(f"Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing root endpoint: {e}")
        return False

# Run tests
if __name__ == "__main__":
    print("🚀 Starting Backend Tests...")
    
    # Test root endpoint first
    root_success = test_root_endpoint()
    
    # Test database connection
    db_success = test_database_connection()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    print(f"Root Endpoint: {'✅ PASS' if root_success else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    
    if root_success and db_success:
        print("\n🎉 All basic tests passed! Ready for authentication tests.")
    else:
        print("\n⚠️  Some tests failed. Check your backend setup.")
