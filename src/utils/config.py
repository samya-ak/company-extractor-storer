"""
Configuration utilities for the company extraction system.
"""
import os
from typing import Optional
from dotenv import load_dotenv

from models.company import DatabaseConfig


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration with optional environment file."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return api_key
    
    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration from environment."""
        return DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "company_data"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
    
    @property
    def model_name(self) -> str:
        """Get the model name to use for extraction."""
        return os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    
    @property
    def temperature(self) -> float:
        """Get the temperature setting for the model."""
        return float(os.getenv("TEMPERATURE", "0.1"))
    
    @property
    def max_tokens(self) -> int:
        """Get the maximum tokens for model responses."""
        return int(os.getenv("MAX_TOKENS", "2000"))
    
    @property
    def chunk_size(self) -> int:
        """Get the chunk size for text splitting."""
        return int(os.getenv("CHUNK_SIZE", "1000"))
    
    @property
    def chunk_overlap(self) -> int:
        """Get the chunk overlap for text splitting."""
        return int(os.getenv("CHUNK_OVERLAP", "200"))
    
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        try:
            # Check OpenAI API key
            _ = self.openai_api_key
            
            # Check database configuration
            db_config = self.database_config
            if not db_config.database or not db_config.username:
                raise ValueError("Database name and username are required")
            
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def print_config(self):
        """Print current configuration (without sensitive data)."""
        print("Current Configuration:")
        print(f"  Model: {self.model_name}")
        print(f"  Temperature: {self.temperature}")
        print(f"  Max Tokens: {self.max_tokens}")
        print(f"  Chunk Size: {self.chunk_size}")
        print(f"  Chunk Overlap: {self.chunk_overlap}")
        print(f"  Database Host: {self.database_config.host}")
        print(f"  Database Port: {self.database_config.port}")
        print(f"  Database Name: {self.database_config.database}")
        print(f"  Database User: {self.database_config.username}")
        print("  Database Password: [HIDDEN]")
        print(f"  OpenAI API Key: [HIDDEN]")


def create_sample_env_file():
    """Create a sample .env file with required configuration."""
    env_content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=company_data
DB_USER=postgres
DB_PASSWORD=your_password_here

# Model Configuration
MODEL_NAME=gpt-3.5-turbo
TEMPERATURE=0.1
MAX_TOKENS=2000

# Text Processing Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
    
    with open(".env.example", "w") as f:
        f.write(env_content)
    
    print("Sample .env file created as .env.example")
    print("Please copy it to .env and fill in your actual values") 