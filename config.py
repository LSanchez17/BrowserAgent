import os


class Settings:
    """Application settings."""
    
    # Ollama Configuration
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    MODEL: str = os.getenv("MODEL", "qwen3:8b")
    
    # Browser Configuration
    HEADLESS: bool = os.getenv("HEADLESS", "True").lower() == "true"
    
    # Service Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "True").lower() == "true"
    
    # API Configuration
    TITLE: str = "BrowserAgent Microservice"
    DESCRIPTION: str = "LLM-powered browser automation service with async webhook support"
    VERSION: str = "1.0.0"


settings = Settings()
