import requests
import base64
import numpy as np
import cv2

def trigger_cv_load():
    # Create a blank image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    url = "http://localhost:8000/api/engagement/track"
    payload = {
        "user_id": "alex_123",
        "frame": img_base64,
        "material_id": "test_material"
    }
    
    try:
        print(">>> Sending mock CV frame to trigger model load...")
        response = requests.post(url, json=payload, timeout=10)
        print(f">>> Response: {response.status_code}")
        print(f">>> Result: {response.json()}")
    except Exception as e:
        print(f">>> Error: {e}")

if __name__ == "__main__":
    trigger_cv_load()
