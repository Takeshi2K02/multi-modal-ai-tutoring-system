import logging
import contextlib
import os
import torch
import torch.nn as nn
import cv2
import numpy as np
import mediapipe as mp
from transformers import pipeline

class SilenceOutput:
    """Project ID: 25-26J-130: Force absolute silence for C++ and Python logs."""
    def __enter__(self):
        self._stdout = os.dup(1)
        self._stderr = os.dup(2)
        self._devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._devnull, 1)
        os.dup2(self._devnull, 2)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self._stdout, 1)
        os.dup2(self._stderr, 2)
        os.close(self._devnull)
        os.close(self._stdout)
        os.close(self._stderr)

class EngagementModel:
    """
    Combines multiple models for comprehensive engagement tracking:
    1. Emotion Detection (FER)
    2. Gaze Tracking
    3. Posture Detection
    """
    
    def __init__(self):
        self.emotion_model = None
        self.gaze_detector = None
        self.pose_detector = None
        self.face_mesh = None
        self.face_landmarker = None
        self.pose_landmarker = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # Project ID: 25-26J-130: Log Throttling
        self._last_face_error_time = 0
        self._last_pose_error_time = 0
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        os.environ['GLOG_minloglevel'] = '2'
        
    def load_model(self):
        """Load all sub-models"""
        with SilenceOutput():
            # Initialize emotion model with fallback
            try:
                # Robust path discovery for trained models
                # Models are in cv/trained_models/engagement_emotions_vit
                BASE_DIR_CV = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                fine_tuned_path = os.path.join(BASE_DIR_CV, 'trained_models', 'engagement_emotions_vit')
                
                if os.path.exists(fine_tuned_path) and os.path.isdir(fine_tuned_path):
                    self.emotion_model = pipeline(
                        "image-classification", 
                        model=fine_tuned_path,
                        device=-1  # Force CPU for stability
                    )
                    # Fine-tuned model directly outputs engagement emotions
                    self.use_fine_tuned = True
                    self.emotion_labels = ['frustrated', 'frustrated', 'confused', 'confident', 'focused', 'bored', 'curious']
                else:
                    # Fallback to pre-trained model
                    self.emotion_model = pipeline(
                        "image-classification", 
                        model="dima806/facial_emotions_image_detection",
                        device=-1  # Force CPU for stability
                    )
                    self.use_fine_tuned = False
                    self.emotion_labels = None  # Will use mapping to engagement emotions
            except Exception as e:
                print(f"ERROR: Failed to load emotion model: {str(e)}")
                self.emotion_model = None
                self.use_fine_tuned = False
        
        # Initialize MediaPipe components with error handling
        # MediaPipe 0.10.31+ uses the Tasks API (mp.tasks.vision)
        # NOT the legacy mp.solutions API which was removed
        
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        
        try:
            face_model_path = os.path.join(model_dir, 'face_landmarker.task')
            if os.path.exists(face_model_path):
                BaseOptions = mp.tasks.BaseOptions
                FaceLandmarker = mp.tasks.vision.FaceLandmarker
                FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
                
                fl_options = FaceLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=face_model_path),
                    running_mode=mp.tasks.vision.RunningMode.IMAGE,
                    num_faces=1,
                    min_face_detection_confidence=0.3,
                    min_face_presence_confidence=0.3
                )
                self.face_landmarker = FaceLandmarker.create_from_options(fl_options)
            else:
                print(f"⚠️ Face model not found at {face_model_path}")
                self.face_landmarker = None
        except Exception as e:
            print(f"Warning: Could not initialize FaceLandmarker: {str(e)}")
            self.face_landmarker = None
        
        try:
            pose_model_path = os.path.join(model_dir, 'pose_landmarker_heavy.task')
            if os.path.exists(pose_model_path):
                BaseOptions = mp.tasks.BaseOptions
                PoseLandmarker = mp.tasks.vision.PoseLandmarker
                PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
                
                pl_options = PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=pose_model_path),
                    running_mode=mp.tasks.vision.RunningMode.IMAGE,
                    num_poses=1,
                    min_pose_detection_confidence=0.3,
                    min_pose_presence_confidence=0.3
                )
                self.pose_landmarker = PoseLandmarker.create_from_options(pl_options)
            else:
                print(f"⚠️ Pose model not found at {pose_model_path}")
                self.pose_landmarker = None
        except Exception as e:
            print(f"Warning: Could not initialize PoseLandmarker: {str(e)}")
            self.pose_landmarker = None
        
        print("[CV] 👁️  Internal Models Ready")
    
    def predict(self, frame):
        """
        Predict engagement metrics from webcam frame
        
        Returns:
            dict with emotion, gaze, posture, and confidence scores
        """
        try:
            # print(f"\n🔍 === Processing Frame ===")
            
            # Detect eye closure/drowsiness first (critical for boredom detection)
            eye_state = self.detect_eye_closure(frame)
            
            # Detect gaze direction (important for engagement and confusion)
            gaze = self.detect_gaze(frame)
            
            # Detect emotion
            emotion_result = self.detect_emotion(frame)
            
            # Detect posture
            posture = self.detect_posture(frame)
            
            # Emotion adjustments disabled - use raw model predictions
            # This allows detecting all emotions: bored, confused, neutral, happy, etc.
            # Without overriding based on eye state or gaze direction
            
            # # Adjust emotion based on eye closure (drowsiness/boredom detection)
            # emotion_result = self.adjust_emotion_by_eye_state(
            #     emotion_result['emotion'],
            #     emotion_result['confidence'],
            #     eye_state
            # )
            
            # # Adjust emotion based on upward gaze (confusion detection)
            # emotion_result = self.adjust_emotion_by_upward_gaze(
            #     emotion_result['emotion'],
            #     emotion_result['confidence'],
            #     gaze
            # )
            
            # # Further adjust emotion based on gaze direction (away = neutral)
            # # When student looks away, it doesn't mean they're bored - could be thinking/neutral
            # adjusted_emotion = self.adjust_emotion_by_gaze(
            #     emotion_result['emotion'],
            #     emotion_result['confidence'],
            #     gaze
            # )
            
            # Use raw emotion detection result
            adjusted_emotion = emotion_result
            
            # print(f"📊 FINAL: emotion={adjusted_emotion['emotion']}, gaze={gaze}, posture={posture}\n")
            
            return {
                'emotion': adjusted_emotion['emotion'],
                'emotion_confidence': adjusted_emotion['confidence'],
                'gaze': gaze,
                'posture': posture,
                'eye_state': eye_state  # Add eye state info
            }
        except Exception as e:
            print(f"Error in engagement prediction: {str(e)}")
            return {
                'emotion': 'neutral',
                'emotion_confidence': 0.5,
                'gaze': 'forward',
                'posture': 'upright'
            }
    
    def detect_emotion(self, frame):
        """Detect facial emotion using trained model"""
        try:
            # Check if emotion model is loaded
            if self.emotion_model is None:
                print("WARNING: Emotion model not loaded - returning default 'neutral'")
                return {'emotion': 'neutral', 'confidence': 0.5}
            
            # Convert frame to PIL Image for Hugging Face pipeline
            from PIL import Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect face first using OpenCV for better crop
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # If face detected, crop to face region
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_region = frame_rgb[y:y+h, x:x+w]
                pil_image = Image.fromarray(face_region)
            else:
                pil_image = Image.fromarray(frame_rgb)
            
            # Get predictions
            predictions = self.emotion_model(pil_image)
            top_prediction = predictions[0]
            emotion_label = top_prediction['label'].lower()
            confidence = top_prediction['score']
            
            # Handle fine-tuned vs pre-trained model
            if self.use_fine_tuned:
                # Fine-tuned model outputs label_0 through label_6
                # Based on alphabetical order: angry, disgust, fear, happy, neutral, sad, surprise
                engagement_map = {
                    # Label IDs (what the model actually outputs)
                    'label_0': 'frustrated',  # angry
                    'label_1': 'frustrated',  # disgust
                    'label_2': 'confused',    # fear
                    'label_3': 'confident',   # happy
                    'label_4': 'neutral',     # neutral
                    'label_5': 'bored',       # sad
                    'label_6': 'curious',     # surprise
                    # Actual emotion names (in case model outputs these)
                    'angry': 'frustrated',
                    'disgust': 'frustrated',
                    'fear': 'confused',
                    'happy': 'confident',
                    'neutral': 'neutral',
                    'sad': 'bored',
                    'surprise': 'curious',
                    # Direct engagement emotions (if model outputs them)
                    'confused': 'confused',
                    'focused': 'focused',
                    'bored': 'bored',
                    'frustrated': 'frustrated',
                    'curious': 'curious',
                    'confident': 'confident'
                }
            else:
                # Pre-trained model mapping
                engagement_map = {
                    'happy': 'confident',
                    'sad': 'bored',
                    'angry': 'frustrated',
                    'fear': 'confused',
                    'surprise': 'curious',
                    'disgust': 'frustrated',
                    'neutral': 'neutral',
                    'confused': 'confused',
                    'focused': 'focused',
                    'bored': 'bored',
                    'frustrated': 'frustrated',
                    'curious': 'curious',
                    'confident': 'confident'
                }
            
            final_emotion = engagement_map.get(emotion_label, 'focused')  # Default to focused
            
            # Log all predictions for debugging
            model_type = "Fine-tuned" if self.use_fine_tuned else "Pre-trained"
            # print(f"[{model_type}] Raw emotion: {emotion_label} -> Mapped: {final_emotion} (confidence: {confidence:.2f})")
            
            return {
                'emotion': final_emotion,
                'confidence': confidence
            }
        except Exception as e:
            print(f"Error detecting emotion: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'emotion': 'neutral', 'confidence': 0.5}
    
    def detect_eye_closure(self, frame):
        """
        Detect eye closure and drowsiness using Eye Aspect Ratio (EAR)
        Uses the Tasks API FaceLandmarker.
        Returns: 'open', 'drowsy', or 'closed'
        """
        try:
            lm = self._get_face_landmarks(frame)
            if lm is None:
                return 'unknown'
            
            # Eye landmark indices for MediaPipe Face Mesh (478 landmarks)
            LEFT_EYE = [362, 385, 387, 263, 373, 380]
            RIGHT_EYE = [33, 160, 158, 133, 153, 144]
            
            def calculate_ear(eye_indices, landmarks):
                """Calculate Eye Aspect Ratio"""
                coords = [(landmarks[idx].x, landmarks[idx].y) for idx in eye_indices]
                v1 = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
                v2 = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
                h = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))
                ear = (v1 + v2) / (2.0 * h + 0.001)
                return ear
            
            left_ear = calculate_ear(LEFT_EYE, lm)
            right_ear = calculate_ear(RIGHT_EYE, lm)
            avg_ear = (left_ear + right_ear) / 2.0
            
            EAR_THRESHOLD_CLOSED = 0.15
            EAR_THRESHOLD_DROWSY = 0.20
            
            if avg_ear < EAR_THRESHOLD_CLOSED:
                eye_state = 'closed'
            elif avg_ear < EAR_THRESHOLD_DROWSY:
                eye_state = 'drowsy'
            else:
                eye_state = 'open'
            
            # print(f"Eye state: {eye_state} (EAR: {avg_ear:.3f})")
            return eye_state
            
        except Exception as e:
            print(f"Error detecting eye closure: {str(e)}")
            return 'unknown'
    
    def adjust_emotion_by_eye_state(self, emotion, confidence, eye_state):
        """
        Adjust emotion based on eye closure state
        Closed or drowsy eyes strongly indicate boredom/fatigue
        
        Args:
            emotion: Detected facial emotion
            confidence: Detection confidence
            eye_state: 'open', 'drowsy', 'closed', or 'unknown'
        
        Returns:
            dict with adjusted emotion and confidence
        """
        try:
            # If eyes are closed or drowsy, override emotion to bored
            if eye_state == 'closed':
                # print(f"Eyes closed detected: {emotion} -> bored (high confidence)")
                return {
                    'emotion': 'bored',
                    'confidence': 0.95  # Very high confidence when eyes are closed
                }
            
            elif eye_state == 'drowsy':
                # Drowsy state indicates tiredness/boredom
                # If current emotion is not already indicating disengagement, change it
                if emotion not in ['bored', 'frustrated', 'confused']:
                    # print(f"Drowsy state detected: {emotion} -> bored")
                    return {
                        'emotion': 'bored',
                        'confidence': 0.85  # High confidence for drowsiness
                    }
                else:
                    # Keep the emotion but increase confidence if it's bored
                    if emotion == 'bored':
                        confidence = max(confidence, 0.85)
                    # print(f"Drowsy state confirms: {emotion} (confidence boosted)")
                    return {
                        'emotion': emotion,
                        'confidence': confidence
                    }
            
            # Eyes open - return emotion as-is
            return {'emotion': emotion, 'confidence': confidence}
            
        except Exception as e:
            print(f"Error adjusting emotion by eye state: {str(e)}")
            return {'emotion': emotion, 'confidence': confidence}
    
    def adjust_emotion_by_upward_gaze(self, emotion, confidence, gaze):
        """
        Adjust emotion when student looks up - strong indicator of confusion/thinking
        
        Args:
            emotion: Detected facial emotion
            confidence: Detection confidence
            gaze: Gaze direction
        
        Returns:
            dict with adjusted emotion and confidence
        """
        try:
            # If looking up, it's a strong indicator of confusion/questioning
            if gaze == 'up':
                # Looking up typically means:
                # - Trying to recall information
                # - Confused about something
                # - Thinking deeply / questioning
                
                # If emotion is not already indicating confusion, change it
                if emotion not in ['confused', 'frustrated']:
                    # print(f"Upward gaze detected: {emotion} -> confused (questioning/thinking)")
                    return {
                        'emotion': 'confused',
                        'confidence': max(confidence, 0.80)  # High confidence for upward gaze
                    }
                else:
                    # Already confused/frustrated, boost confidence
                    # print(f"Upward gaze confirms: {emotion} (confidence boosted)")
                    return {
                        'emotion': emotion,
                        'confidence': max(confidence, 0.85)
                    }
            
            # Not looking up, return as-is
            return {'emotion': emotion, 'confidence': confidence}
            
        except Exception as e:
            print(f"Error adjusting emotion by upward gaze: {str(e)}")
            return {'emotion': emotion, 'confidence': confidence}
    
    def adjust_emotion_by_gaze(self, emotion, confidence, gaze):
        """
        Adjust detected emotion based on gaze direction
        When student looks away, emotion is set to neutral with low confidence
        
        Args:
            emotion: Detected facial emotion
            confidence: Detection confidence
            gaze: Gaze direction ('screen', 'away', 'forward')
        
        Returns:
            dict with adjusted emotion and confidence
        """
        try:
            # If looking at screen, return emotion as-is
            if gaze in ['screen', 'forward']:
                return {'emotion': emotion, 'confidence': confidence}
            
            # Student is looking away - set to neutral with low confidence
            # Looking away indicates disengagement, not necessarily any specific emotion
            # We can't reliably detect emotion when face is turned away
            
            # Always set to neutral when looking away
            adjusted_emotion = 'neutral'
            
            # Significantly reduce confidence when looking away
            adjusted_confidence = min(confidence * 0.4, 0.5)  # Max 50% confidence, reduced by 60%
            
            # print(f"Gaze adjustment: {emotion} ({confidence:.2f}) -> {adjusted_emotion} ({adjusted_confidence:.2f}) [gaze: {gaze}]")
            
            return {
                'emotion': adjusted_emotion,
                'confidence': adjusted_confidence
            }
            
        except Exception as e:
            print(f"Error adjusting emotion by gaze: {str(e)}")
            return {'emotion': emotion, 'confidence': confidence}
    
    def _get_face_landmarks(self, frame):
        """Get face landmarks using the Tasks API FaceLandmarker.
        Returns list of landmarks or None."""
        try:
            if self.face_landmarker is None:
                return None
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self.face_landmarker.detect(mp_image)
            if result.face_landmarks and len(result.face_landmarks) > 0:
                return result.face_landmarks[0]
            return None
        except Exception as e:
            print(f"❌ FaceLandmarker error: {str(e)}")
            return None
    
    def _get_pose_landmarks(self, frame):
        """Get pose landmarks using the Tasks API PoseLandmarker.
        Returns list of landmarks or None."""
        try:
            if self.pose_landmarker is None:
                return None
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self.pose_landmarker.detect(mp_image)
            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                return result.pose_landmarks[0]
            return None
        except Exception as e:
            print(f"❌ PoseLandmarker error: {str(e)}")
            return None
    
    def detect_gaze(self, frame):
        """Detect gaze direction using head pose estimation from FaceLandmarker.
        
        Uses nose tip position relative to face bounding box to determine
        head orientation. Works on independent base64 frames.
        
        Returns: 'forward', 'left', 'right', 'up', 'down', or 'away'
        """
        try:
            if frame is None or frame.size == 0:
                return 'away'
            
            lm = self._get_face_landmarks(frame)
            
            if lm is None:
                import time
                if time.time() - self._last_face_error_time > 30:
                    print(f"⚠️ No face detected for gaze | shape:{frame.shape} mean:{frame.mean():.0f}")
                    self._last_face_error_time = time.time()
                return 'away'
            
            # === HEAD POSE via key landmark positions ===
            nose = lm[1]          # Nose tip
            chin = lm[152]        # Chin
            left_cheek = lm[234]  # Left face boundary
            right_cheek = lm[454] # Right face boundary
            forehead = lm[10]     # Top of face
            
            # Face bounding box from landmarks
            face_left = left_cheek.x
            face_right = right_cheek.x
            face_top = forehead.y
            face_bottom = chin.y
            
            face_width = face_right - face_left
            face_height = face_bottom - face_top
            
            if face_width < 0.01 or face_height < 0.01:
                return 'away'
            
            # Nose position relative to face bounding box (0.0 to 1.0)
            nose_rel_x = (nose.x - face_left) / face_width
            nose_rel_y = (nose.y - face_top) / face_height
            
            # Deviation from center (0 = perfectly centered)
            h_deviation = nose_rel_x - 0.5
            v_deviation = nose_rel_y - 0.5
            
            # === GAZE DIRECTION ===
            gaze_direction = 'forward'
            
            if v_deviation < -0.08:
                gaze_direction = 'up'
            elif v_deviation > 0.12:
                gaze_direction = 'down'
            elif h_deviation < -0.08:
                gaze_direction = 'left'
            elif h_deviation > 0.08:
                gaze_direction = 'right'
            
            # print(f"👁️ Gaze: {gaze_direction:>8} | nose_rx:{nose_rel_x:.3f} nose_ry:{nose_rel_y:.3f} | h_dev:{h_deviation:+.3f} v_dev:{v_deviation:+.3f}")
            return gaze_direction
            
        except Exception as e:
            print(f"❌ Gaze error: {str(e)}")
            return 'away'
    
    def detect_posture(self, frame):
        """Detect posture using PoseLandmarker, with FaceLandmarker fallback.
        
        Primary: PoseLandmarker (if shoulders visible)
        Fallback: FaceLandmarker (face position in frame)
        
        Returns: 'upright', 'leaning_forward', 'head_tilted', 'slouched',
                 'head_turned', 'head_down', 'leaning_back', or 'unknown'
        """
        try:
            if frame is None or frame.size == 0:
                return 'unknown'
            
            # Try PoseLandmarker first
            plm = self._get_pose_landmarks(frame)
            if plm is not None:
                nose = plm[0]      # NOSE
                l_sh = plm[11]     # LEFT_SHOULDER
                r_sh = plm[12]     # RIGHT_SHOULDER
                l_ear = plm[7]     # LEFT_EAR
                r_ear = plm[8]     # RIGHT_EAR
                
                # Check visibility
                nose_vis = nose.visibility if hasattr(nose, 'visibility') else 1.0
                ls_vis = l_sh.visibility if hasattr(l_sh, 'visibility') else 1.0
                rs_vis = r_sh.visibility if hasattr(r_sh, 'visibility') else 1.0
                
                if nose_vis > 0.3 and ls_vis > 0.3 and rs_vis > 0.3:
                    sc_x = (l_sh.x + r_sh.x) / 2
                    sc_y = (l_sh.y + r_sh.y) / 2
                    ear_cy = (l_ear.y + r_ear.y) / 2
                    
                    head_v = nose.y - sc_y
                    head_h = abs(nose.x - sc_x)
                    sh_tilt = abs(l_sh.y - r_sh.y)
                    ear_tilt = abs(l_ear.y - r_ear.y)
                    
                    if head_v > 0.15 or ear_cy > sc_y + 0.10:
                        posture = 'head_down'
                    elif sh_tilt > 0.06 or ear_tilt > 0.10:
                        posture = 'head_tilted'
                    elif head_h > 0.12:
                        posture = 'head_turned'
                    elif head_v > 0.08:
                        posture = 'slouched'
                    elif head_v < -0.08:
                        posture = 'leaning_forward'
                    elif 0.04 < head_v < 0.08:
                        posture = 'leaning_back'
                    else:
                        posture = 'upright'
                    
                    # print(f"🧍 Posture(pose): {posture:>15} | head_v:{head_v:.3f} head_h:{head_h:.3f} sh_tilt:{sh_tilt:.3f}")
                    return posture
            
            # FALLBACK: Use FaceLandmarker to estimate posture from face position
            flm = self._get_face_landmarks(frame)
            if flm is not None:
                nose = flm[1]
                chin = flm[152]
                forehead = flm[10]
                left_cheek = flm[234]
                right_cheek = flm[454]
                
                face_center_y = (forehead.y + chin.y) / 2
                face_center_x = (left_cheek.x + right_cheek.x) / 2
                face_tilt = abs(left_cheek.y - right_cheek.y)
                nose_z = nose.z
                
                if face_center_y > 0.65:
                    posture = 'head_down'
                elif face_tilt > 0.04:
                    posture = 'head_tilted'
                elif abs(face_center_x - 0.5) > 0.15:
                    posture = 'head_turned'
                elif nose_z < -0.08:
                    posture = 'leaning_forward'
                elif face_center_y > 0.55:
                    posture = 'slouched'
                else:
                    posture = 'upright'
                
                # print(f"🧍 Posture(face): {posture:>15} | face_y:{face_center_y:.3f} face_x:{face_center_x:.3f} tilt:{face_tilt:.3f} z:{nose_z:.3f}")
                return posture
            
            import time
            if time.time() - self._last_pose_error_time > 30:
                print(f"⚠️ No pose/face detected for posture | shape:{frame.shape} mean:{frame.mean():.0f}")
                self._last_pose_error_time = time.time()
            return 'unknown'
                
        except Exception as e:
            print(f"❌ Posture error: {str(e)}")
            return 'unknown'


