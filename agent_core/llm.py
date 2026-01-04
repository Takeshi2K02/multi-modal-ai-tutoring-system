import os
import subprocess
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def ensure_ollama_model(model_name: str):
    """
    Checks if the Ollama model exists. If not, pulls it.
    Verifies with a quick generation test.
    """
    print(f"--- Checking for Ollama model: {model_name} ---")
    
    try:
        # 1. Check if model exists
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model_name not in result.stdout:
            print(f"Model '{model_name}' not found. Pulling now... (This may take a while)")
            subprocess.run(["ollama", "pull", model_name], check=True)
            print(f"Successfully pulled '{model_name}'.")
        else:
            print(f"'{model_name}' is already installed.")

        # 2. Verify with simple run
        print(f"Verifying '{model_name}' with a test prompt...")
        # specific 'ollama run' command might be interactive, use 'generate' api or subprocess with input
        # Simplest non-interactive way:
        test_proc = subprocess.run(
            ["ollama", "run", model_name, "hello"], 
            capture_output=True, 
            text=True, 
            input="hello", # just in case
            timeout=30
        )
        if test_proc.returncode == 0:
            print(f"'{model_name}' installed successfully and ready.")
        else:
            print(f"Warning: Test run failed for '{model_name}'. Output: {test_proc.stderr}")

    except FileNotFoundError:
        print("Error: 'ollama' command not found. Please install Ollama from https://ollama.com/")
    except Exception as e:
        print(f"Error during Ollama verification: {e}")

def get_llm():
    """
    Factory function to return the configured LLM based on environment variables.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Auto-ensure model exists
        ensure_ollama_model(model_name)
        
        print(f"--- Using Local LLM: Ollama ({model_name}) ---")
        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.7
        )
    
    # Default to Gemini
    print("--- Using Cloud LLM: Google Gemini ---")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not found. Gemini calls may fail.")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        google_api_key=api_key
    )
