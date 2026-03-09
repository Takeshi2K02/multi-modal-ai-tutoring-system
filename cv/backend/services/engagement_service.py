import cv2
import numpy as np
import base64
import torch
from PIL import Image
import io
import easyocr
from services.ml_models import EngagementModel, ContentModel

import logging
import contextlib

# Project ID: 25-26J-130: CV Stability Configuration
_emotion_buffer = [] 
_last_valid_result = {
    'emotion': 'neutral',
    'engagement_score': 0.5,
    'gaze': 'forward',
    'posture': 'upright'
}

# Initialize models (loaded once)
engagement_model = None
content_model = None
ocr_reader = None

def initialize_models():
    """Initialize ML models once"""
    global engagement_model, content_model, ocr_reader
    
    if engagement_model is None:
        engagement_model = EngagementModel()
        engagement_model.load_model()
    
    if content_model is None:
        content_model = ContentModel()
        content_model.load_model()
    
    if ocr_reader is None:
        ocr_reader = easyocr.Reader(['en'])

def decode_base64_image(base64_string):
    """Convert base64 string to numpy array"""
    try:
        # Remove header if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        return image_np
    except Exception as e:
        print(f"Error decoding image: {str(e)}")
        return None

def process_engagement_data(frame_data, screen_data=None, material_id=None):
    """
    Process webcam frame and screen data to extract engagement metrics
    
    Args:
        frame_data: Base64 encoded webcam image
        screen_data: Base64 encoded screen capture (optional)
        material_id: Current material being viewed (optional)
    
    Returns:
        Dictionary with engagement metrics in required format
    """
    try:
        # Initialize models if needed
        initialize_models()
        
        # Decode webcam frame
        frame = decode_base64_image(frame_data)
        if frame is None:
            raise ValueError("Failed to decode frame data")
        
        # Get engagement predictions from model
        engagement_result = engagement_model.predict(frame)
        
        # Process screen data for OCR if provided
        ocr_excerpt = None
        context_match = None
        if screen_data:
            screen_frame = decode_base64_image(screen_data)
            if screen_frame is not None:
                ocr_result = extract_text_from_screen(screen_frame)
                ocr_excerpt = ocr_result.get('text', '')[:200]  # First 200 chars
                context_match = content_model.predict(ocr_excerpt)
        
        # Calculate overall engagement score
        engagement_score = calculate_engagement_score(engagement_result)
        
        # Determine engagement state
        engagement_state = get_engagement_state(engagement_score)
        
        # Create engagement context state
        engagement_context_state = f"{engagement_result['emotion']}_on_{context_match}" if context_match else engagement_result['emotion']
        
        # CV JITTER FILTERING & STABILITY BUFFER (Project ID: 25-26J-130)
        global _emotion_buffer, _last_valid_result
        _emotion_buffer.append(engagement_result['emotion'])
        if len(_emotion_buffer) > 3:
            _emotion_buffer.pop(0)
            
        # Only change "official" state if 3 consecutive frames match
        if len(_emotion_buffer) == 3 and len(set(_emotion_buffer)) == 1:
            stable_emotion = _emotion_buffer[0]
        else:
            stable_emotion = _last_valid_result['emotion']

        # Format response
        result = {
            'timestamp': None,  # Will be set by caller
            'emotion': stable_emotion,
            'emotion_conf': round(engagement_result['emotion_confidence'], 2),
            'engagement_score': round(engagement_score, 2),
            'engagement_state': engagement_state,
            'gaze': engagement_result['gaze'],
            'posture': engagement_result['posture'],
            'ocr_excerpt': ocr_excerpt,
            'context_match': context_match,
            'engagement_context_state': f"{stable_emotion}_on_{context_match}" if context_match else stable_emotion
        }
        
        # Update last valid result for fallback
        _last_valid_result = {
            'emotion': stable_emotion,
            'engagement_score': round(engagement_score, 2),
            'gaze': engagement_result['gaze'],
            'posture': engagement_result['posture']
        }
        
        return result
        
    except Exception as e:
        print(f"Error processing engagement data: {str(e)}")
        # Project ID: 25-26J-130: GAZE FALLBACK LOGIC
        # Return last known valid result instead of hardcoded defaults
        return {
            'timestamp': None,
            'emotion': _last_valid_result['emotion'],
            'emotion_conf': 0.0,
            'engagement_score': _last_valid_result['engagement_score'],
            'engagement_state': 'unknown',
            'gaze': _last_valid_result['gaze'],
            'posture': _last_valid_result['posture'],
            'ocr_excerpt': None,
            'context_match': None,
            'engagement_context_state': _last_valid_result['emotion']
        }

