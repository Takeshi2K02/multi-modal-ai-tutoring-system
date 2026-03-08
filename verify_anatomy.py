import requests
import os
import time

API_BASE_URL = "http://localhost:8000"

def test_analyze_anatomy():
    print("Starting test_analyze_anatomy script...")
    # Wait for server to start
    connected = False
    for i in range(5):
        try:
            print(f"Checking server health (attempt {i+1})...")
            r = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                print("Server is UP!")
                connected = True
                break
        except Exception as e:
            print(f"Server not ready: {e}")
            time.sleep(2)
            
    if not connected:
        print("COULD NOT CONNECT TO SERVER. ABORTING TEST.")
        return

    dummy_pdf = "test_lecture.pdf"
    content = b'%PDF-1.1\n%\xef\xbb\xbf\n\n1 0 obj\n  << /Type /Catalog\n     /Pages 2 0 R\n  >>\nendobj\n\n2 0 obj\n  << /Type /Pages\n     /Kids [3 0 R]\n     /Count 1\n     /MediaBox [0 0 300 144]\n  >>\nendobj\n\n3 0 obj\n  <<  /Type /Page\n      /Parent 2 0 R\n      /Resources\n       << /Font\n           << /F1 4 0 R >>\n       >>\n      /Contents 5 0 R\n  >>\nendobj\n\n4 0 obj\n  << /Type /Font\n     /Subtype /Type1\n     /BaseFont /Times-Roman\n  >>\nendobj\n\n5 0 obj\n  << /Length 44 >>\nstream\nBT\n70 50 Td\n/F1 12 Tf\n(Hello world anatomy test) Tj\nET\nendstream\nendobj\n\nxref\n0 6\n0000000000 65535 f \n0000000018 00000 n \n0000000077 00000 n \n0000000178 00000 n \n0000000457 00000 n \n0000000574 00000 n \ntrailer\n  <<  /Size 6\n      /Root 1 0 R\n  >>\nstartxref\n665\n%%EOF'
    
    with open(dummy_pdf, "wb") as f:
        f.write(content)

    print(f"Opening {dummy_pdf} and sending to {API_BASE_URL}/api/analyze-anatomy...")
    try:
        with open(dummy_pdf, "rb") as f:
            files = {"file": (dummy_pdf, f, "application/pdf")}
            response = requests.post(f"{API_BASE_URL}/api/analyze-anatomy", files=files)
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Successfully received analysis result!")
            print(f"Summary Content: {str(result.get('summary_content'))[:100]}...")
            print(f"Summary File: {result.get('summary_file')}")
            
            # Verify file download
            summary_file = result.get('summary_file')
            download_url = f"{API_BASE_URL}/api/download-summary/{summary_file}"
            print(f"Verifying download from {download_url}...")
            dl_response = requests.get(download_url)
            if dl_response.status_code == 200:
                print("Download successful!")
            else:
                print(f"Download failed with status {dl_response.status_code}: {dl_response.text}")
        else:
            print(f"Analysis failed status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Request Error: {e}")
    finally:
        if os.path.exists(dummy_pdf):
            os.remove(dummy_pdf)

if __name__ == "__main__":
    test_analyze_anatomy()
