"""
CodeGPT model configuration
"""
from typing import Dict, Any, Optional
import os

class CodeGPTConfig:
    """Configuration for CodeGPT model"""
   
    def __init__(self):
        self.model_name = "microsoft/CodeGPT-small-py"
        self.tokenizer_name = "microsoft/CodeGPT-small-py"
        self.model_path = os.path.join(os.path.expanduser("~"), ".cache", "ai-model", "codegpt")
       
        # Model parameters
        self.max_length = 1024
        self.vocab_size = 50257
        self.hidden_size = 768
        self.num_layers = 12
        self.num_heads = 12
       
        # Default generation parameters
        self.generation_config = {
            'max_new_tokens': 150,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'repetition_penalty': 1.1,
            'do_sample': True,
            'early_stopping': True,
            'pad_token_id': 50256,
            'eos_token_id': 50256,
            'length_penalty': 1.0,
            'num_return_sequences': 1
        }
       
        # Supported languages
        self.supported_languages = [
            'python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'c#', 
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 
            'html', 'css', 'sql', 'bash', 'powershell'
        ]
       
        # Special tokens
        self.special_tokens = {
            'pad_token': '<pad>',
            'eos_token': '<|endoftext|>',
            'bos_token': '<|endoftext|>',
            'unk_token': '<unk>'
        }
        
        # Language-specific configurations
        self.language_configs = {
            "python": {
                "max_new_tokens": 150,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 2048,
                "comment_style": "#",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".py", ".pyx", ".pyi"]
            },
            "javascript": {
                "max_new_tokens": 120,
                "temperature": 0.7,
                "top_p": 0.9,
                "context_window": 1536,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 2,
                "file_extensions": [".js", ".jsx", ".mjs"]
            },
            "typescript": {
                "max_new_tokens": 120,
                "temperature": 0.7,
                "top_p": 0.9,
                "context_window": 1536,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 2,
                "file_extensions": [".ts", ".tsx"]
            },
            "java": {
                "max_new_tokens": 140,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 1800,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".java"]
            },
            "cpp": {
                "max_new_tokens": 130,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 1800,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".cpp", ".cc", ".cxx", ".c++"]
            },
            "c": {
                "max_new_tokens": 130,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 1800,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".c", ".h"]
            },
            "c#": {
                "max_new_tokens": 130,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 1800,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".cs"]
            },
            "go": {
                "max_new_tokens": 120,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 1600,
                "comment_style": "//",
                "indent_style": "tabs",
                "indent_size": 1,
                "file_extensions": [".go"]
            },
            "rust": {
                "max_new_tokens": 140,
                "temperature": 0.6,
                "top_p": 0.85,
                "context_window": 1800,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".rs"]
            },
            "php": {
                "max_new_tokens": 120,
                "temperature": 0.7,
                "top_p": 0.9,
                "context_window": 1536,
                "comment_style": "//",
                "indent_style": "spaces",
                "indent_size": 4,
                "file_extensions": [".php", ".phtml"]
            },
            "ruby": {
                "max_new_tokens": 120,
                "temperature": 0.7,
                "top_p": 0.9,
                "context_window": 1536,
                "comment_style": "#",
                "indent_style": "spaces",
                "indent_size": 2,
                "file_extensions": [".rb", ".rbw"]
            },
            "html": {
                "max_new_tokens": 100,
                "temperature": 0.5,
                "top_p": 0.9,
                "context_window": 1024,
                "comment_style": "<!-- -->",
                "indent_style": "spaces",
                "indent_size": 2,
                "file_extensions": [".html", ".htm", ".xhtml"]
            },
            "css": {
                "max_new_tokens": 80,
                "temperature": 0.5,
                "top_p": 0.9,
                "context_window": 1024,
                "comment_style": "/* */",
                "indent_style": "spaces",
                "indent_size": 2,
                "file_extensions": [".css", ".scss", ".sass", ".less"]
            },
            "sql": {
                "max_new_tokens": 100,
                "temperature": 0.5,
                "top_p": 0.9,
                "context_window": 1024,
                "comment_style": "--",
                "indent_style": "spaces",
                "indent_size": 2,
                "file_extensions": [".sql"]
            }
        }
   
    def get_model_config(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get complete model configuration, optionally for a specific language"""
        base_config = {
            'model_name': self.model_name,
            'tokenizer_name': self.tokenizer_name,
            'model_path': self.model_path,
            'max_length': self.max_length,
            'vocab_size': self.vocab_size,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'num_heads': self.num_heads,
            'generation_config': self.generation_config.copy(),
            'supported_languages': self.supported_languages,
            'special_tokens': self.special_tokens
        }
        
        # Apply language-specific configuration if provided
        if language and language in self.language_configs:
            lang_config = self.language_configs[language]
            # Update generation config with language-specific settings
            base_config['generation_config'].update({
                'max_new_tokens': lang_config.get('max_new_tokens', self.generation_config['max_new_tokens']),
                'temperature': lang_config.get('temperature', self.generation_config['temperature']),
                'top_p': lang_config.get('top_p', self.generation_config['top_p'])
            })
            base_config['language_config'] = lang_config
        
        return base_config
   
    def get_generation_config(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get generation configuration for a specific language"""
        config = self.generation_config.copy()
        
        if language and language in self.language_configs:
            lang_config = self.language_configs[language]
            config.update({
                'max_new_tokens': lang_config.get('max_new_tokens', config['max_new_tokens']),
                'temperature': lang_config.get('temperature', config['temperature']),
                'top_p': lang_config.get('top_p', config['top_p'])
            })
        
        return config
    
    def get_language_config(self, language: str) -> Dict[str, Any]:
        """Get language-specific configuration"""
        return self.language_configs.get(language, {})
    
    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        for lang, config in self.language_configs.items():
            if file_ext in config.get('file_extensions', []):
                return lang
        
        return None
   
    def update_generation_config(self, **kwargs):
        """Update default generation configuration"""
        self.generation_config.update(kwargs)
        
    def update_language_config(self, language: str, **kwargs):
        """Update language-specific configuration"""
        if language not in self.language_configs:
            self.language_configs[language] = {}
        self.language_configs[language].update(kwargs)
   
    def create_model_directory(self):
        """Create model directory if it doesn't exist"""
        os.makedirs(self.model_path, exist_ok=True)
        
    def is_language_supported(self, language: str) -> bool:
        """Check if a programming language is supported"""
        return language.lower() in [lang.lower() for lang in self.supported_languages]
    
    def add_supported_language(self, language: str, config: Dict[str, Any] = None):
        """Add a new supported language with optional configuration"""
        if language not in self.supported_languages:
            self.supported_languages.append(language)
        
        if config:
            self.language_configs[language] = config
    
    def get_context_window(self, language: str) -> int:
        """Get context window size for a specific language"""
        if language in self.language_configs:
            return self.language_configs[language].get('context_window', self.max_length)
        return self.max_length
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get basic model information"""
        return {
            'name': self.model_name,
            'max_length': self.max_length,
            'vocab_size': self.vocab_size,
            'supported_languages': self.supported_languages,
            'language_configs': list(self.language_configs.keys())
        }

# Create default instance
default_codegpt_config = CodeGPTConfig()