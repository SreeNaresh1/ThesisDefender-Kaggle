from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    # Model provider
    MODEL_PROVIDER: str = "github"
    MODEL_NAME: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None

    # Azure Foundry IQ
    AZURE_SEARCH_ENDPOINT: Optional[str] = None
    AZURE_SEARCH_KEY: Optional[str] = None
    AZURE_SEARCH_INDEX_NAME: str = "thesisdefender-index"

    # Infrastructure
    REDIS_URL: str = "redis://localhost:6379"
    UNPAYWALL_EMAIL: Optional[str] = None

    # ADK integration — set USE_ADK=true to route through Google ADK SequentialAgent.
    # Defaults to False: original pipeline.py logic runs unchanged.
    USE_ADK: bool = False

    # MCP Server integration (Phase 2)
    # URL of the running FastMCP SSE server started by mcp_server/run_server.py.
    # Agents degrade gracefully to no enrichment if the server is unreachable.
    MCP_SERVER_URL: str = "http://localhost:8001/sse"
    MCP_PORT: int = 8001
    
    @model_validator(mode="after")
    def validate_api_keys(self) -> 'Settings':
        if self.MODEL_PROVIDER == "github" and not self.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required when MODEL_PROVIDER is 'github'")
        elif self.MODEL_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when MODEL_PROVIDER is 'openai'")
        elif self.MODEL_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when MODEL_PROVIDER is 'gemini'")
        elif self.MODEL_PROVIDER == "openrouter" and not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when MODEL_PROVIDER is 'openrouter'")
        return self

    class Config:
        env_file = ".env"

settings = Settings()
