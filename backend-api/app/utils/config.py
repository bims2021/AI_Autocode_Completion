from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
import os
from ai_model.model_configs.codebert_config import CodeBERTConfig
from ai_model.model_configs.codegpt_config import CodeGPTConfig

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # Model settings - Updated to use new config system
    MODEL_PATH: str = "gpt2"
    MAX_TOKENS: int = 1024
    
    # Language-specific settings
    DEFAULT_LANGUAGE: str = "python"
    ENABLE_LANGUAGE_DETECTION: bool = True
    
    # CodeGPT specific settings
    CODEGPT_MODEL_NAME: str = "microsoft/CodeGPT-small-py"
    CODEGPT_MAX_LENGTH: int = 1024
    CODEGPT_TEMPERATURE: float = 0.7
    CODEGPT_TOP_P: float = 0.9
    CODEGPT_TOP_K: int = 50
    
    # CodeBERT specific settings
    CODEBERT_MODEL_NAME: str = "microsoft/codebert-base"
    CODEBERT_MAX_LENGTH: int = 512
    CODEBERT_TEMPERATURE: float = 0.8
    CODEBERT_TOP_P: float = 0.95
    
    # Context processing settings
    MAX_CONTEXT_LINES: int = 50
    ENABLE_CONTEXT_CACHING: bool = True
    CONTEXT_CACHE_TTL: int = 3600  # 1 hour
    
    # Advanced model settings
    ENABLE_BATCH_PROCESSING: bool = True
    BATCH_SIZE: int = 4
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # Language support settings
    SUPPORTED_LANGUAGES: List[str] = [
        'python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'c#', 
        'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 
        'html', 'css', 'sql', 'bash', 'powershell'
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class ModelConfigManager:
    """Manager for handling model configurations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._codegpt_config = None
        self._codebert_config = None
        
    @property
    def codegpt_config(self) -> CodeGPTConfig:
        """Get CodeGPT configuration instance"""
        if self._codegpt_config is None:
            self._codegpt_config = CodeGPTConfig()
            # Apply settings overrides
            self._apply_codegpt_settings()
        return self._codegpt_config
    
    @property
    def codebert_config(self) -> CodeBERTConfig:
        """Get CodeBERT configuration instance"""
        if self._codebert_config is None:
            self._codebert_config = CodeBERTConfig()
            # Apply settings overrides
            self._apply_codebert_settings()
        return self._codebert_config
    
    def _apply_codegpt_settings(self):
        """Apply settings to CodeGPT configuration"""
        # Update model name and path
        self._codegpt_config.model_name = self.settings.CODEGPT_MODEL_NAME
        self._codegpt_config.max_length = self.settings.CODEGPT_MAX_LENGTH
        
        # Update default generation config
        self._codegpt_config.update_generation_config(
            temperature=self.settings.CODEGPT_TEMPERATURE,
            top_p=self.settings.CODEGPT_TOP_P,
            top_k=self.settings.CODEGPT_TOP_K
        )
        
        # Update supported languages
        for lang in self.settings.SUPPORTED_LANGUAGES:
            if not self._codegpt_config.is_language_supported(lang):
                self._codegpt_config.add_supported_language(lang)
    
    def _apply_codebert_settings(self):
        """Apply settings to CodeBERT configuration"""
        # Update model name and path
        self._codebert_config.model_name = self.settings.CODEBERT_MODEL_NAME
        self._codebert_config.max_length = self.settings.CODEBERT_MAX_LENGTH
        
        # Update task configurations
        self._codebert_config.update_task_config(
            'code_completion',
            temperature=self.settings.CODEBERT_TEMPERATURE,
            top_p=self.settings.CODEBERT_TOP_P
        )
        
        # Update supported languages
        for lang in self.settings.SUPPORTED_LANGUAGES:
            if not self._codebert_config.is_language_supported(lang):
                self._codebert_config.add_supported_language(lang)
    
    def get_model_config(self, model_type: str, language: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
        """Get model configuration for specific model type and language"""
        if model_type.lower() == 'codegpt':
            return self.codegpt_config.get_model_config(language)
        elif model_type.lower() == 'codebert':
            return self.codebert_config.get_model_config(task or 'code_completion')
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def get_generation_config(self, model_type: str, language: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
        """Get generation configuration for specific model type and language"""
        if model_type.lower() == 'codegpt':
            return self.codegpt_config.get_generation_config(language)
        elif model_type.lower() == 'codebert':
            return self.codebert_config.get_generation_config(task or 'code_completion')
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def is_language_supported(self, language: str, model_type: str = 'codegpt') -> bool:
        """Check if language is supported by the specified model"""
        if model_type.lower() == 'codegpt':
            return self.codegpt_config.is_language_supported(language)
        elif model_type.lower() == 'codebert':
            return self.codebert_config.is_language_supported(language)
        else:
            return False
    
    def get_context_window_size(self, language: str, model_type: str = 'codegpt') -> int:
        """Get context window size for language and model"""
        if model_type.lower() == 'codegpt':
            return self.codegpt_config.get_context_window(language)
        elif model_type.lower() == 'codebert':
            return self.codebert_config.max_length
        else:
            return self.settings.MAX_TOKENS
    
    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect language from file path"""
        return self.codegpt_config.detect_language_from_file(file_path)
    
    def get_language_config(self, language: str) -> Dict[str, Any]:
        """Get language-specific configuration"""
        return self.codegpt_config.get_language_config(language)
    
    def validate_request_config(self, language: str, model_type: str, max_tokens: int) -> Dict[str, Any]:
        """Validate and adjust request configuration"""
        errors = []
        warnings = []
        
        # Validate language support
        if not self.is_language_supported(language, model_type):
            warnings.append(f"Language '{language}' may not be fully supported for {model_type}")
        
        # Validate max tokens
        context_window = self.get_context_window_size(language, model_type)
        if max_tokens > context_window:
            warnings.append(f"Requested max_tokens ({max_tokens}) exceeds context window ({context_window})")
            max_tokens = context_window
        
        # Get generation config
        gen_config = self.get_generation_config(model_type, language)
        
        return {
            'validated_config': {
                'language': language,
                'model_type': model_type,
                'max_tokens': max_tokens,
                'generation_config': gen_config
            },
            'errors': errors,
            'warnings': warnings
        }
    
    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get model information"""
        if model_type.lower() == 'codegpt':
            return self.codegpt_config.get_model_info()
        elif model_type.lower() == 'codebert':
            return self.codebert_config.get_model_info()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

# Global settings instance
_settings = None
_config_manager = None

def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_config_manager() -> ModelConfigManager:
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ModelConfigManager(get_settings())
    return _config_manager

def reset_config():
    """Reset global configuration instances (useful for testing)"""
    global _settings, _config_manager
    _settings = None
    _config_manager = None

# Convenience functions
def get_model_config(model_type: str, language: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get model configuration"""
    return get_config_manager().get_model_config(model_type, language, task)

def get_generation_config(model_type: str, language: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get generation configuration"""
    return get_config_manager().get_generation_config(model_type, language, task)

def is_language_supported(language: str, model_type: str = 'codegpt') -> bool:
    """Convenience function to check language support"""
    return get_config_manager().is_language_supported(language, model_type)

def detect_language_from_file(file_path: str) -> Optional[str]:
    """Convenience function to detect language from file"""
    return get_config_manager().detect_language_from_file(file_path)