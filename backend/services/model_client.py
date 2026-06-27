import json
import asyncio
from typing import Optional
import httpx
from openai import AsyncOpenAI
from google import genai
import os

from config import settings

class ModelError(Exception):
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code

class ModelClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key
        
        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=api_key)
            self.model_name = settings.MODEL_NAME or "gpt-4o"
        elif self.provider == "github":
            self.client = AsyncOpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=api_key,
            )
            self.model_name = settings.MODEL_NAME or "gpt-4o"
        elif self.provider == "gemini":
            self.client = genai.Client(api_key=api_key)
            self.model_name = settings.MODEL_NAME or "gemini-2.5-flash-lite"
        elif self.provider == "openrouter":
            self.client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            # Use a completely free model on OpenRouter by default to avoid 402 Credit errors
            self.model_name = settings.MODEL_NAME or "google/gemini-2.0-flash-lite-preview-02-05:free"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _strip_json_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 1000, json_mode: bool = False) -> str:
        backoffs = [2, 5, 10, 35, 60]
        for attempt in range(len(backoffs) + 1):
            try:
                if self.provider in ["openai", "github", "openrouter"]:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    kwargs = {
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    if json_mode and self.provider in ["openai", "openrouter"]:
                        kwargs["response_format"] = {"type": "json_object"}
                        
                    response = await self.client.chat.completions.create(**kwargs)
                    return response.choices[0].message.content
                
                elif self.provider == "gemini":
                    from google.genai import types
                    generation_config = types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        system_instruction=system_prompt,
                    )
                    if json_mode:
                        generation_config.response_mime_type = "application/json"
                    
                    response = await self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=user_prompt,
                        config=generation_config
                    )
                    return response.text
                    
            except Exception as e:
                if attempt == len(backoffs):
                    raise ModelError(str(e), self.provider)
                await asyncio.sleep(backoffs[attempt])
                
        raise ModelError("Max retries exceeded", self.provider)

    async def complete_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 1000) -> dict:
        max_attempts = 3
        last_cleaned = ""
        for attempt in range(max_attempts):
            text = await self.complete(system_prompt, user_prompt, temperature, max_tokens, json_mode=True)
            cleaned = self._strip_json_fences(text)
            last_cleaned = cleaned
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                if attempt == max_attempts - 1:
                    raise ModelError(f"Failed to parse JSON response: {cleaned}", self.provider)
                await asyncio.sleep(1)

def create_model_client() -> ModelClient:
    provider = settings.MODEL_PROVIDER
    if provider == "github":
        key = settings.GITHUB_TOKEN
    elif provider == "openai":
        key = settings.OPENAI_API_KEY
    elif provider == "gemini":
        key = settings.GEMINI_API_KEY
    elif provider == "openrouter":
        key = settings.OPENROUTER_API_KEY
    else:
        raise ValueError("Invalid MODEL_PROVIDER")
        
    if not key:
        raise ValueError(f"Missing API key for provider {provider}")
        
    if provider == "gemini":
        os.environ["GEMINI_API_KEY"] = key
    elif not os.environ.get("GEMINI_API_KEY"):
        # ADK requires GEMINI_API_KEY to be set in the environment even if we use another provider
        os.environ["GEMINI_API_KEY"] = "dummy_adk_key"
        
    return ModelClient(provider=provider, api_key=key)
