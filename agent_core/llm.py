import os
import warnings
import vertexai
from google.cloud import aiplatform
from langchain_google_vertexai import ChatVertexAI
from dotenv import load_dotenv

# Project ID: 25-26J-130: Suppress ChatVertexAI deprecation warning
# ChatVertexAI is required for our ADC-based service account authentication.
warnings.filterwarnings("ignore", message="The class `ChatVertexAI` was deprecated")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

load_dotenv()

def get_llm():
    """
    Factory function to return the configured LLM.
    Uses ChatVertexAI from langchain-google-vertexai.
    Maintains Vertex AI backend via ADC/Service Account.
    """
    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION")
    
    if not project or not location:
        # Fallback to hardcoded defaults if env vars are missing (Project ID: 25-26J-130)
        project = project or "edusynth-488911"
        location = location or "us-central1"
    
    # Initialize Vertex AI SDK as requested (Project ID: 25-26J-130)
    vertexai.init(project=project, location=location)
    aiplatform.init(project=project, location=location)
    
    # Log line as requested
    print("--- Google Gemini 2.5 Flash (Vertex AI) ---")
    
    # Using ChatVertexAI as requested
    # No api_key parameter — authentication must use ADC only
    return ChatVertexAI(
        model="gemini-2.5-flash",
        project=project,
        location=location,
        temperature=0.7,
        max_retries=3
    )
