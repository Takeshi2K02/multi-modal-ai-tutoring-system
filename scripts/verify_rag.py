import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_decomposition():
    goal = "Linear Algebra"
    print(f"Testing decomposition for goal: {goal}")
    try:
        r = requests.post(f"{API_BASE_URL}/api/goal_decompose", json={"goal": goal})
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # print(json.dumps(data, indent=2)) # Debug
            print(f"Status: {data.get('status')}")
            print(f"Evidence Coverage: {data.get('evidenceCoverage')}")
            print(f"TOC Modules: {len(data.get('toc', []))}")
            print(f"Gaps found: {len(data.get('gaps', []))}")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Error testing decomposition: {e}")

if __name__ == "__main__":
    test_decomposition()
