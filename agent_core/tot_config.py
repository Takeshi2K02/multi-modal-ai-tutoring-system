import asyncio
import re
import json
from agent_core.schemas import ToTConfig

# Configuration
CONFIG = ToTConfig(
    max_depth=2, # Exactly 3 stages: Root (0), L1 (1), L2 (2)
    beam_width=3, 
    branching_factor=3, 
    score_threshold=0.85
)

# Vertex AI Rate Limiting Semaphore (Cap concurrent requests at 3 as per Issue 2)
semaphore = asyncio.Semaphore(3)

# Helper for robust parsing
def extract_json_from_text(text: str) -> dict:
    """
    Extracts the first valid JSON object from a string, handling markdown blocks and control characters.
    """
    cleaned_text = text
    try:
        # Pre-processing: Strip markdown backticks
        cleaned_text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        
        # Robust Regex for JSON block extraction if still wrapped
        match = re.search(r"(\{.*\})", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(1)
            
        # Use strict=False to handle invalid control characters (e.g. newlines in strings)
        return json.loads(cleaned_text, strict=False)
    except Exception as e:
        print(f"[Parser] !!! RAW_LLM_RESPONSE failing at char 281: {text}")
        # Final attempt: manual regex fix for unescaped quotes in common fields
        try:
            # Simple heuristic: try to escape quotes that are not followed by , or }
            # This is risky but helps for "label" or "approach" strings
            manual_fix = re.sub(r'(?<=[:\s])"(.*?)"(?=[\s,])', r'"\1"', cleaned_text)
            return json.loads(manual_fix, strict=False)
        except:
            raise ValueError(f"Failed to extract JSON from text: {text[:200]}... Error: {e}")
