from services.decomposition_service import decompose_goal
import json
import traceback

try:
    print("Attempting decomposition with LLM...")
    # Goal: Use a real goal related to uploaded PDFs (Machine Learning)
    result = decompose_goal("I want to learn machine learning")
    
    print("\n=== RESPONSE STATUS ===")
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['outlineConfidence']}")
    print(f"Coverage: {result['evidenceCoverage']}")
    
    print("\n=== GENERATED TOC ===")
    print(json.dumps(result['toc'], indent=2))
    
    print("\n=== GAPS ===")
    print(json.dumps(result['gaps'], indent=2))

except Exception:
    traceback.print_exc()
