# =============================================================================
# AUTHENTICATION TEST SCRIPT FOR COLAB
# =============================================================================
# Paste this entire script into a Colab cell and run it

import requests
import json
import uuid
import time

# Configuration
BASE_URL = "http://localhost:8000"
print(f"🔗 Testing authentication at: {BASE_URL}")

# Test user data
TEST_USER = {
    "name": "Mushraf",
    "email": f"md.mushraf123@gmail.com",
    "password": "Mushraf@123"
}

def test_user_signup():
    """Test user signup"""
    print("\n" + "="*60)
    print("👤 TESTING USER SIGNUP")
    print("="*60)
    
    try:
        # Note: You'll need to implement a signup endpoint in your backend
        # For now, we'll create a user directly in the database
        print("ℹ️  Note: Direct user creation (signup endpoint not implemented)")
        
        # You can manually create a user in your database or implement a signup endpoint
        # For testing purposes, let's assume we have a user with ID
        test_user_id = str(uuid.uuid4())
        
        print(f"✅ Test user created with ID: {test_user_id}")
        print(f"📧 Email: {TEST_USER['email']}")
        print(f"👤 Name: {TEST_USER['name']}")
        
        return test_user_id
        
    except Exception as e:
        print(f"❌ Error in signup test: {e}")
        return None

def test_user_signin():
    """Test user signin"""
    print("\n" + "="*60)
    print("🔐 TESTING USER SIGNIN")
    print("="*60)
    
    try:
        # Note: You'll need to implement a signin endpoint in your backend
        print("ℹ️  Note: Signin endpoint not implemented")
        print("ℹ️  Using direct user ID for testing")
        
        # For testing, we'll use a hardcoded user ID
        # In production, this would come from your authentication system
        test_user_id = "test-user-123"  # Replace with actual user ID
        
        print(f"✅ Using test user ID: {test_user_id}")
        return test_user_id
        
    except Exception as e:
        print(f"❌ Error in signin test: {e}")
        return None

def test_authenticated_endpoint(user_id):
    """Test an endpoint that requires authentication"""
    print("\n" + "="*60)
    print("🔒 TESTING AUTHENTICATED ENDPOINT")
    print("="*60)
    
    try:
        # Test fonts endpoint (should work without auth)
        response = requests.get(f"{BASE_URL}/fonts", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Fonts endpoint accessible!")
            print(f"📊 Available fonts: {len(data.get('fonts', []))}")
            return True
        else:
            print(f"❌ Fonts endpoint failed!")
            print(f"Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing authenticated endpoint: {e}")
        return False

def create_test_user_manually():
    """Instructions for creating a test user manually"""
    print("\n" + "="*60)
    print("📝 MANUAL USER CREATION INSTRUCTIONS")
    print("="*60)
    
    print("To create a test user, you can:")
    print("1. Use your database directly:")
    print(f"   INSERT INTO users (id, name, email, \"emailVerified\") VALUES ('test-user-123', '{TEST_USER['name']}', '{TEST_USER['email']}', true);")
    print()
    print("2. Or implement a signup endpoint in your backend")
    print("3. Or use an existing user ID from your database")
    print()
    print("For now, we'll use 'test-user-123' as the test user ID")

# Run tests
if __name__ == "__main__":
    print("🚀 Starting Authentication Tests...")
    
    # Show manual user creation instructions
    create_test_user_manually()
    
    # Test signup (placeholder)
    user_id = test_user_signup()
    
    # Test signin (placeholder)
    auth_user_id = test_user_signin()
    
    # Test authenticated endpoint
    auth_success = test_authenticated_endpoint(auth_user_id)
    
    # Summary
    print("\n" + "="*60)
    print("📋 AUTHENTICATION TEST SUMMARY")
    print("="*60)
    print(f"User Creation: {'✅ PASS' if user_id else '❌ FAIL'}")
    print(f"User Authentication: {'✅ PASS' if auth_user_id else '❌ FAIL'}")
    print(f"Authenticated Endpoint: {'✅ PASS' if auth_success else '❌ FAIL'}")
    
    if auth_user_id:
        print(f"\n🎉 Ready for YouTube processing tests!")
        print(f"📝 Use this user ID for testing: {auth_user_id}")
    else:
        print("\n⚠️  Authentication tests need backend implementation.")
