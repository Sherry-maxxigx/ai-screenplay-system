from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI编剧协同创作系统"
    API_V1_STR: str = "/api"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    OPENAI_API_KEY: Optional[str] = None
    ZHIPUAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
