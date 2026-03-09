import os
import time
import warnings
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Suppress LangChain noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

load_dotenv()

def get_llm():
    """
    Factory function to return the configured LLM based on environment variables.
    Supports Vertex AI and Google AI Studio (Gemini).
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "vertexai":
        project = os.getenv("VERTEX_PROJECT_ID", "edusynth-488911")
        location = os.getenv("VERTEX_REGION", "us-central1")
        
        print(f"--- Using Vertex AI LLM: Gemini 2.5 Flash ({project}, {location}) ---")
        from langchain_google_vertexai import ChatVertexAI
        return ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=project,
            location=location,
            temperature=0.7
        )
    
    # Default to Gemini (AI Studio)
    print("--- Using Cloud LLM: Google Gemini 2.5 Flash (AI Studio) ---")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not found. Gemini calls may fail.")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=api_key
    )
