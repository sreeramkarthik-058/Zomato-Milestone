"""Verification script for Groq API calls.

This script initializes the GroqProvider and makes a simple completion request
to verify that the API key and connection are working correctly.
"""

import sys
from pathlib import Path

# Add src to sys.path to allow importing from restaurant_recommender
sys.path.append(str(Path(__file__).parent.parent / "src"))

from restaurant_recommender.llm.provider import create_llm_provider
from restaurant_recommender.config import get_settings

def verify_api():
    print("Initializing Groq provider...")
    try:
        settings = get_settings()
        print(f"Using model: {settings.llm_model}")
        print(f"Provider: {settings.llm_provider}")
        
        provider = create_llm_provider(settings)
        
        print("\nSending test completion request...")
        messages = [
            {"role": "user", "content": "Hello! Please respond with a short sentence to confirm you are working."}
        ]
        
        response = provider.complete(messages)
        
        print("\n--- API Response ---")
        print(response)
        print("--------------------")
        
        print("\nAPI call successful!")
        
    except Exception as e:
        print(f"\nError during API verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_api()
