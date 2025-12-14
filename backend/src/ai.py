"""
Optimized AI functions for transcript analysis using Ollama.
Streamlined for Google Colab integration with minimal dependencies.
"""
from typing import List, Optional, Dict, Any
import logging
import os
import json
import time
import requests
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Ollama File Logging Setup ---------------------------------------------------
# Write logs inside the project tree by default
OLLAMA_LOG_DIR = "backend/logs"
OLLAMA_LOG_FILE = os.path.join(OLLAMA_LOG_DIR, "ollama_log")

# Initialize file logger for Ollama operations
_ollama_file_logger = None

def _get_ollama_file_logger():
    """Get or create the file logger for Ollama operations."""
    global _ollama_file_logger
    
    if _ollama_file_logger is not None:
        return _ollama_file_logger
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(OLLAMA_LOG_DIR, exist_ok=True)
        
        # Create file logger
        _ollama_file_logger = logging.getLogger("ollama_file_logger")
        _ollama_file_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        _ollama_file_logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(OLLAMA_LOG_FILE, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        _ollama_file_logger.addHandler(file_handler)
        _ollama_file_logger.propagate = False
        
        _ollama_file_logger.info("=" * 80)
        _ollama_file_logger.info("OLLAMA LOGGING INITIALIZED")
        _ollama_file_logger.info(f"Log file: {OLLAMA_LOG_FILE}")
        _ollama_file_logger.info("=" * 80)
        
        return _ollama_file_logger
    except Exception as e:
        logger.error(f"Failed to initialize Ollama file logger: {e}")
        return None

def _log_to_file(message: str, level: str = "INFO"):
    """Log message to Ollama log file and flush immediately."""
    file_logger = _get_ollama_file_logger()
    if file_logger:
        try:
            if level == "DEBUG":
                file_logger.debug(message)
            elif level == "WARNING":
                file_logger.warning(message)
            elif level == "ERROR":
                file_logger.error(message)
            else:
                file_logger.info(message)
            # Force flush all handlers to ensure logs are written immediately
            for handler in file_logger.handlers:
                handler.flush()
        except Exception as e:
            # Don't fail if logging fails
            logger.error(f"Failed to write to log file: {e}")

# --- Domain models ----------------------------------------------------------------
class TranscriptSegment:
    def __init__(self, start_time: str, end_time: str, text: str, relevance_score: float, reasoning: str):
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.relevance_score = relevance_score
        self.reasoning = reasoning
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text,
            "relevance_score": self.relevance_score,
            "reasoning": self.reasoning
        }

class TranscriptAnalysis:
    def __init__(self, most_relevant_segments: List[TranscriptSegment], summary: str, key_topics: List[str]):
        self.most_relevant_segments = most_relevant_segments
        self.summary = summary
        self.key_topics = key_topics

# --- System prompt for Ollama ---------------------------------------------------
 
OLLAMA_SYSTEM_PROMPT = """
You are a viral segment extractor for motivational video transcripts. RETURN ONLY JSON.

MERGE LOGIC:
1. Begin at any transcript line. Merge the next consecutive lines (do not skip lines), creating the longest possible segment that is at least 60 seconds and at most 90 seconds in duration, stopping only at sentence/idea end or natural pause.
2. Each segment must use start_time and end_time ONLY from transcript lines. NO invented timestamps.
3. Segment text is the verbatim concatenation of transcript lines (space between lines), always ending at a sentence/idea boundary.
4. Segments under 30 seconds are FORBIDDEN. If you reach sentence end and still under 30s, KEEP MERGING next lines until >30s.
5. Segments must never cut mid-sentence, must not be a single line, and never under 30s.
6. Select at least 3 segments if possible. If not possible, output empty list with an error explaining why.
7. duration_seconds = end_time (in seconds) - start_time (in seconds).

EXPLICIT EXAMPLES(This logic should be applied to all the elements of most_relevant_segments):
Good:
  start_time: "00:10", end_time: "01:20", duration_seconds: 70,
  text: "Sometimes you need to feel the pain and sting of defeat to activate the real passion and purpose that God predestined inside of you God says in Jeremiah, I know the plans I have for you Plans to prosper you and not to harm you Plans to give you hope in the future Hear me well on this day This day when you have reached the hilltop and you are deciding on next jobs next steps careers for the education"
Bad:
  start_time: "00:10", end_time: "00:15", duration_seconds: 5 (Too short!)
  start_time: "00:29", end_time: "00:32", duration_seconds: 3 (Too short!)
(Segments like these are NOT allowed.)

OUTPUT THIS JSON SCHEMA ONLY:
{{
  "most_relevant_segments": [
    {{
      "start_time": "MM:SS",
      "end_time": "MM:SS",
      "duration_seconds": <integer>,
      "text": "verbatim merged transcript",
      "relevance_score": <float 0.7-1.0>,
      "reasoning": "1-2 sentences why viral"
    }}
    // Repeat for each merged segment, minimum 3 if possible
  ],
  "summary": "Motivational video arc summary.",
  "key_topics": ["Purpose", "Motivation"]
}}
If not possible:
{{
  "most_relevant_segments": [],
  "error": "Transcript too short or fragmented for 3 merged segments"
}}
TRANSCRIPT:
{transcript}

OUTPUT ONLY VALID JSON!
"""