class ContentModel:
    """
    Content topic detection and matching using NLP
    Analyzes OCR text to determine what topic the student is viewing
    """
    
    def __init__(self):
        self.topic_classifier = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def load_model(self):
        """Load topic classification model"""
        with SilenceOutput():
            try:
                # Using zero-shot classification for topic detection
                self.topic_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
            except Exception as e:
                print(f"Error loading content model: {str(e)}")
    
    def predict(self, text):
        """
        Predict topic/subject from extracted text
        
        Args:
            text: OCR extracted text from screen
            
        Returns:
            str: Detected topic/subject
        """
        try:
            if not text or len(text.strip()) < 10:
                return None
            
            # Define common educational topics
            candidate_topics = [
                'mathematics', 'algebra', 'geometry', 'calculus',
                'physics', 'chemistry', 'biology',
                'programming', 'python', 'javascript', 'web development',
                'data science', 'machine learning',
                'history', 'geography', 'literature',
                'fractions', 'equations', 'science'
            ]
            
            # Classify text
            result = self.topic_classifier(
                text,
                candidate_topics,
                multi_label=False
            )
            
            # Return top topic with confidence > 0.3
            if result['scores'][0] > 0.3:
                return result['labels'][0]
            else:
                return 'general'
                
        except Exception as e:
            print(f"Error predicting content topic: {str(e)}")
            return None
