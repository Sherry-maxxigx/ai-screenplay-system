from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    PROJECT_NAME: str = "AI剧本协同创作系统"
    API_V1_STR: str = "/api"
    
    # MySQL数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "screenplay_system"
    
    # MongoDB配置
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "screenplay_system"
    
    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # Neo4j配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # OpenAI API配置
    OPENAI_API_KEY: Optional[str] = None
    
    # 智谱AI API配置
    ZHIPUAI_API_KEY: Optional[str] = "29a636d5b47c4ba78cbe1612e60d33cd.7DCz91mVvjYCCCYI"
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: Optional[str] = "sk-90c0a9261628428d993d14ab5c0ae4c5"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()