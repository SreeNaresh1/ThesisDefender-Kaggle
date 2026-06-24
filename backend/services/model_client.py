import json
import asyncio
from typing import Optional
import httpx
from openai import AsyncOpenAI
import google.generativeai as genai

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
            genai.configure(api_key=api_key)
            self.model_name = settings.MODEL_NAME or "gemini-2.5-flash-lite"
        elif self.provider == "openrouter":
            self.client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            self.model_name = settings.MODEL_NAME or "meta-llama/llama-3.3-70b-instruct:free"
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
                    model = genai.GenerativeModel(self.model_name, system_instruction=system_prompt)
                    generation_config = genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                    if json_mode:
                        generation_config.response_mime_type = "application/json"
                    
                    response = model.generate_content(
                        user_prompt,
                        generation_config=generation_config
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
        
    return ModelClient(provider=provider, api_key=key)