def extract_text_from_screen(screen_frame):
    """Extract text from screen capture using OCR"""
    try:
        # Use EasyOCR to extract text
        results = ocr_reader.readtext(screen_frame)
        
        # Combine all detected text
        text_parts = [result[1] for result in results]
        full_text = ' '.join(text_parts)
        
        return {
            'text': full_text,
            'detections': len(results)
        }
    except Exception as e:
        print(f"Error in OCR: {str(e)}")
        return {'text': '', 'detections': 0}

def calculate_engagement_score(engagement_result):
    """
    Calculate overall engagement score (0-1) from individual metrics
    
    Factors:
    - Emotion: positive emotions = higher score
    - Gaze: looking at screen = higher score
    - Posture: upright = higher score
    """
    score = 0.5  # Base score
    
    # Emotion contribution (0.6 weight - high impact)
    emotion_scores = {
        'happy': 0.9,
        'focused': 1.0,
        'engaged': 0.95,
        'confident': 0.85,
        'curious': 0.9,
        'neutral': 0.6,
        'confused': 0.5,         # Confused students are still engaged
        'frustrated': 0.55,      # Frustrated students are still trying/engaged
        'bored': 0.1,            # Low score: bored = low engagement, triggers disengaged state
        'tired': 0.3
    }
    emotion_score = emotion_scores.get(engagement_result['emotion'], 0.5)
    score += (emotion_score - 0.5) * 0.6  # High weight for emotion
    
    # Gaze contribution (0.2 weight)
    gaze_scores = {
        'forward': 0.20,    # Looking directly at camera - highly engaged
        'left': -0.10,      # Head turned left - mildly distracted
        'right': -0.10,     # Head turned right - mildly distracted
        'up': 0.0,          # Looking up - thinking/confused (neutral)
        'down': -0.15,      # Looking down - distracted/bored
        'away': -0.10,      # No face detected - mildly negative
        'unknown': 0.0      # Detection uncertain - neutral (don't penalize)
    }
    gaze_contribution = gaze_scores.get(engagement_result['gaze'], 0)
    score += gaze_contribution
    
    # Posture contribution (0.2 weight)
    posture_scores = {
        'upright': 0.2,              # Attentive, facing screen
        'leaning_forward': 0.18,     # Very engaged
        'head_tilted': 0.0,          # Confusion/thinking - neutral
        'leaning_back': -0.05,       # Less engaged
        'slouched': -0.15,           # Poor engagement
        'head_turned': -0.15,        # Looking away, distracted
        'head_down': -0.20,          # Very distracted, bored (phone/desk)
        'unknown': 0.0               # Detection uncertain - neutral (don't penalize)
    }
    posture_contribution = posture_scores.get(engagement_result['posture'], 0)
    score += posture_contribution
    
    # Clamp between 0 and 1
    final_score = max(0.0, min(1.0, score))
    
    # Log scoring breakdown for debugging (occasional logging)
    # if np.random.random() < 0.15:  # 15% of frames
    #     emotion_contrib = (emotion_score - 0.5) * 0.6
    #     print(f"\n📊 Engagement Score Breakdown:")
    #     print(f"   Emotion: {engagement_result['emotion']} ({emotion_score:.2f}) → {emotion_contrib:+.2f}")
    #     print(f"   Gaze: {engagement_result['gaze']} → {gaze_contribution:+.2f}")
    #     print(f"   Posture: {engagement_result['posture']} → {posture_contribution:+.2f}")
    #     print(f"   Final Score: {final_score:.2f}")
    
    return final_score

def get_engagement_state(engagement_score):
    """Convert engagement score to categorical state
    
    Thresholds:
    - >= 0.65: engaged
    - >= 0.4: moderately_engaged  
    - < 0.4: disengaged
    """
    if engagement_score >= 0.65:
        return 'engaged'
    elif engagement_score >= 0.4:
        return 'moderately_engaged'
    else:
        return 'disengaged'
