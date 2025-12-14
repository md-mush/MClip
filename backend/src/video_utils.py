"""
Utility functions for video-related operations.
Robust for MoviePy v2 (>=2.2.1). Uses lazy imports and
diagnostic checks so the app doesn't hard-fail at import-time
when system packages are missing.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import os
import logging
import numpy as np
import json
import tempfile
import shutil
import subprocess
import math

logger = logging.getLogger(__name__)

# Local config import (keep as you had)
from .config import Config
config = Config()

# ---------------------------------------------------------------------------
# Lazy availability flags and helpers
# ---------------------------------------------------------------------------
_MOVIEPY_AVAILABLE = None
_WHISPER_AVAILABLE = None
_IMAGEMAGICK_AVAILABLE = None

# ---------------------------------------------------------------------------
# Helper: safe gaussian blur using OpenCV (works with moviepy 1.0.x)
# ---------------------------------------------------------------------------
def apply_gaussian_blur(clip, ksize: int = 35):
    """
    Apply gaussian blur to a moviepy clip using OpenCV.
    Falls back to returning the original clip if OpenCV is unavailable.
    """
    try:
        import cv2
    except Exception:
        logger.warning("OpenCV not available; skipping blur effect")
        return clip

    # ksize must be odd and >=3 for GaussianBlur
    k = max(3, int(ksize) | 1)
    return clip.fl_image(lambda frame: cv2.GaussianBlur(frame, (k, k), 0))

def _check_executable_in_path(name: str) -> Optional[str]:
    """Return path if executable exists on PATH, else None."""
    path = shutil.which(name)
    return path

def _check_imagemagick_availability():
    """Check if ImageMagick is available and working with MoviePy."""
    global _IMAGEMAGICK_AVAILABLE
    if _IMAGEMAGICK_AVAILABLE is not None:
        return _IMAGEMAGICK_AVAILABLE
    
    # First check if convert command is available
    convert_path = _check_executable_in_path("convert")
    if not convert_path:
        logger.warning("ImageMagick 'convert' command not found on PATH")
        _IMAGEMAGICK_AVAILABLE = False
        return False
    
    # Test basic ImageMagick functionality
    try:
        result = subprocess.run(
            ["convert", "-version"],  # FIX: Use list instead of shell string
            capture_output=True, 
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning("ImageMagick version check failed")
            _IMAGEMAGICK_AVAILABLE = False
            return False
    except Exception as e:
        logger.warning(f"ImageMagick version check error: {e}")
        _IMAGEMAGICK_AVAILABLE = False
        return False
    
    # Test MoviePy TextClip with ImageMagick
    try:
        VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips = _import_moviepy()
        # Simple test without complex parameters
        test_clip = TextClip(txt="test", fontsize=20, color='white')
        test_clip.close()
        _IMAGEMAGICK_AVAILABLE = True
        logger.debug("ImageMagick TextClip functionality confirmed")
        return True
    except Exception as e:
        logger.warning(f"ImageMagick TextClip test failed: {e}")
        _IMAGEMAGICK_AVAILABLE = False
        return False

def _warn_missing_system_deps():
    """Log warnings about ffmpeg / ImageMagick presence (helpful diagnostics)."""
    ffmpeg_path = _check_executable_in_path("ffmpeg")
    magick_path = _check_executable_in_path("convert")  # Using convert for ImageMagick 6

    if not ffmpeg_path:
        logger.warning(
            "ffmpeg not found on PATH. MoviePy needs ffmpeg to read/write videos. "
            "Install system ffmpeg (e.g. apt-get install -y ffmpeg) and ensure it is on PATH."
        )
    else:
        logger.debug("ffmpeg found: %s", ffmpeg_path)

    if not magick_path:
        logger.warning(
            "ImageMagick (convert) not found on PATH. MoviePy TextClip often requires ImageMagick "
            "or a working Pillow configuration to render text."
        )
    else:
        logger.debug("ImageMagick found: %s", magick_path)
        # Test if ImageMagick works with basic command
        try:
            result = subprocess.run(["convert", "-version"], capture_output=True, text=True)  # FIX: Use list
            if result.returncode == 0:
                logger.debug("ImageMagick basic functionality confirmed")
        except Exception as e:
            logger.warning("ImageMagick basic test failed: %s", e)

def _import_moviepy():
    """Try to import moviepy editor API. Return module or raise with helpful message."""
    global _MOVIEPY_AVAILABLE
    if _MOVIEPY_AVAILABLE is not None:
        if _MOVIEPY_AVAILABLE:
            # import lazily again to return actual classes
            from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
            return VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
        raise RuntimeError("MoviePy marked unavailable")

    try:
        # Try canonical v2 import
        from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
        _MOVIEPY_AVAILABLE = True
        
        # Check ImageMagick availability after MoviePy import
        _check_imagemagick_availability()
        
        return VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
    except Exception as e:
        _MOVIEPY_AVAILABLE = False
        _warn_missing_system_deps()
        logger.exception("moviepy.editor import failed: %s", e)
        raise RuntimeError(
            "moviepy (moviepy.editor) import failed. Ensure moviepy is installed and system "
            "dependencies (ffmpeg, ImageMagick) are available. See logs for the original exception."
        ) from e

def _import_whisper():
    """Try to import whisper (lazy)."""
    global _WHISPER_AVAILABLE
    if _WHISPER_AVAILABLE is not None:
        if _WHISPER_AVAILABLE:
            import whisper
            return whisper
        raise RuntimeError("whisper marked unavailable")

    try:
        import whisper
        _WHISPER_AVAILABLE = True
        return whisper
    except Exception as e:
        _WHISPER_AVAILABLE = False
        logger.exception("whisper import failed: %s", e)
        raise RuntimeError("openai-whisper import failed. Ensure the package is installed.") from e

# ---------------------------------------------------------------------------
# VideoProcessor and model caching
# ---------------------------------------------------------------------------
class VideoProcessor:
    """Handles video processing operations with optimized settings."""

    def __init__(self, font_family: str = "DejaVu-Sans", font_size: int = 24, font_color: str = "#FFFFFF"):
        # Use available fonts - DejaVu is installed and works with ImageMagick
        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color
        
        # Check for font file availability
        self.font_path = str(Path(__file__).parent.parent / "fonts" / f"{font_family}.ttf")
        if not Path(self.font_path).exists():
            # Fallback to system fonts that work with ImageMagick
            logger.info(f"Font file {self.font_path} not found, using system font: {font_family}")
            self.font_path = font_family

    def get_optimal_encoding_settings(self, target_quality: str = "high") -> Dict[str, Any]:
        settings = {
            "high": {
                "codec": "libx264",
                "audio_codec": "aac",
                "bitrate": "8000k",
                "audio_bitrate": "256k",
                "preset": "medium",
                "ffmpeg_params": ["-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "main", "-level", "4.1"]
            },
            "medium": {
                "codec": "libx264",
                "audio_codec": "aac",
                "bitrate": "4000k",
                "audio_bitrate": "192k",
                "preset": "fast",
                "ffmpeg_params": ["-crf", "23", "-pix_fmt", "yuv420p"]
            }
        }
        return settings.get(target_quality, settings["high"])

_whisper_model_cache = None

def get_video_transcript(video_path: Path) -> str:
    """Get transcript using Whisper model; model loading is cached and lazy."""
    # Ensure Path object even if caller passed str
    video_path = Path(video_path)
    whisper_mod = _import_whisper()
    global _whisper_model_cache

    logger.info("Getting transcript for: %s", video_path)
    try:
        if _whisper_model_cache is None:
            logger.info("Loading Whisper model: %s", getattr(config, "whisper_model", None))
            _whisper_model_cache = whisper_mod.load_model(getattr(config, "whisper_model", "base"))
        model = _whisper_model_cache

        result = model.transcribe(
            str(video_path),
            verbose=False,
            word_timestamps=True,
            fp16=False,
            task="transcribe"
        )

        formatted_lines: List[str] = []
        if result.get("segments"):
            logger.info("Processing %d segments", len(result["segments"]))
            for segment in result["segments"]:
                if segment.get("words"):
                    current_segment = []
                    current_start = None
                    segment_word_count = 0
                    max_words_per_segment = 8
                    for word in segment["words"]:
                        w_text = (word.get("word") or "").strip()
                        w_start = word.get("start")
                        w_end = word.get("end")
                        if not w_text or w_start is None or w_end is None:
                            logger.debug("Skipping incomplete word: %s", word)
                            continue
                        if current_start is None:
                            current_start = w_start
                        current_segment.append(w_text)
                        segment_word_count += 1
                        if (segment_word_count >= max_words_per_segment or
                            w_text.endswith('.') or w_text.endswith('!') or w_text.endswith('?')):
                            if current_segment and current_start is not None:
                                start_time = format_timestamp(current_start)
                                end_time = format_timestamp(w_end)
                                text = ' '.join(current_segment)
                                formatted_lines.append(f"[{start_time} - {end_time}] {text}")
                            current_segment = []
                            current_start = None
                            segment_word_count = 0
                    if current_segment and current_start is not None:
                        last_valid_end = None
                        for w in reversed(segment["words"]):
                            if w.get("end") is not None:
                                last_valid_end = w.get("end")
                                break
                        if last_valid_end is not None:
                            start_time = format_timestamp(current_start)
                            end_time = format_timestamp(last_valid_end)
                            text = ' '.join(current_segment)
                            formatted_lines.append(f"[{start_time} - {end_time}] {text}")
                        else:
                            logger.warning("Skipping segment with no valid end time")
                else:
                    seg_start = segment.get("start")
                    seg_end = segment.get("end")
                    seg_text = (segment.get("text") or "").strip()
                    if seg_start is not None and seg_end is not None and seg_text:
                        start_time = format_timestamp(seg_start)
                        end_time = format_timestamp(seg_end)
                        formatted_lines.append(f"[{start_time} - {end_time}] {seg_text}")
                    else:
                        logger.warning("Skipping segment with missing data: %s", segment)

        cache_transcript_data(video_path, result)
        result_text = '\n'.join(formatted_lines)
        
        logger.info("Transcript generated successfully")
        logger.info("📝 TRANSCRIPT CONTENT:")
        logger.info("=" * 80)
        logger.info(result_text)
        logger.info("=" * 80)
        logger.info(f"📊 Transcript stats: {len(formatted_lines)} segments, {len(result_text)} characters")
        
        return result_text

    except Exception as e:
        logger.exception("Error in Whisper transcription for %s: %s", video_path, e)
        raise

def cache_transcript_data(video_path: Path, transcript_data: dict) -> None:
    video_path = Path(video_path)
    cache_path = video_path.with_suffix('.transcript_cache.json')
    words_data = []
    if transcript_data.get("segments"):
        for segment in transcript_data["segments"]:
            if segment.get("words"):
                for word in segment["words"]:
                    words_data.append({
                        'text': (word.get("word") or "").strip(),
                        'start': int((word.get("start") or 0) * 1000),
                        'end': int((word.get("end") or 0) * 1000),
                        'confidence': word.get("probability", word.get("confidence", 1.0))
                    })
    cache_data = {
        'words': words_data,
        'text': transcript_data.get("text", ""),
        'segments': transcript_data.get("segments", []),
        'language': transcript_data.get("language", "")
    }
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        logger.info("Cached %d words to %s", len(words_data), cache_path)
    except Exception as e:
        logger.warning("Failed to write transcript cache to %s: %s", cache_path, e)

def load_cached_transcript_data(video_path: Path) -> Optional[Dict]:
    video_path = Path(video_path)
    cache_path = video_path.with_suffix('.transcript_cache.json')
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
        cached_data['_source'] = 'whisper'
        return cached_data
    except Exception as e:
        logger.warning("Failed to load transcript cache %s: %s", cache_path, e)
        return None

# Timestamp helpers
def format_timestamp(seconds: float) -> str:
    if seconds is None:
        return "00:00"
    minutes = int(seconds // 60)
    seconds_i = int(seconds % 60)
    return f"{minutes:02d}:{seconds_i:02d}"

def parse_timestamp_to_seconds(timestamp_str: str) -> float:
    if timestamp_str is None:
        raise ValueError("timestamp_str is None")
    ts = str(timestamp_str).strip()
    try:
        if ':' in ts:
            parts = ts.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours = int(parts[0]); minutes = int(parts[1]); seconds = int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            else:
                raise ValueError(f"Unsupported timestamp format: {ts}")
        return float(ts)
    except Exception as e:
        logger.debug("Failed to parse timestamp '%s': %s", ts, e)
        raise

def round_to_even(value: int) -> int:
    return value - (value % 2)

# Face detection & cropping: keep implementations similar but lazy-import MediaPipe inside function
def detect_optimal_square_crop_region(video_clip, start_time: float, end_time: float) -> Tuple[int, int, int, int]:
    """Detect optimal crop region for a square (1:1) aspect ratio, centered on faces."""
    try:
        original_width, original_height = video_clip.size
        # For square crop, use the smaller dimension
        crop_size = min(original_width, original_height)
        new_width = round_to_even(crop_size)
        new_height = round_to_even(crop_size)

        face_centers = detect_faces_in_clip(video_clip, start_time, end_time)

        if face_centers:
            total_weight = sum(area * confidence for _, _, area, confidence in face_centers)
            if total_weight > 0:
                weighted_x = sum(x * area * confidence for x, y, area, confidence in face_centers) / total_weight
                weighted_y = sum(y * area * confidence for x, y, area, confidence in face_centers) / total_weight
                x_offset = max(0, min(int(weighted_x - new_width // 2), original_width - new_width))
                y_offset = max(0, min(int(weighted_y - new_height // 2), original_height - new_height))
            else:
                x_offset = (original_width - new_width) // 2 if original_width > new_width else 0
                y_offset = (original_height - new_height) // 2 if original_height > new_height else 0
        else:
            x_offset = (original_width - new_width) // 2 if original_width > new_width else 0
            y_offset = (original_height - new_height) // 2 if original_height > new_height else 0

        x_offset = round_to_even(x_offset)
        y_offset = round_to_even(y_offset)
        return (x_offset, y_offset, new_width, new_height)

    except Exception as e:
        logger.exception("Error in square crop detection: %s", e)
        original_width, original_height = video_clip.size
        crop_size = min(original_width, original_height)
        new_width = round_to_even(crop_size)
        new_height = round_to_even(crop_size)
        x_offset = round_to_even((original_width - new_width) // 2) if original_width > new_width else 0
        y_offset = round_to_even((original_height - new_height) // 2) if original_height > new_height else 0
        return (x_offset, y_offset, new_width, new_height)

def detect_optimal_crop_region(video_clip, start_time: float, end_time: float, target_ratio: float = 9/16) -> Tuple[int, int, int, int]:
    try:
        original_width, original_height = video_clip.size
        if original_width / original_height > target_ratio:
            new_width = round_to_even(int(original_height * target_ratio))
            new_height = round_to_even(original_height)
        else:
            new_width = round_to_even(original_width)
            new_height = round_to_even(int(original_width / target_ratio))

        face_centers = detect_faces_in_clip(video_clip, start_time, end_time)

        if face_centers:
            total_weight = sum(area * confidence for _, _, area, confidence in face_centers)
            if total_weight > 0:
                weighted_x = sum(x * area * confidence for x, y, area, confidence in face_centers) / total_weight
                weighted_y = sum(y * area * confidence for x, y, area, confidence in face_centers) / total_weight
                weighted_y = max(0, weighted_y - new_height * 0.1)
                x_offset = max(0, min(int(weighted_x - new_width // 2), original_width - new_width))
                y_offset = max(0, min(int(weighted_y - new_height // 2), original_height - new_height))
            else:
                x_offset = (original_width - new_width) // 2 if original_width > new_width else 0
                y_offset = (original_height - new_height) // 2 if original_height > new_height else 0
        else:
            x_offset = (original_width - new_width) // 2 if original_width > new_width else 0
            y_offset = (original_height - new_height) // 2 if original_height > new_height else 0

        x_offset = round_to_even(x_offset)
        y_offset = round_to_even(y_offset)
        return (x_offset, y_offset, new_width, new_height)

    except Exception as e:
        logger.exception("Error in crop detection: %s", e)
        original_width, original_height = video_clip.size
        if original_width / original_height > target_ratio:
            new_width = round_to_even(int(original_height * target_ratio))
            new_height = round_to_even(original_height)
        else:
            new_width = round_to_even(original_width)
            new_height = round_to_even(int(original_width / target_ratio))
        x_offset = round_to_even((original_width - new_width) // 2) if original_width > new_width else 0
        y_offset = round_to_even((original_height - new_height) // 2) if original_height > new_height else 0
        return (x_offset, y_offset, new_width, new_height)

def detect_faces_in_clip(video_clip, start_time: float, end_time: float) -> List[Tuple[int, int, int, float]]:
    face_centers: List[Tuple[int, int, int, float]] = []
    try:
        # MediaPipe lazy import
        try:
            import mediapipe as mp
            mp_face_detection = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
            use_mediapipe = True
        except Exception:
            mp_face_detection = None
            use_mediapipe = False

        haar_cascade = None
        try:
            import cv2
            haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception:
            logger.debug("OpenCV or Haar cascade not available for face detection")

        # sampling frames
        duration = max(0.1, end_time - start_time)
        sample_interval = min(0.5, duration / 10.0)
        sample_times = []
        t = start_time
        while t < end_time:
            sample_times.append(t)
            t += sample_interval
        if duration > 1.0:
            mid = start_time + duration / 2
            if mid not in sample_times:
                sample_times.append(mid)
        sample_times = sorted(set([s for s in sample_times if s < end_time]))

        for sample_time in sample_times:
            try:
                frame = video_clip.get_frame(sample_time)
                if frame is None:
                    continue
                frame_rgb = frame
                height, width = frame_rgb.shape[:2]
                detected_faces = []

                if use_mediapipe and mp_face_detection is not None:
                    try:
                        import mediapipe as mp
                        frame_rgb_uint8 = frame_rgb.astype('uint8')
                        results = mp_face_detection.process(frame_rgb_uint8)
                        if results and getattr(results, "detections", None):
                            for detection in results.detections:
                                bbox = detection.location_data.relative_bounding_box
                                x = int(bbox.xmin * width)
                                y = int(bbox.ymin * height)
                                w = int(bbox.width * width)
                                h = int(bbox.height * height)
                                confidence = float(detection.score[0]) if getattr(detection, "score", None) else 0.5
                                if w > 30 and h > 30:
                                    detected_faces.append((x + w // 2, y + h // 2, w * h, confidence))
                    except Exception:
                        logger.debug("MediaPipe detection error at %.2fs", sample_time)

                # Haar fallback
                if not detected_faces and haar_cascade is not None:
                    try:
                        import cv2
                        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                        faces = haar_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))
                        for (x, y, w, h) in faces:
                            face_area = w * h
                            relative_size = face_area / (width * height)
                            confidence = min(0.9, 0.3 + relative_size * 2)
                            detected_faces.append((x + w // 2, y + h // 2, face_area, confidence))
                    except Exception:
                        logger.debug("Haar detection error at %.2fs", sample_time)

                for (cx, cy, area, conf) in detected_faces:
                    frame_area = width * height
                    relative_area = area / frame_area
                    if 0.005 < relative_area < 0.9:
                        face_centers.append((int(cx), int(cy), int(area), float(conf)))

            except Exception:
                logger.debug("Error processing frame at %.2fs", sample_time)
                continue

    except Exception as e:
        logger.exception("Error in face detection: %s", e)
    finally:
        try:
            if mp_face_detection is not None:
                mp_face_detection.close()
        except Exception:
            pass

    # filter small outliers
    if len(face_centers) > 2:
        face_centers = filter_face_outliers(face_centers)
    return face_centers

def filter_face_outliers(face_centers: List[Tuple[int, int, int, float]]) -> List[Tuple[int, int, int, float]]:
    if len(face_centers) < 3:
        return face_centers
    try:
        x_positions = [x for x, y, area, conf in face_centers]
        y_positions = [y for x, y, area, conf in face_centers]
        median_x = np.median(x_positions)
        median_y = np.median(y_positions)
        std_x = np.std(x_positions)
        std_y = np.std(y_positions)
        filtered_faces = []
        for face in face_centers:
            x, y, area, conf = face
            if (abs(x - median_x) <= 2 * std_x and abs(y - median_y) <= 2 * std_y):
                filtered_faces.append(face)
        return filtered_faces if filtered_faces else face_centers
    except Exception:
        return face_centers

def create_whisper_subtitles(
    video_path: Path,
    clip_start: float,
    clip_end: float,
    video_width: int,
    video_height: int,
    font_family: str = "DejaVu-Sans",
    font_size: int = 24,
    font_color: str = "#FFFFFF",
    square_y_position: int = None,
    square_size: int = None
) -> List[Any]:
    # Ensure moviepy available
    VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips = _import_moviepy()
    
    transcript_data = load_cached_transcript_data(video_path)
    if not transcript_data or not transcript_data.get('words'):
        logger.warning("No cached transcript data available for subtitles")
        return []

    clip_start_ms = int(clip_start * 1000)
    clip_end_ms = int(clip_end * 1000)

    relevant_words = []
    for word_data in transcript_data['words']:
        word_start = int(word_data.get('start', 0))
        word_end = int(word_data.get('end', 0))
        if word_start < clip_end_ms and word_end > clip_start_ms:
            relative_start = max(0, (word_start - clip_start_ms) / 1000.0)
            relative_end = min((clip_end_ms - clip_start_ms) / 1000.0, (word_end - clip_start_ms) / 1000.0)
            if relative_end > relative_start:
                relevant_words.append({
                    'text': word_data.get('text', ''),
                    'start': relative_start,
                    'end': relative_end,
                    'confidence': word_data.get('confidence', 1.0)
                })

    if not relevant_words:
        logger.warning("No words found in clip timerange")
        return []

    subtitle_clips = []
    processor = VideoProcessor(font_family, font_size, font_color)
    
    # Use available fonts - DejaVu is confirmed to be available
    font_arg = "DejaVu-Sans"  # This font is available and works with ImageMagick
    
    # --- Increased font sizing: 1.5× multiplier, min 28, max 64 ---
    scale_multiplier = 1.5
    calculated_font_size = int(font_size * (video_width / 720) * scale_multiplier)
    final_font_size = max(28, min(64, calculated_font_size))
    # ----------------------------------------------------------------

    words_per_subtitle = 3
    
    # FIX: Add the missing code block that builds the subtitle text
    for i in range(0, len(relevant_words), words_per_subtitle):
        word_group = relevant_words[i:i + words_per_subtitle]
        if not word_group:
            continue
            
        # Build the text for this subtitle
        text = ' '.join([word['text'] for word in word_group])
        
        # Calculate timing for this subtitle
        segment_start = word_group[0]['start']
        segment_end = word_group[-1]['end']
        segment_duration = segment_end - segment_start
        
        if segment_duration <= 0:
            continue
            
        try:
            # Attempt TextClip with 'label' method; fall back to 'caption' on failure
            try:
                text_clip = TextClip(
                    txt=text,
                    fontsize=final_font_size,
                    font=font_arg,
                    color=font_color,
                    method='label'
                ).set_duration(segment_duration).set_start(segment_start)
            except Exception as e_label:
                logger.debug("TextClip 'label' method failed: %s. Trying 'caption'...", e_label)
                text_clip = TextClip(
                    txt=text,
                    fontsize=final_font_size,
                    font=font_arg,
                    color=font_color,
                    method='caption'
                ).set_duration(segment_duration).set_start(segment_start)

            if text_clip is not None:
                text_height = text_clip.size[1] if getattr(text_clip, "size", None) else int(final_font_size * 1.6)
                # Position subtitles inside the square frame at the bottom
                if square_y_position is not None and square_size is not None:
                    # Position at bottom of square with padding (80px from bottom of square)
                    padding_from_bottom = 80
                    vertical_position = square_y_position + square_size - padding_from_bottom
                else:
                    # Fallback to original positioning if square info not provided
                    vertical_position = int(video_height * 0.85)
                text_clip = text_clip.set_position(('center', vertical_position))
                subtitle_clips.append(text_clip)
            else:
                logger.warning("Failed to create subtitle for '%s'", text[:30])
        except Exception as e:
            logger.warning("Failed to create subtitle for '%s': %s", text[:30], e)
            continue

    logger.info("Created %d subtitle elements from Whisper data", len(subtitle_clips))
    return subtitle_clips


# Clip creation - uses moviepy, lazy-imported
def create_optimized_clip(
    video_path: Path,
    start_time: float,
    end_time: float,
    output_path: Path,
    add_subtitles: bool = True,
    font_family: str = "DejaVu-Sans",
    font_size: int = 24,
    font_color: str = "#FFFFFF"
) -> bool:
    video_path = Path(video_path)
    VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips = _import_moviepy()
    video = None
    clip = None
    final_clip = None
    temp_audio = None
    try:
        duration = end_time - start_time
        if duration <= 0:
            logger.error("Invalid clip duration: %.1f", duration)
            return False

        video = VideoFileClip(str(video_path))
        if start_time >= video.duration:
            logger.error("Start time %.1f exceeds video duration %.1f", start_time, video.duration)
            video.close()
            return False

        end_time = min(end_time, video.duration)
        clip = video.subclip(start_time, end_time)
        
        # Target dimensions: 9:16 vertical format (e.g., 1080x1920 for full HD)
        target_width = 1080
        target_height = 1920
        
        # Step 1: Crop to square (1:1) aspect ratio, centered on faces
        x_offset, y_offset, square_width, square_height = detect_optimal_square_crop_region(video, start_time, end_time)
        square_clip = clip.crop(x1=x_offset, y1=y_offset, x2=x_offset + square_width, y2=y_offset + square_height)
        
        # Step 2: Resize square clip to fit within the vertical canvas
        # The square should fit the width of the canvas
        square_size = target_width
        square_clip_resized = square_clip.resize((square_size, square_size))
        
        # Step 3: Create blurred background from original clip
        # Resize original clip to fill the entire 9:16 canvas
        background_clip = clip.resize((target_width, target_height))
        # Apply blur effect and remove audio (background should be silent)
        blurred_background = apply_gaussian_blur(background_clip, ksize=35).without_audio()
        
        # Step 4: Position the square video in the center of the vertical canvas
        # Calculate vertical position to center the square
        square_y_position = (target_height - square_size) // 2
        square_clip_positioned = square_clip_resized.set_position(('center', square_y_position))
        
        # Step 5: Composite blurred background with square video
        final_clips = [blurred_background, square_clip_positioned]
        
        # Step 6: Add subtitles if requested
        if add_subtitles:
            subtitle_clips = create_whisper_subtitles(
                video_path, start_time, end_time, 
                target_width, target_height,  # Use full canvas dimensions for subtitles
                font_family, font_size, font_color,
                square_y_position=square_y_position,  # Pass square position for subtitle positioning
                square_size=square_size  # Pass square size for subtitle positioning
            )
            final_clips.extend(subtitle_clips)

        # Create final composite clip with proper canvas size
        # Audio will come from square_clip_positioned (the main video)
        final_clip = CompositeVideoClip(final_clips, size=(target_width, target_height))

        tmpf = tempfile.NamedTemporaryFile(prefix="tmp_audio_", suffix=".m4a", delete=False)
        temp_audio = tmpf.name
        tmpf.close()

        processor = VideoProcessor(font_family, font_size, font_color)
        encoding_settings = processor.get_optimal_encoding_settings("high")

        final_clip.write_videofile(
            str(output_path),
            temp_audiofile=temp_audio,
            remove_temp=True,
            logger=None,
            codec=encoding_settings.get("codec"),
            audio_codec=encoding_settings.get("audio_codec"),
            bitrate=encoding_settings.get("bitrate"),
            audio_bitrate=encoding_settings.get("audio_bitrate"),
            preset=encoding_settings.get("preset"),
            ffmpeg_params=encoding_settings.get("ffmpeg_params", [])
        )

        logger.info("Successfully created clip: %s", output_path)
        return True

    except Exception as e:
        logger.exception("Failed to create clip: %s", e)
        return False

    finally:
        try:
            if final_clip is not None:
                final_clip.close()
        except Exception:
            pass
        try:
            if clip is not None:
                clip.close()
        except Exception:
            pass
        try:
            if video is not None:
                video.close()
        except Exception:
            pass
        try:
            if temp_audio and Path(temp_audio).exists():
                os.remove(temp_audio)
        except Exception:
            pass

# --- Clip creation and transitions ------------------------------------------------------
def create_clips_from_segments(
    video_path: Path, 
    segments: List[Dict[str, Any]], 
    output_dir: Path, 
    font_family: str = "DejaVu-Sans", 
    font_size: int = 24, 
    font_color: str = "#FFFFFF"
) -> List[Dict[str, Any]]:
    """Create optimized video clips from segments."""
    logger.info(f"Creating {len(segments)} clips")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    clips_info = []
    
    for i, segment in enumerate(segments):
        try:
            logger.info(f"Processing segment {i+1}: start='{segment.get('start_time')}', end='{segment.get('end_time')}'")
            
            start_seconds = parse_timestamp_to_seconds(segment['start_time'])
            end_seconds = parse_timestamp_to_seconds(segment['end_time'])
            duration = end_seconds - start_seconds
            
            logger.info(f"Segment {i+1} duration: {duration:.1f}s (start: {start_seconds}s, end: {end_seconds}s)")
            
            if duration <= 0:
                logger.warning(f"Skipping clip {i+1}: invalid duration {duration:.1f}s")
                continue
            
            clip_filename = f"clip_{i+1}_{segment['start_time'].replace(':', '')}-{segment['end_time'].replace(':', '')}.mp4"
            clip_path = output_dir / clip_filename
            
            success = create_optimized_clip(video_path, start_seconds, end_seconds, clip_path, True, font_family, font_size, font_color)
            
            if success:
                clip_info = {
                    "clip_id": i + 1,
                    "filename": clip_filename,
                    "path": str(clip_path),
                    "start_time": segment['start_time'],
                    "end_time": segment['end_time'],
                    "duration": duration,
                    "text": segment['text'],
                    "relevance_score": segment['relevance_score'],
                    "reasoning": segment['reasoning']
                }
                clips_info.append(clip_info)
                logger.info(f"Created clip {i+1}: {duration:.1f}s")
            else:
                logger.error(f"Failed to create clip {i+1}")
                
        except Exception as e:
            logger.error(f"Error processing clip {i+1}: {e}")
    
    logger.info(f"Successfully created {len(clips_info)}/{len(segments)} clips")
    return clips_info

def get_available_transitions() -> List[str]:
    """Get list of available transition video files."""
    transitions_dir = Path(__file__).parent.parent / "transitions"
    if not transitions_dir.exists():
        logger.warning("Transitions directory not found")
        return []
    
    transition_files = []
    for file_path in transitions_dir.glob("*.mp4"):
        transition_files.append(str(file_path))
    
    logger.info(f"Found {len(transition_files)} transition files")
    return transition_files

def apply_transition_effect(clip1_path: Path, clip2_path: Path, transition_path: Path, output_path: Path) -> bool:
    """Apply transition effect between two clips using a transition video."""
    VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips = _import_moviepy()
    
    try:
        # Load clips
        clip1 = VideoFileClip(str(clip1_path))
        clip2 = VideoFileClip(str(clip2_path))
        transition = VideoFileClip(str(transition_path))
        
        # Ensure transition duration is reasonable (max 1.5 seconds)
        transition_duration = min(1.5, transition.duration)
        transition = transition.subclip(0, transition_duration)
        
        # Resize transition to match clip dimensions
        clip_size = clip1.size
        transition = transition.resize(clip_size)
        
        # Create fade effect with transition
        fade_duration = 0.5  # Half second fade
        
        # Fade out clip1
        clip1_faded = clip1.fadeout(fade_duration)
        
        # Fade in clip2
        clip2_faded = clip2.fadein(fade_duration)
        
        # Combine: clip1 -> transition -> clip2
        final_clip = concatenate_videoclips([clip1_faded, transition, clip2_faded])
        
        # Write output
        processor = VideoProcessor()
        encoding_settings = processor.get_optimal_encoding_settings("high")
        
        final_clip.write_videofile(
            str(output_path),
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            logger=None,
            codec=encoding_settings.get("codec"),
            audio_codec=encoding_settings.get("audio_codec"),
            bitrate=encoding_settings.get("bitrate"),
            audio_bitrate=encoding_settings.get("audio_bitrate"),
            preset=encoding_settings.get("preset"),
            ffmpeg_params=encoding_settings.get("ffmpeg_params", [])
        )
        
        # Cleanup
        final_clip.close()
        clip1.close()
        clip2.close()
        transition.close()
        
        logger.info(f"Applied transition effect: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying transition effect: {e}")
        return False

def create_clips_with_transitions(
    video_path: Path, 
    segments: List[Dict[str, Any]], 
    output_dir: Path, 
    font_family: str = "DejaVu-Sans", 
    font_size: int = 24, 
    font_color: str = "#FFFFFF"
) -> List[Dict[str, Any]]:
    """Create video clips with transition effects between them."""
    logger.info(f"Creating {len(segments)} clips with transitions")
    
    # First create individual clips
    clips_info = create_clips_from_segments(video_path, segments, output_dir, font_family, font_size, font_color)
    
    if len(clips_info) < 2:
        logger.info("Not enough clips to apply transitions")
        return clips_info
    
    # Get available transitions
    transitions = get_available_transitions()
    if not transitions:
        logger.warning("No transition files found, returning clips without transitions")
        return clips_info
    
    # Create clips with transitions
    transition_output_dir = output_dir / "with_transitions"
    transition_output_dir.mkdir(parents=True, exist_ok=True)
    
    enhanced_clips = []
    
    for i, clip_info in enumerate(clips_info):
        if i == 0:
            # First clip - no transition before
            enhanced_clips.append(clip_info)
        else:
            # Apply transition before this clip
            prev_clip_path = Path(clips_info[i-1]["path"])
            current_clip_path = Path(clip_info["path"])
            
            # Select transition (cycle through available transitions)
            transition_path = Path(transitions[i % len(transitions)])
            
            # Create output path for clip with transition
            transition_filename = f"transition_{i}_{clip_info['filename']}"
            transition_output_path = transition_output_dir / transition_filename
            
            success = apply_transition_effect(
                prev_clip_path,
                current_clip_path,
                transition_path,
                transition_output_path
            )
            
            if success:
                # Update clip info with transition version
                enhanced_clip_info = clip_info.copy()
                enhanced_clip_info["filename"] = transition_filename
                enhanced_clip_info["path"] = str(transition_output_path)
                enhanced_clip_info["has_transition"] = True
                enhanced_clips.append(enhanced_clip_info)
                logger.info(f"Added transition to clip {i+1}")
            else:
                # Fallback to original clip if transition fails
                enhanced_clips.append(clip_info)
                logger.warning(f"Failed to add transition to clip {i+1}, using original")
    
    logger.info(f"Successfully created {len(enhanced_clips)} clips with transitions")
    return enhanced_clips

def split_video_by_duration(video_path: Path, duration_seconds: int, output_dir: Path):
    from moviepy.editor import VideoFileClip

    output_dir.mkdir(parents=True, exist_ok=True)
    clips_info = []

    with VideoFileClip(str(video_path)) as probe:
        total_duration = probe.duration

    current_start = 0.0
    clip_count = 0

    while current_start < total_duration:
        current_end = min(current_start + duration_seconds, total_duration)
        clip_duration = current_end - current_start

        if clip_duration <= 0:
            break

        clip_count += 1
        clip_filename = f"clip_{clip_count:04d}_{current_start:.1f}s-{current_end:.1f}s.mp4"
        clip_path = output_dir / clip_filename

        logger.info(
            f"Creating clip {clip_count}: "
            f"{current_start:.2f}s - {current_end:.2f}s ({clip_duration:.2f}s)"
        )

        try:
            video = VideoFileClip(str(video_path))
            clip = video.subclip(current_start, current_end)

            clip.write_videofile(
                str(clip_path),
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                logger=None,
                verbose=False
            )

            clips_info.append({
                "clip_number": clip_count,
                "filename": clip_filename,
                "path": str(clip_path),
                "start_time": current_start,
                "end_time": current_end,
                "duration": clip_duration
            })

            logger.info(f"✅ Created clip {clip_count}: {clip_filename}")

        except Exception as e:
            logger.error(f"❌ Error creating clip {clip_count}: {e}")

        finally:
            try:
                clip.close()
                video.close()
            except Exception:
                pass
            current_start = current_end

    return clips_info

def split_video_by_duration_ffmpeg(
    video_path: Path,
    duration_seconds: int,
    output_dir: Path
) -> List[Dict[str, Any]]:
    """
    Split video using pure ffmpeg (safe for Colab / long videos)
    """
    video_path = Path(video_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get duration using ffprobe
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]

    result = subprocess.run(
        probe_cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    total_duration = float(result.stdout.strip())
    logger.info(f"Video duration: {total_duration:.2f} seconds")

    clips_info = []
    clip_count = 0
    current_start = 0.0

    while current_start < total_duration:
        clip_count += 1
        current_end = min(current_start + duration_seconds, total_duration)
        clip_duration = current_end - current_start

        clip_filename = (
            f"clip_{clip_count:04d}_"
            f"{current_start:.1f}s-{current_end:.1f}s.mp4"
        )
        clip_path = output_dir / clip_filename

        logger.info(
            f"Creating clip {clip_count}: "
            f"{current_start:.2f}s - {current_end:.2f}s"
        )

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{current_start}",
            "-i", str(video_path),
            "-t", f"{clip_duration}",
            "-map", "0:v:0",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(clip_path)
        ]

        process = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode != 0:
            logger.error(
                f"ffmpeg failed for clip {clip_count}: {process.stderr}"
            )
        else:
            clips_info.append({
                "clip_number": clip_count,
                "filename": clip_filename,
                "path": str(clip_path),
                "start_time": current_start,
                "end_time": current_end,
                "duration": clip_duration
            })
            logger.info(f"✅ Created clip {clip_count}")

        current_start = current_end

    return clips_info