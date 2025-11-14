# SupoClip Backend Testing Scripts for Colab

This directory contains comprehensive test scripts for your SupoClip backend running in Google Colab.

## 🚀 Quick Start

### 1. Setup (Run First)
```python
# Paste and run: 00_setup.py
```
This script will:
- Install all required dependencies
- Create necessary directories
- Set up environment variables
- Verify Colab environment

### 2. Database Connection Test
```python
# Paste and run: 01_database_test.py
```
Tests:
- ✅ Root endpoint connectivity
- ✅ Database connection health
- ✅ Basic server functionality

### 3. Authentication Test
```python
# Paste and run: 02_authentication_test.py
```
Tests:
- ✅ User creation (manual instructions)
- ✅ Authentication flow
- ✅ Protected endpoints

### 4. YouTube Processing Test
```python
# Paste and run: 03_youtube_processing_test.py
```
Tests:
- ✅ YouTube URL processing
- ✅ Task creation and monitoring
- ✅ Clip generation and retrieval
- ✅ Real-time progress tracking

### 5. Comprehensive Endpoint Test
```python
# Paste and run: 04_comprehensive_test.py
```
Tests ALL endpoints:
- ✅ Root endpoint
- ✅ Health check
- ✅ Fonts endpoint
- ✅ Transitions endpoint
- ✅ Task creation (basic)
- ✅ Task creation with progress
- ✅ Task details retrieval
- ✅ Task clips retrieval
- ✅ File upload endpoint

## 📋 Prerequisites

1. **Backend Running**: Your backend must be running in Colab:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

2. **Database Connected**: Your Neon PostgreSQL database should be accessible

3. **User ID**: You need a valid user ID for testing (create one manually or use existing)

## 🔧 Configuration

### Update Test User ID
In each test script, update this line:
```python
TEST_USER_ID = "your-actual-user-id-here"
```

### Update Backend URL
If your backend runs on a different port:
```python
BASE_URL = "http://localhost:8000"  # Change port if needed
```

## 📊 Test Results

Each script provides:
- ✅ **PASS/FAIL** status for each test
- 📊 **Detailed response data**
- 🔍 **Error messages** for debugging
- 📋 **Summary statistics**

## 🐛 Troubleshooting

### Common Issues:

1. **Connection Refused**
   - Make sure backend is running: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
   - Check if port 8000 is accessible

2. **Database Connection Failed**
   - Verify your Neon database URL
   - Check if database is accessible from Colab

3. **Authentication Errors**
   - Create a test user in your database
   - Update `TEST_USER_ID` in scripts

4. **YouTube Processing Fails**
   - Check if yt-dlp is working
   - Verify YouTube URL is accessible
   - Check backend logs for detailed errors

### Debug Tips:

1. **Check Backend Logs**:
   ```bash
   # In Colab terminal where backend is running
   tail -f logs/backend.log
   ```

2. **Test Individual Endpoints**:
   ```python
   import requests
   response = requests.get("http://localhost:8000/")
   print(response.json())
   ```

3. **Verify Database**:
   ```python
   import requests
   response = requests.get("http://localhost:8000/health/db")
   print(response.json())
   ```

## 📝 Manual User Creation

If you need to create a test user manually:

```sql
INSERT INTO users (id, name, email, "emailVerified") 
VALUES ('test-user-123', 'manifesto', 'manifesto.ai23@gmail.com', true);
```

## 🎯 Expected Results

- **Database Test**: Should show connection success
- **Authentication Test**: Should work with valid user ID
- **YouTube Test**: Should create task and process video
- **Comprehensive Test**: Should pass all endpoint tests

## 📞 Support

If tests fail:
1. Check backend logs
2. Verify database connection
3. Ensure all dependencies are installed
4. Test individual endpoints manually

---

**Happy Testing! 🚀**
