import os
from dotenv import load_dotenv
from openai import OpenAI

def main():
    load_dotenv()
    
    provider = os.getenv("LLM_PROVIDER")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("LLM_API_KEY")
    
    if provider != "openai":
        print("LLM_PREFLIGHT = INVALID_PROVIDER")
        return
        
    if not api_key or api_key == "your_openai_api_key_here":
        # Do not expose the exact key, just its structure or length
        print("Detected placeholder API key.")
        
    client = OpenAI(api_key=api_key)
    
    try:
        models_response = client.models.list()
        available_models = [m.id for m in models_response.data]
        
        if model in available_models:
            print("LLM_PREFLIGHT = PASS")
        else:
            print("LLM_PREFLIGHT = MODEL_UNAVAILABLE")
            print("\nAvailable models include:")
            # Print a few models that start with 'gpt'
            gpt_models = [m for m in available_models if m.startswith("gpt-")]
            print(gpt_models[:10])
            
    except Exception as e:
        if "Incorrect API key" in str(e) or "invalid_api_key" in str(e):
            print("LLM_PREFLIGHT = AUTH_FAILURE")
            print("Error: Invalid API Key.")
        else:
            print("LLM_PREFLIGHT = ERROR")
            print(f"Details: {e}")

if __name__ == "__main__":
    main()
