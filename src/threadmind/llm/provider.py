import os
import json
import hashlib
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv
from src.threadmind import config

load_dotenv()

class LLMProvider:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.api_key = os.getenv("LLM_API_KEY")
        
        self.cache_dir = config.PROJECT_ROOT / ".cache" / "llm"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if self.provider == "openai":
            if not self.api_key:
                raise ValueError("LLM_API_KEY environment variable is required for OpenAI provider.")
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "ollama":
            self.ollama_endpoint = "http://localhost:11434"
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented.")
            
    def verify_model_availability(self):
        """
        Verifies that the requested model exists in the provider's API.
        """
        if self.provider == "openai":
            try:
                models = self.client.models.list()
                available_models = [m.id for m in models.data]
                if self.model not in available_models:
                    raise ValueError(f"Requested model '{self.model}' is NOT available in the configured OpenAI account. Available models include: {available_models[:5]}...")
            except Exception as e:
                raise RuntimeError(f"Failed to verify model availability: {e}")
        elif self.provider == "ollama":
            try:
                response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=5)
                response.raise_for_status()
                models = response.json().get("models", [])
                available_models = [m["name"] for m in models]
                if self.model not in available_models and f"{self.model}:latest" not in available_models:
                    raise ValueError(f"Requested model '{self.model}' is NOT available in local Ollama. Available models: {available_models}. Please run 'ollama pull {self.model}' first.")
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Failed to connect to local Ollama instance at {self.ollama_endpoint}. Is Ollama running? Error: {e}")
        return True
        
    def _get_cache_path(self, prompt: str) -> str:
        # Cache based on hash of the prompt and model to ensure reproducibility and save costs
        key = hashlib.sha256(f"{self.model}:{prompt}".encode()).hexdigest()
        return self.cache_dir / f"{key}.json"

    def predict(self, prompt: str, json_mode: bool = True) -> dict:
        cache_path = self._get_cache_path(prompt)
        
        # 1. Check Cache
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                result_data = json.load(f)
                result_data["_cache_hit"] = True
                return result_data
                
        # 2. Call API
        try:
            if self.provider == "openai":
                kwargs = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                    
                response = self.client.chat.completions.create(**kwargs)
                result_text = response.choices[0].message.content
                
                if json_mode:
                    result_data = json.loads(result_text)
                else:
                    result_data = {"text": result_text}
                
            elif self.provider == "ollama":
                max_retries = 3
                result_data = None
                last_error = None
                
                for attempt in range(max_retries):
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.0, "num_ctx": 4096}
                    }
                    if json_mode:
                        payload["format"] = "json"
                        
                    response = requests.post(f"{self.ollama_endpoint}/api/chat", json=payload, timeout=120)
                    response.raise_for_status()
                    
                    result_text = response.json().get("message", {}).get("content", "")
                    
                    if not json_mode:
                        result_data = {"text": result_text}
                        break
                        
                    try:
                        result_data = json.loads(result_text)
                        break
                    except json.JSONDecodeError as e:
                        last_error = e
                        time.sleep(1)
                
                if result_data is None:
                    return {"error": f"Failed to parse JSON from Ollama after {max_retries} attempts: {last_error}. Raw: {result_text}", "_cache_hit": False}
                
            # 3. Save Cache (without the cache_hit flag)
            with open(cache_path, "w") as f:
                json.dump(result_data, f)
                
            result_data["_cache_hit"] = False
            return result_data
        except Exception as e:
            return {"error": str(e), "_cache_hit": False}
