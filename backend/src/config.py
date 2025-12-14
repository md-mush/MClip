from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class Config:
    def __init__(self):
        # Core video processing settings
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.max_video_duration = int(os.getenv("MAX_VIDEO_DURATION", "3600"))
        self.output_dir = os.getenv("OUTPUT_DIR", "outputs")
        self.max_clips = int(os.getenv("MAX_CLIPS", "10"))
        self.clip_duration = int(os.getenv("CLIP_DURATION", "30"))
        self.temp_dir = os.getenv("TEMP_DIR", "temp")
        
        # Ollama configuration (for AI analysis)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q6_K")
        
        logger.info(f"✅ Config loaded - Whisper: {self.whisper_model}, Ollama: {self.ollama_model}")