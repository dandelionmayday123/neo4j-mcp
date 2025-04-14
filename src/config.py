from pydantic import BaseModel, Field
from typing import Optional
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config(BaseModel):
    # Neo4j配置
    NEO4J_URI: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    NEO4J_USERNAME: str = Field(default_factory=lambda: os.getenv("NEO4J_USERNAME", "neo4j"))
    NEO4J_PASSWORD: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "your-password"))
    
    # 代理服务器配置
    HTTP_PROXY: Optional[str] = Field(default=None)
    HTTPS_PROXY: Optional[str] = Field(default=None)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

config = Config()