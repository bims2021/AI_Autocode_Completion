"""
Configuration management for AI Model package
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class ModelConfig:
    """Configuration for individual models"""
    name: str
    model_path: str
    tokenizer_path: str
    max_length: int = 2048
    supported_languages: List[str] = None
    generation_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = ["python"]
        if self.generation_config is None:
            self.generation_config = {
                "max_new_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50,
                "do_sample": True,
                "pad_token_id": 50256,
                "eos_token_id": 50256,
            }

@dataclass
class ServerConfig:
    """Configuration for HTTP server"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "INFO"
    cors_enabled: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    timeout: int = 30
    workers: int = 1

@dataclass
class CacheConfig:
    """Configuration for caching"""
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 3600  # 1 hour
    backend: str = "memory"  # memory, redis, etc.

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class AIModelConfig:
    """Main configuration class"""
    default_model: str = "codegpt"
    models: Dict[str, ModelConfig] = None
    server: ServerConfig = None
    cache: CacheConfig = None
    logging: LoggingConfig = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = {}
        if self.server is None:
            self.server = ServerConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.logging is None:
            self.logging = LoggingConfig()

class ConfigManager:
    """Configuration manager for AI Model package"""
    
    DEFAULT_CONFIG_PATHS = [
        "ai_model_config.yaml",
        "ai_model_config.json",
        "~/.ai_model/config.yaml",
        "~/.ai_model/config.json",
        "/etc/ai_model/config.yaml",
        "/etc/ai_model/config.json",
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> AIModelConfig:
        """Load configuration from file or create default"""
        if self.config_path:
            config_paths = [self.config_path]
        else:
            config_paths = self.DEFAULT_CONFIG_PATHS
        
        for path in config_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                try:
                    return self._load_config_file(expanded_path)
                except Exception as e:
                    print(f"Warning: Failed to load config from {expanded_path}: {e}")
                    continue
        
        # Return default configuration with built-in models
        return self._create_default_config()
    
    def _load_config_file(self, path: Path) -> AIModelConfig:
        """Load configuration from a specific file"""
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return self._parse_config_data(data)
    
    def _parse_config_data(self, data: Dict[str, Any]) -> AIModelConfig:
        """Parse configuration data into config objects"""
        config = AIModelConfig()
        
        # Parse main config
        config.default_model = data.get('default_model', 'codegpt')
        
        # Parse models
        if 'models' in data:
            for model_name, model_data in data['models'].items():
                config.models[model_name] = ModelConfig(
                    name=model_name,
                    **model_data
                )
        
        # Parse server config
        if 'server' in data:
            config.server = ServerConfig(**data['server'])
        
        # Parse cache config
        if 'cache' in data:
            config.cache = CacheConfig(**data['cache'])
        
        # Parse logging config
        if 'logging' in data:
            config.logging = LoggingConfig(**data['logging'])
        
        return config
    
    def _create_default_config(self) -> AIModelConfig:
        """Create default configuration with built-in models"""
        config = AIModelConfig()
        
        # Add default models
        config.models['codegpt'] = ModelConfig(
            name='codegpt',
            model_path='microsoft/CodeGPT-small-py',
            tokenizer_path='microsoft/CodeGPT-small-py',
            max_length=1024,
            supported_languages=['python', 'javascript', 'typescript', 'java', 'c++'],
            generation_config={
                "max_new_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50,
                "do_sample": True,
                "pad_token_id": 50256,
                "eos_token_id": 50256,
            }
        )
        
        config.models['codebert'] = ModelConfig(
            name='codebert',
            model_path='microsoft/codebert-base',
            tokenizer_path='microsoft/codebert-base',
            max_length=512,
            supported_languages=['python', 'java', 'javascript', 'php', 'ruby', 'go'],
            generation_config={
                "max_new_tokens": 50,
                "temperature": 0.5,
                "top_p": 0.95,
                "top_k": 40,
                "do_sample": True,
            }
        )
        
        return config
    
    def save_config(self, path: Optional[str] = None):
        """Save current configuration to file"""
        if not path:
            path = self.config_path or "ai_model_config.yaml"
        
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dict
        config_dict = asdict(self.config)
        
        # Save as YAML
        with open(path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.config.models.get(model_name)
    
    def add_model_config(self, model_config: ModelConfig):
        """Add or update model configuration"""
        self.config.models[model_config.name] = model_config
    
    def get_server_config(self) -> ServerConfig:
        """Get server configuration"""
        return self.config.server
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self.config.cache
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        return self.config.logging
    
    def update_from_env(self):
        """Update configuration from environment variables"""
        # Server configuration
        if os.getenv('AI_MODEL_SERVER_HOST'):
            self.config.server.host = os.getenv('AI_MODEL_SERVER_HOST')
        if os.getenv('AI_MODEL_SERVER_PORT'):
            self.config.server.port = int(os.getenv('AI_MODEL_SERVER_PORT'))
        
        # Default model
        if os.getenv('AI_MODEL_DEFAULT'):
            self.config.default_model = os.getenv('AI_MODEL_DEFAULT')
        
        # Logging
        if os.getenv('AI_MODEL_LOG_LEVEL'):
            self.config.logging.level = os.getenv('AI_MODEL_LOG_LEVEL')
        
        # Cache
        if os.getenv('AI_MODEL_CACHE_ENABLED'):
            self.config.cache.enabled = os.getenv('AI_MODEL_CACHE_ENABLED').lower() == 'true'