# --- Ollama Configuration --------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "7200"))  # 2 hours default for long transcripts (Ollama can be slow)
OLLAMA_TEST_TIMEOUT = int(os.getenv("OLLAMA_TEST_TIMEOUT", "300"))  # 5 minutes for test requests

def test_ollama_connection() -> bool:
    """Test Ollama connection with a simple 'Hi' request to verify it's working."""
    _log_to_file("=" * 80)
    _log_to_file("STEP: Testing Ollama Connection")
    _log_to_file("=" * 80)
    try:
        logger.info(f"🔍 Testing Ollama connection at {OLLAMA_BASE_URL}...")
        _log_to_file(f"🔍 Testing Ollama connection at {OLLAMA_BASE_URL}...")
        logger.info(f"⏰ Test timeout set to {OLLAMA_TEST_TIMEOUT} seconds ({OLLAMA_TEST_TIMEOUT//60} minutes)")
        _log_to_file(f"⏰ Test timeout set to {OLLAMA_TEST_TIMEOUT} seconds ({OLLAMA_TEST_TIMEOUT//60} minutes)")
        
        # First, test if Ollama is reachable via tags endpoint
        tags_url = f"{OLLAMA_BASE_URL}/api/tags"
        logger.info(f"📡 Checking Ollama availability: {tags_url}")
        _log_to_file(f"📡 Checking Ollama availability: {tags_url}")
        
        try:
            import time as time_module
            tags_start = time_module.time()
            tags_response = requests.get(tags_url, timeout=min(OLLAMA_TEST_TIMEOUT, 60))  # Max 60s for tags
            tags_time = time_module.time() - tags_start
            tags_response.raise_for_status()
            tags_data = tags_response.json()
            models = tags_data.get('models', [])
            model_names = [m.get('name', '') for m in models]
            logger.info(f"✅ Ollama is reachable! Found {len(models)} model(s): {model_names} (took {tags_time:.2f}s)")
            _log_to_file(f"✅ Ollama is reachable! Found {len(models)} model(s): {model_names} (took {tags_time:.2f}s)")
        except Exception as e:
            logger.error(f"❌ Ollama tags endpoint failed: {e}")
            _log_to_file(f"❌ Ollama tags endpoint failed: {e}", "ERROR")
            return False
        
        # Now test with a simple generate request
        logger.info(f"🧪 Sending test 'Hi' request to Ollama with model {OLLAMA_MODEL}...")
        _log_to_file(f"🧪 Sending test 'Hi' request to Ollama with model {OLLAMA_MODEL}...")
        logger.info(f"⏰ This test may take up to {OLLAMA_TEST_TIMEOUT//60} minutes. Please wait...")
        _log_to_file(f"⏰ This test may take up to {OLLAMA_TEST_TIMEOUT//60} minutes. Please wait...")
        test_url = f"{OLLAMA_BASE_URL}/api/generate"
        test_payload = {
            "model": OLLAMA_MODEL,
            "prompt": "Say 'Hi' in one word. Only respond with that word.",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "max_tokens": 5
            }
        }
        
        logger.info(f"📤 Test request URL: {test_url}")
        _log_to_file(f"📤 Test request URL: {test_url}")
        logger.info(f"📤 Test request payload: model={OLLAMA_MODEL}, prompt_length={len(test_payload['prompt'])}")
        _log_to_file(f"📤 Test request payload: model={OLLAMA_MODEL}, prompt_length={len(test_payload['prompt'])}")
        _log_to_file(f"📤 Test prompt: {test_payload['prompt']}")
        _log_to_file(f"📤 Full test payload: {json.dumps(test_payload, indent=2)}")
        
        import time as time_module
        test_start = time_module.time()
        test_response = requests.post(test_url, json=test_payload, timeout=OLLAMA_TEST_TIMEOUT)
        test_time = time_module.time() - test_start
        test_response.raise_for_status()
        
        test_result = test_response.json()
        test_output = test_result.get("response", "").strip()
        
        logger.info(f"✅ Ollama test response received: '{test_output}' (took {test_time:.2f}s)")
        _log_to_file(f"✅ Ollama test response received: '{test_output}' (took {test_time:.2f}s)")
        _log_to_file(f"📥 Full test response: {json.dumps(test_result, indent=2)}")
        if test_time > 60:
            logger.warning(f"⚠️ Ollama is slow (took {test_time:.2f}s for simple test), actual analysis may take 20-30 minutes")
            _log_to_file(f"⚠️ Ollama is slow (took {test_time:.2f}s for simple test), actual analysis may take 20-30 minutes", "WARNING")
        logger.info(f"✅ Ollama connection test successful! Model {OLLAMA_MODEL} is ready for analysis.")
        _log_to_file(f"✅ Ollama connection test successful! Model {OLLAMA_MODEL} is ready for analysis.")
        _log_to_file("=" * 80)
        
        return True
        
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ Ollama connection test timed out after {OLLAMA_TEST_TIMEOUT}s: {e}")
        _log_to_file(f"❌ Ollama connection test timed out after {OLLAMA_TEST_TIMEOUT}s: {e}", "ERROR")
        logger.error(f"   This suggests Ollama may be overloaded or not responding properly.")
        _log_to_file(f"   This suggests Ollama may be overloaded or not responding properly.", "ERROR")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Ollama connection test failed - cannot connect to {OLLAMA_BASE_URL}: {e}")
        _log_to_file(f"❌ Ollama connection test failed - cannot connect to {OLLAMA_BASE_URL}: {e}", "ERROR")
        logger.error(f"   Please ensure Ollama is running and accessible.")
        _log_to_file(f"   Please ensure Ollama is running and accessible.", "ERROR")
        return False
    except Exception as e:
        logger.error(f"❌ Ollama connection test failed: {e}")
        _log_to_file(f"❌ Ollama connection test failed: {e}", "ERROR")
        logger.exception("Full error details:")
        _log_to_file(f"Full error details: {str(e)}", "ERROR")
        return False

