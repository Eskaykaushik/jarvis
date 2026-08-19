from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Jarvis"
    debug: bool = False

    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model name")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_model: str = Field(default="meta-llama/llama-3.1-8b-instruct:free", description="OpenRouter model name")
    together_api_key: str = Field(default="", description="Together AI API key")
    together_model: str = Field(default="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", description="Together model name")
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model name")
    cerebras_api_key: str = Field(default="", description="Cerebras API key")
    cerebras_model: str = Field(default="llama-3.3-70b", description="Cerebras model name")

    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    resend_api_key: str = Field(default="", description="Resend API key for emails")
    email_from: str = Field(default="noreply@example.com", description="Sender email address")

    chat_cache_ttl: int = Field(default=3600, description="Chat cache TTL in seconds (1hr)")
    summary_cache_ttl: int = Field(default=21600, description="Summary cache TTL in seconds (6hr)")

    model_max_tokens: int = Field(default=1024, description="Max tokens for model responses")
    model_timeout: int = Field(default=30, description="Provider request timeout in seconds")

    allowed_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