def call_ollama(prompt: str, max_retries: int = 3) -> Optional[str]:
    """Call Ollama API directly for transcript analysis with extended retry logic and full timeout wait."""
    _log_to_file("=" * 80)
    _log_to_file("STEP: Calling Ollama API for Transcript Analysis")
    _log_to_file("=" * 80)
    
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 2048
        }
    }
    
    # Log the full prompt being sent
    _log_to_file("📤 FULL PROMPT BEING SENT TO OLLAMA:")
    _log_to_file("-" * 80)
    _log_to_file(prompt)
    _log_to_file("-" * 80)
    _log_to_file(f"Prompt length: {len(prompt)} characters")
    
    # Use a session with extended timeout settings
    session = requests.Session()
    session.timeout = OLLAMA_TIMEOUT
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                wait_time = 5  # Wait 5 minutes between retries
                logger.warning(f"🔄 Retrying Ollama request (attempt {attempt + 1}/{max_retries + 1}) after {wait_time*60}s...")
                _log_to_file(f"🔄 Retrying Ollama request (attempt {attempt + 1}/{max_retries + 1}) after {wait_time*60}s...", "WARNING")
                logger.info(f"⏳ Waiting {wait_time} minutes before retry...")
                _log_to_file(f"⏳ Waiting {wait_time} minutes before retry...")
                time.sleep(wait_time * 60)
            
            logger.info(f"📤 Calling Ollama API (attempt {attempt + 1}/{max_retries + 1})...")
            _log_to_file(f"📤 Calling Ollama API (attempt {attempt + 1}/{max_retries + 1})...")
            logger.info(f"   URL: {url}")
            _log_to_file(f"   URL: {url}")
            logger.info(f"   Model: {OLLAMA_MODEL}")
            _log_to_file(f"   Model: {OLLAMA_MODEL}")
            logger.info(f"   Prompt length: {len(prompt)} characters")
            _log_to_file(f"   Prompt length: {len(prompt)} characters")
            logger.info(f"   Timeout: {OLLAMA_TIMEOUT} seconds ({OLLAMA_TIMEOUT//60} minutes)")
            _log_to_file(f"   Timeout: {OLLAMA_TIMEOUT} seconds ({OLLAMA_TIMEOUT//60} minutes)")
            logger.info(f"   ⏰ This request will wait up to {OLLAMA_TIMEOUT//60} minutes for response...")
            _log_to_file(f"   ⏰ This request will wait up to {OLLAMA_TIMEOUT//60} minutes for response...")
            
            # Log the full payload
            _log_to_file(f"📤 Full request payload:")
            _log_to_file(json.dumps(payload, indent=2))
            
            # Make the actual request - this will block for up to OLLAMA_TIMEOUT seconds
            request_start = time.time()
            _log_to_file(f"⏳ Sending request to Ollama at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
            response = None
            response_text = None
            result = None
            
            try:
                response = session.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
                response.raise_for_status()
                
                request_time = time.time() - request_start
                logger.info(f"✅ Ollama API responded with status {response.status_code} after {request_time:.2f}s ({request_time//60:.1f} minutes)")
                _log_to_file(f"✅ Ollama API responded with status {response.status_code} after {request_time:.2f}s ({request_time//60:.1f} minutes)")
                _log_to_file(f"⏰ Response received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Always try to get the response, even if JSON parsing fails
                try:
                    result = response.json()
                except Exception as json_error:
                    _log_to_file(f"⚠️ Failed to parse response as JSON: {json_error}", "WARNING")
                    _log_to_file(f"Raw response text (first 5000 chars): {response.text[:5000]}", "WARNING")
                    # Try to extract response text from raw response
                    response_text = response.text.strip()
                    result = {"response": response_text}
                
                response_text = result.get("response", "").strip() if result else response.text.strip() if response else ""
                
                # Log the full response - THIS IS CRITICAL
                _log_to_file("📥 FULL RESPONSE FROM OLLAMA:")
                _log_to_file("-" * 80)
                _log_to_file(f"Response length: {len(response_text)} characters")
                _log_to_file(f"Full response text:")
                _log_to_file(response_text)
                _log_to_file("-" * 80)
                
                if result:
                    try:
                        _log_to_file(f"📥 Full response JSON:")
                        _log_to_file(json.dumps(result, indent=2))
                    except Exception as e:
                        _log_to_file(f"⚠️ Could not serialize response JSON: {e}", "WARNING")
                        _log_to_file(f"Response type: {type(result)}")
                
                _log_to_file("-" * 80)
                
                if response_text:
                    logger.info(f"✅ Received response from Ollama ({len(response_text)} characters)")
                    _log_to_file(f"✅ Successfully received response from Ollama ({len(response_text)} characters)")
                    logger.debug(f"Response preview (first 200 chars): {response_text[:200]}")
                    _log_to_file(f"Response preview (first 200 chars): {response_text[:200]}")
                    _log_to_file("=" * 80)
                    return response_text
                else:
                    logger.warning(f"⚠️ Ollama returned empty response")
                    _log_to_file(f"⚠️ Ollama returned empty response", "WARNING")
                    if attempt < max_retries:
                        logger.info(f"🔄 Will retry in 5 minutes...")
                        _log_to_file(f"🔄 Will retry in 5 minutes...")
                        continue
                    return None
                    
            except Exception as response_error:
                # Log response even if there's an error
                if response is not None:
                    try:
                        _log_to_file(f"⚠️ Error occurred but response was received. Status: {response.status_code}", "WARNING")
                        _log_to_file(f"Response text (first 5000 chars): {response.text[:5000]}", "WARNING")
                    except:
                        pass
                # Re-raise to be handled by outer exception handlers
                raise
            
        except requests.exceptions.Timeout as e:
            request_time = time.time() - request_start if 'request_start' in locals() else OLLAMA_TIMEOUT
            logger.error(f"❌ Ollama API call timed out after {OLLAMA_TIMEOUT}s ({OLLAMA_TIMEOUT//60} minutes) - attempt {attempt + 1}/{max_retries + 1}")
            _log_to_file(f"❌ Ollama API call timed out after {OLLAMA_TIMEOUT}s ({OLLAMA_TIMEOUT//60} minutes) - attempt {attempt + 1}/{max_retries + 1}", "ERROR")
            logger.error(f"   This may indicate the model needs more time to process a very long transcript.")
            _log_to_file(f"   This may indicate the model needs more time to process a very long transcript.", "ERROR")
            logger.error(f"   Current timeout is {OLLAMA_TIMEOUT//60} minutes. Retrying...")
            _log_to_file(f"   Current timeout is {OLLAMA_TIMEOUT//60} minutes. Retrying...", "ERROR")
            if attempt < max_retries:
                logger.info(f"🔄 Will retry in 5 minutes...")
                _log_to_file(f"🔄 Will retry in 5 minutes...")
                continue
            logger.error(f"❌ All retries exhausted. Ollama did not respond within {OLLAMA_TIMEOUT//60} minutes.")
            _log_to_file(f"❌ All retries exhausted. Ollama did not respond within {OLLAMA_TIMEOUT//60} minutes.", "ERROR")
            _log_to_file("=" * 80)
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Ollama connection error (attempt {attempt + 1}/{max_retries + 1}): {e}")
            _log_to_file(f"❌ Ollama connection error (attempt {attempt + 1}/{max_retries + 1}): {e}", "ERROR")
            logger.error(f"   Please check if Ollama is running at {OLLAMA_BASE_URL}")
            _log_to_file(f"   Please check if Ollama is running at {OLLAMA_BASE_URL}", "ERROR")
            if attempt < max_retries:
                logger.info(f"🔄 Will retry in 5 minutes...")
                _log_to_file(f"🔄 Will retry in 5 minutes...")
                continue
            _log_to_file("=" * 80)
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Ollama HTTP error (attempt {attempt + 1}/{max_retries + 1}): {e}")
            _log_to_file(f"❌ Ollama HTTP error (attempt {attempt + 1}/{max_retries + 1}): {e}", "ERROR")
            if e.response is not None:
                logger.error(f"   Status code: {e.response.status_code}")
                _log_to_file(f"   Status code: {e.response.status_code}", "ERROR")
                logger.error(f"   Response: {e.response.text[:500]}")
                _log_to_file(f"   Response: {e.response.text[:500]}", "ERROR")
            if attempt < max_retries:
                logger.info(f"🔄 Will retry in 5 minutes...")
                _log_to_file(f"🔄 Will retry in 5 minutes...")
                continue
            _log_to_file("=" * 80)
            return None
        except Exception as e:
            logger.error(f"❌ Ollama API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
            _log_to_file(f"❌ Ollama API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}", "ERROR")
            logger.exception("Full error details:")
            _log_to_file(f"Full error details: {str(e)}", "ERROR")
            if attempt < max_retries:
                logger.info(f"🔄 Will retry in 5 minutes...")
                _log_to_file(f"🔄 Will retry in 5 minutes...")
                continue
            _log_to_file("=" * 80)
            return None
    
    logger.error(f"❌ All {max_retries + 1} attempts to call Ollama failed")
    _log_to_file(f"❌ All {max_retries + 1} attempts to call Ollama failed", "ERROR")
    _log_to_file("=" * 80)
    return None

# --- Constants and Helpers ------------------------------------------------------
MIN_SEGMENT_DURATION = 30  # 30 seconds minimum for viral clips
MAX_SEGMENT_DURATION = 60  # 60 seconds maximum (1 minute)
MIN_SEGMENTS = 3
MAX_SEGMENTS = 5  # Reduced to 5 for faster processing

def extract_json_from_text(text: str) -> Optional[dict]:
    """Extract JSON object from Ollama response."""
    _log_to_file("🔍 Extracting JSON from text...")
    _log_to_file(f"Input text length: {len(text) if text else 0} characters")
    
    if not text:
        _log_to_file("❌ No text provided for JSON extraction", "ERROR")
        return None
    
    # Log first 1000 characters for debugging
    _log_to_file(f"First 1000 characters of response: {text[:1000]}")
    
    # Try direct JSON parse first
    try:
        result = json.loads(text.strip())
        _log_to_file("✅ Successfully parsed JSON directly")
        _log_to_file(f"Parsed JSON keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        if isinstance(result, dict) and "most_relevant_segments" in result:
            segments_count = len(result.get("most_relevant_segments", []))
            _log_to_file(f"Found {segments_count} segments in JSON")
        return result
    except json.JSONDecodeError as e:
        _log_to_file(f"Direct JSON parse failed: {str(e)} at position {e.pos}", "WARNING")
        _log_to_file(f"Error context: {text[max(0, e.pos-50):e.pos+50]}", "WARNING")
    except Exception as e:
        _log_to_file(f"Direct JSON parse failed with unexpected error: {str(e)}", "WARNING")
    
    # Look for JSON object in text - try to find markdown code blocks first
    _log_to_file("Trying to extract JSON from markdown code blocks or plain text...")
    
    # Try to find markdown code blocks (```json ... ```)
    json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    matches = re.findall(json_block_pattern, text, re.DOTALL)
    if matches:
        _log_to_file(f"Found {len(matches)} potential JSON code blocks in markdown")
        for i, match in enumerate(matches):
            try:
                result = json.loads(match.strip())
                _log_to_file(f"✅ Successfully extracted JSON from code block {i+1}")
                return result
            except Exception as e:
                _log_to_file(f"Failed to parse code block {i+1}: {str(e)}")
    
    # Look for JSON object in text
    start = text.find('{')
    if start == -1:
        _log_to_file("❌ No opening brace found in text", "ERROR")
        _log_to_file(f"Full response text for debugging:\n{text}", "ERROR")
        return None
    
    _log_to_file(f"Found opening brace at position {start}")
    depth = 0
    end_positions = []
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end_positions.append(i)
                try:
                    json_str = text[start:i+1]
                    result = json.loads(json_str)
                    _log_to_file(f"✅ Successfully extracted JSON object (length: {i+1-start} characters)")
                    _log_to_file(f"Parsed JSON keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    if isinstance(result, dict) and "most_relevant_segments" in result:
                        segments_count = len(result.get("most_relevant_segments", []))
                        _log_to_file(f"Found {segments_count} segments in extracted JSON")
                    return result
                except Exception as e:
                    _log_to_file(f"Failed to parse JSON at position {start}-{i+1}: {str(e)}")
                    continue
    
    _log_to_file(f"❌ Failed to extract valid JSON object. Found {len(end_positions)} potential end positions", "ERROR")
    _log_to_file(f"Full response text for debugging:\n{text}", "ERROR")
    return None

def parse_timestamp_to_seconds(ts: str) -> int:
    """Parse timestamp string to seconds."""
    if not isinstance(ts, str):
        raise ValueError("Timestamp must be a string")
    ts = ts.strip()
    parts = ts.split(':')
    if len(parts) == 2:
        minutes, seconds = parts
        hours = 0
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Invalid timestamp format: {ts}")
    try:
        hours_i = int(hours)
        minutes_i = int(minutes)
        seconds_i = int(seconds.split('.')[0]) if '.' in seconds else int(seconds)
    except Exception as e:
        raise ValueError(f"Invalid timestamp components: {e}")
    if seconds_i < 0 or minutes_i < 0 or hours_i < 0:
        raise ValueError("Negative timestamp not allowed")
    return hours_i * 3600 + minutes_i * 60 + seconds_i

def _parse_transcript_lines(transcript: str) -> List[Dict[str, Any]]:
    """Parse transcript lines of the form [MM:SS - MM:SS] text into structured entries."""
    entries: List[Dict[str, Any]] = []
    pattern = re.compile(r"\[(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\]\s*(.*)")
    for line in transcript.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        start, end, text = match.groups()
        try:
            start_s = parse_timestamp_to_seconds(start)
            end_s = parse_timestamp_to_seconds(end)
            if end_s <= start_s:
                continue
            entries.append({
                "start_time": start,
                "end_time": end,
                "start_s": start_s,
                "end_s": end_s,
                "text": text or ""
            })
        except Exception:
            continue
    return entries

def _expand_segments_with_transcript(transcript: str, segments_data: List[dict]) -> List[dict]:
    """Expand too-short segments by concatenating subsequent transcript lines until 10–45s.
    Keeps original start_time, grows end_time and text. Skips if cannot reach 10s.
    """
    _log_to_file("🔧 Fallback: Expanding too-short segments using transcript lines...")
    entries = _parse_transcript_lines(transcript)
    if not entries:
        _log_to_file("⚠️ Fallback aborted: transcript lines could not be parsed", "WARNING")
        return []
    expanded: List[dict] = []
    for idx, seg in enumerate(segments_data, 1):
        try:
            seg_start = seg.get("start_time", "").strip()
            seg_end = seg.get("end_time", "").strip()
            base_text = seg.get("text", "")
            score = float(seg.get("relevance_score", 0.8))
            reasoning = seg.get("reasoning", "Engaging segment")
            start_s = parse_timestamp_to_seconds(seg_start)
            end_s = parse_timestamp_to_seconds(seg_end)
        except Exception:
            continue

        # Find the first transcript entry at or after seg_start
        start_idx = None
        for i, e in enumerate(entries):
            if e["start_s"] >= start_s - 1:  # allow slight drift
                start_idx = i
                break
        if start_idx is None:
            continue

        # Expand forward until duration within bounds
        combined_texts: List[str] = []
        new_start_s = entries[start_idx]["start_s"]
        new_end_s = entries[start_idx]["end_s"]
        combined_texts.append(entries[start_idx]["text"])
        j = start_idx + 1
        while (new_end_s - new_start_s) < MIN_SEGMENT_DURATION and j < len(entries):
            # Append next line
            combined_texts.append(entries[j]["text"])
            new_end_s = entries[j]["end_s"]
            if (new_end_s - new_start_s) > MAX_SEGMENT_DURATION:
                break
            j += 1

        new_duration = new_end_s - new_start_s
        if new_duration < MIN_SEGMENT_DURATION or new_duration > (MAX_SEGMENT_DURATION + 2):
            # Could not expand to valid duration
            _log_to_file(f"  Fallback segment {idx}: unable to reach valid duration ({new_duration}s)")
            continue

        # Build expanded segment
        expanded_seg = {
            "start_time": f"{new_start_s//60:02d}:{new_start_s%60:02d}",
            "end_time": f"{new_end_s//60:02d}:{new_end_s%60:02d}",
            "text": (base_text + " " + " ".join(combined_texts)).strip(),
            "relevance_score": score,
            "reasoning": reasoning
        }
        _log_to_file(f"  Fallback segment {idx}: expanded to {expanded_seg['start_time']}-{expanded_seg['end_time']} ({new_duration}s)")
        expanded.append(expanded_seg)

    _log_to_file(f"🔧 Fallback produced {len(expanded)} expanded segments")
    return expanded

def validate_segments(segments_data: List[dict]) -> List[TranscriptSegment]:
    """Validate and create TranscriptSegment objects."""
    _log_to_file(f"🔍 Validating {len(segments_data)} segments...")
    validated_segments = []
    
    for idx, seg_data in enumerate(segments_data, 1):
        if not isinstance(seg_data, dict):
            _log_to_file(f"  Segment {idx}: Skipping (not a dict)")
            continue
            
        try:
            # Extract segment data
            start_time = seg_data.get("start_time", "")
            end_time = seg_data.get("end_time", "")
            text = seg_data.get("text", "")
            relevance_score = float(seg_data.get("relevance_score", 0.8))
            reasoning = seg_data.get("reasoning", "Engaging segment")
            
            _log_to_file(f"  Segment {idx}: Validating {start_time}-{end_time} (score: {relevance_score})")
            
            # Basic validation
            if not text or len(text.split()) < 3:
                _log_to_file(f"  Segment {idx}: Skipping (text too short)")
                continue
                
            # Validate timestamps and duration
            start_sec = parse_timestamp_to_seconds(start_time)
            end_sec = parse_timestamp_to_seconds(end_time)
            duration = end_sec - start_sec
            
            if duration < MIN_SEGMENT_DURATION or duration > MAX_SEGMENT_DURATION:
                _log_to_file(f"  Segment {idx}: Skipping (duration {duration}s out of range {MIN_SEGMENT_DURATION}-{MAX_SEGMENT_DURATION}s)")
                continue
                
            if not (0.0 <= relevance_score <= 1.0):
                _log_to_file(f"  Segment {idx}: Skipping (invalid score: {relevance_score})")
                continue
                
            segment = TranscriptSegment(
                start_time=start_time,
                end_time=end_time,
                text=text,
                relevance_score=relevance_score,
                reasoning=reasoning
            )
            validated_segments.append(segment)
            logger.info(f"✓ Valid segment: {start_time}-{end_time} ({duration}s) score={relevance_score:.2f}")
            _log_to_file(f"  Segment {idx}: ✓ Valid ({start_time}-{end_time}, {duration}s, score={relevance_score:.2f})")
                           
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid segment: {e}")
            _log_to_file(f"  Segment {idx}: Skipping invalid segment: {str(e)}", "WARNING")
            continue
    
    _log_to_file(f"✅ Validated {len(validated_segments)}/{len(segments_data)} segments")
    return validated_segments

def validate_and_fix_json_data(json_data: dict) -> TranscriptAnalysis:
    """Validate and fix JSON data from Ollama response."""
    _log_to_file("🔍 Validating and fixing JSON data...")
    _log_to_file(f"JSON data type: {type(json_data)}")
    _log_to_file(f"JSON data keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
    
    try:
        # Extract segments
        segments_data = json_data.get("most_relevant_segments", [])
        _log_to_file(f"Raw segments_data type: {type(segments_data)}")
        _log_to_file(f"Raw segments_data length: {len(segments_data) if isinstance(segments_data, list) else 'N/A'}")
        
        # Check for alternative key names
        if not segments_data or len(segments_data) == 0:
            _log_to_file("⚠️ No segments found in 'most_relevant_segments', checking alternative keys...", "WARNING")
            for alt_key in ["segments", "clips", "relevant_segments", "top_segments"]:
                if alt_key in json_data:
                    _log_to_file(f"Found alternative key: {alt_key} with {len(json_data[alt_key])} items")
                    segments_data = json_data[alt_key]
                    break
        
        if not isinstance(segments_data, list):
            _log_to_file(f"⚠️ segments_data is not a list, it's {type(segments_data)}. Converting to empty list.", "WARNING")
            if isinstance(segments_data, dict):
                _log_to_file(f"Segments data dict keys: {list(segments_data.keys())}")
            segments_data = []
        
        _log_to_file(f"Final segments_data: {len(segments_data)} items")
        if len(segments_data) > 0:
            _log_to_file(f"First segment sample: {segments_data[0] if isinstance(segments_data[0], dict) else 'Not a dict'}")
        
        # Validate segments
        validated_segments = validate_segments(segments_data)
        
        _log_to_file(f"After validation: {len(validated_segments)} valid segments")
        
        # Extract summary and topics
        summary = json_data.get("summary", "Video analysis completed")
        key_topics = json_data.get("key_topics", [])
        
        if not isinstance(key_topics, list):
            key_topics = []
        
        _log_to_file(f"Summary: {summary[:200]}...")
        _log_to_file(f"Key topics: {key_topics}")
        
        result = TranscriptAnalysis(
            most_relevant_segments=validated_segments,
            summary=summary,
            key_topics=key_topics
        )
        
        _log_to_file(f"✅ Created TranscriptAnalysis with {len(validated_segments)} segments")
        return result
        
    except Exception as e:
        logger.error(f"Error validating JSON data: {e}")
        _log_to_file(f"❌ Error validating JSON data: {str(e)}", "ERROR")
        import traceback
        _log_to_file(f"Traceback: {traceback.format_exc()}", "ERROR")
        return TranscriptAnalysis(
            most_relevant_segments=[],
            summary="Analysis failed",
            key_topics=[]
        )

# --- Main processing function ------------------------------------------------------
def get_most_relevant_parts_by_transcript(transcript: str) -> TranscriptAnalysis:
    """Get the most relevant parts of a transcript for creating clips using Ollama."""
    _log_to_file("=" * 80)
    _log_to_file("STARTING NEW TRANSCRIPT ANALYSIS")
    _log_to_file("=" * 80)
    _log_to_file(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not transcript or not transcript.strip():
        logger.error("Empty transcript provided")
        _log_to_file("Empty transcript provided", "ERROR")
        return TranscriptAnalysis(
            most_relevant_segments=[],
            summary="No transcript provided",
            key_topics=[]
        )

    logger.info("Starting AI analysis of transcript (%d chars)", len(transcript))
    _log_to_file(f"Starting AI analysis of transcript ({len(transcript)} characters)")
    _log_to_file(f"Transcript preview (first 500 chars): {transcript[:500]}")
    
    # Step 1: Test Ollama connection first
    logger.info("🔍 Step 1: Testing Ollama connection before analysis...")
    _log_to_file("🔍 Step 1: Testing Ollama connection before analysis...")
    if not test_ollama_connection():
        logger.error("❌ Ollama connection test failed. Aborting transcript analysis.")
        _log_to_file("❌ Ollama connection test failed. Aborting transcript analysis.", "ERROR")
        return TranscriptAnalysis(
            most_relevant_segments=[],
            summary="Analysis failed: Ollama connection test failed",
            key_topics=[]
        )
    
    # Step 2: Format the prompt with the transcript
    logger.info("📝 Step 2: Formatting prompt with transcript...")
    _log_to_file("📝 Step 2: Formatting prompt with transcript...")
    formatted_prompt = OLLAMA_SYSTEM_PROMPT.format(transcript=transcript)
    logger.info(f"   Formatted prompt length: {len(formatted_prompt)} characters")
    _log_to_file(f"   Formatted prompt length: {len(formatted_prompt)} characters")
    
    try:
        # Step 3: Call Ollama API for actual analysis
        logger.info("🚀 Step 3: Calling Ollama API for transcript analysis...")
        _log_to_file("🚀 Step 3: Calling Ollama API for transcript analysis...")
        logger.info(f"⏰ Analysis timeout set to {OLLAMA_TIMEOUT} seconds ({OLLAMA_TIMEOUT//60} minutes)")
        _log_to_file(f"⏰ Analysis timeout set to {OLLAMA_TIMEOUT} seconds ({OLLAMA_TIMEOUT//60} minutes)")
        logger.info(f"⏰ This analysis may take 20-30 minutes. Please be patient and do not interrupt...")
        _log_to_file(f"⏰ This analysis may take 20-30 minutes. Please be patient and do not interrupt...")
        
        analysis_start = time.time()
        raw_text = call_ollama(formatted_prompt)
        analysis_time = time.time() - analysis_start
        
        if not raw_text:
            raise ValueError("No response from Ollama after connection test succeeded")
        
        logger.info(f"✅ Received response from Ollama ({len(raw_text)} characters) in {analysis_time:.2f}s ({analysis_time//60:.1f} minutes)")
        _log_to_file(f"✅ Received response from Ollama ({len(raw_text)} characters) in {analysis_time:.2f}s ({analysis_time//60:.1f} minutes)")
        logger.debug("Raw model response preview (first 500 chars): %s", raw_text[:500])
        _log_to_file(f"Raw model response preview (first 500 chars): {raw_text[:500]}")
        
        # Step 4: Extract JSON from response
        logger.info("📋 Step 4: Extracting JSON from response...")
        _log_to_file("📋 Step 4: Extracting JSON from response...")
        json_data = extract_json_from_text(raw_text)
        if not json_data:
            logger.error("❌ Failed to extract valid JSON from response")
            _log_to_file("❌ Failed to extract valid JSON from response", "ERROR")
            logger.debug(f"Response text: {raw_text[:1000]}")
            _log_to_file(f"Response text (first 1000 chars): {raw_text[:1000]}", "ERROR")
            _log_to_file(f"Full response text for debugging:\n{raw_text}", "ERROR")
            raise ValueError("No valid JSON found in model response")
        
        logger.info("✅ Successfully extracted JSON from response")
        _log_to_file("✅ Successfully extracted JSON from response")
        _log_to_file(f"📋 Extracted JSON data:")
        try:
            _log_to_file(json.dumps(json_data, indent=2))
        except Exception as e:
            _log_to_file(f"Could not serialize JSON: {e}", "WARNING")
            _log_to_file(f"JSON type: {type(json_data)}, keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'N/A'}")
        
        # Check if segments exist in the JSON
        if isinstance(json_data, dict):
            segments_in_json = json_data.get("most_relevant_segments", [])
            _log_to_file(f"📊 Found {len(segments_in_json)} segments in extracted JSON")
            if len(segments_in_json) == 0:
                _log_to_file("⚠️ WARNING: JSON has 0 segments in most_relevant_segments array!", "WARNING")
                _log_to_file(f"JSON keys: {list(json_data.keys())}", "WARNING")
                _log_to_file(f"Summary from JSON: {json_data.get('summary', 'N/A')}", "WARNING")
        
        # Step 5: Validate and convert to TranscriptAnalysis
        logger.info("✅ Step 5: Validating and processing segments...")
        _log_to_file("✅ Step 5: Validating and processing segments...")
        analysis = validate_and_fix_json_data(json_data)
        
        logger.info("AI analysis returned %d candidate segments", len(analysis.most_relevant_segments))
        _log_to_file(f"AI analysis returned {len(analysis.most_relevant_segments)} candidate segments")
        
        # Sort by score and limit
        analysis.most_relevant_segments.sort(key=lambda s: s.relevance_score, reverse=True)
        analysis.most_relevant_segments = analysis.most_relevant_segments[:MAX_SEGMENTS]
        
        if len(analysis.most_relevant_segments) < MIN_SEGMENTS:
            logger.warning("Only found %d valid segments (wanted %d)", len(analysis.most_relevant_segments), MIN_SEGMENTS)
            _log_to_file(f"Only found {len(analysis.most_relevant_segments)} valid segments (wanted {MIN_SEGMENTS})", "WARNING")
            # Fallback: try to expand too-short segments using transcript
            try:
                original_segments = json_data.get("most_relevant_segments", []) if isinstance(json_data, dict) else []
                _log_to_file("🔧 Attempting fallback expansion using transcript...")
                expanded_segments = _expand_segments_with_transcript(transcript, original_segments)
                # Re-validate expanded segments
                revalidated = validate_segments(expanded_segments)
                _log_to_file(f"🔧 Fallback re-validation produced {len(revalidated)} valid segments")
                # Merge with existing (avoid duplicates by time window)
                existing_keys = {(s.start_time, s.end_time) for s in analysis.most_relevant_segments}
                for s in revalidated:
                    key = (s.start_time, s.end_time)
                    if key not in existing_keys:
                        analysis.most_relevant_segments.append(s)
                        existing_keys.add(key)
                # Resort and trim
                analysis.most_relevant_segments.sort(key=lambda s: s.relevance_score, reverse=True)
                analysis.most_relevant_segments = analysis.most_relevant_segments[:MAX_SEGMENTS]
                _log_to_file(f"🔧 After fallback, have {len(analysis.most_relevant_segments)} segments")
            except Exception as e:
                _log_to_file(f"Fallback expansion failed: {e}", "ERROR")
        
        logger.info("✅ Selected %d segments for processing", len(analysis.most_relevant_segments))
        _log_to_file(f"✅ Selected {len(analysis.most_relevant_segments)} segments for processing")
        
        # Log final analysis result
        _log_to_file("=" * 80)
        _log_to_file("FINAL ANALYSIS RESULT:")
        _log_to_file("-" * 80)
        _log_to_file(f"Summary: {analysis.summary}")
        _log_to_file(f"Key Topics: {analysis.key_topics}")
        _log_to_file(f"Number of segments: {len(analysis.most_relevant_segments)}")
        for i, segment in enumerate(analysis.most_relevant_segments, 1):
            _log_to_file(f"Segment {i}:")
            _log_to_file(f"  Start: {segment.start_time}, End: {segment.end_time}")
            _log_to_file(f"  Score: {segment.relevance_score}")
            _log_to_file(f"  Reasoning: {segment.reasoning}")
            _log_to_file(f"  Text: {segment.text[:200]}...")
        _log_to_file("-" * 80)
        _log_to_file(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _log_to_file("=" * 80)
        
        return analysis
        
    except Exception as exc:
        logger.exception("Error in transcript analysis: %s", exc)
        _log_to_file(f"❌ Error in transcript analysis: {str(exc)}", "ERROR")
        _log_to_file(f"Analysis failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "ERROR")
        _log_to_file("=" * 80)
        return TranscriptAnalysis(
            most_relevant_segments=[],
            summary=f"Analysis failed: {str(exc)}",
            key_topics=[]
        )
