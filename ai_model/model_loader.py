import os
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    GPT2LMHeadModel, GPT2Tokenizer,
    AutoModel, RobertaTokenizer
)
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from .model_configs.codegpt_config import CodeGPTConfig
from .model_configs.codebert_config import CodeBERTConfig

logger = logging.getLogger(__name__)

class ModelLoader:
    """
    Universal model loader for different AI models
    """
    
    def __init__(self):
        self.loaded_models = {}
        self.model_configs = {
            'codegpt': CodeGPTConfig(),
            'codebert': CodeBERTConfig(),
            'gpt2': {'model_name': 'gpt2', 'tokenizer_name': 'gpt2'},
            'codet5': {'model_name': 'Salesforce/codet5-base', 'tokenizer_name': 'Salesforce/codet5-base'}
        }
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Model loader initialized with device: {self.device}")
    
    def load_model(self, model_name: str, model_path: Optional[str] = None, language: Optional[str] = None) -> Tuple[Any, Any]:
        """
        Load a model and its tokenizer
        
        Args:
            model_name: Name of the model to load
            model_path: Optional custom path to model
            language: Optional language for language-specific configuration
            
        Returns:
            Tuple of (model, tokenizer)
        """
        # Create cache key that includes language for language-specific models
        cache_key = f"{model_name}_{language}" if language and model_name in ['codegpt', 'codebert'] else model_name
        
        if cache_key in self.loaded_models:
            logger.info(f"Model {cache_key} already loaded")
            return self.loaded_models[cache_key]
        
        try:
            if model_name == 'codegpt':
                model, tokenizer = self._load_codegpt(model_path, language)
            elif model_name == 'codebert':
                model, tokenizer = self._load_codebert(model_path, language)
            elif model_name == 'gpt2':
                model, tokenizer = self._load_gpt2(model_path)
            elif model_name == 'codet5':
                model, tokenizer = self._load_codet5(model_path)
            else:
                raise ValueError(f"Unsupported model: {model_name}")
            
            # Move model to device
            model.to(self.device)
            model.eval()
            
            # Cache loaded model
            self.loaded_models[cache_key] = (model, tokenizer)
            
            logger.info(f"Successfully loaded model: {cache_key}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def _load_codegpt(self, model_path: Optional[str] = None, language: Optional[str] = None) -> Tuple[Any, Any]:
        """Load CodeGPT model"""
        config = self.model_configs['codegpt']
        
        # Get model configuration (with language-specific settings if provided)
        model_config = config.get_model_config(language)
        
        # Use provided path or config path
        path = model_path or config.model_path
        
        # Create model directory if it doesn't exist
        config.create_model_directory()
        
        try:
            if not os.path.exists(path) or not os.listdir(path):
                logger.info(f"Downloading CodeGPT model to {path}")
                # Download from HuggingFace
                model = AutoModelForCausalLM.from_pretrained(
                    config.model_name,
                    cache_dir=path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    config.tokenizer_name,
                    cache_dir=path,
                    trust_remote_code=True
                )
                
                # Save model locally
                model.save_pretrained(path)
                tokenizer.save_pretrained(path)
            else:
                logger.info(f"Loading CodeGPT model from {path}")
                model = AutoModelForCausalLM.from_pretrained(
                    path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    path,
                    trust_remote_code=True
                )
        except Exception as e:
            logger.warning(f"Failed to load from local path, downloading from HuggingFace: {e}")
            model = AutoModelForCausalLM.from_pretrained(
                config.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True
            )
            tokenizer = AutoTokenizer.from_pretrained(
                config.tokenizer_name,
                trust_remote_code=True
            )
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Set special tokens from config
        special_tokens = config.special_tokens
        if special_tokens.get('pad_token') and not tokenizer.pad_token:
            tokenizer.pad_token = special_tokens['pad_token']
        
        return model, tokenizer
    
    def _load_codebert(self, model_path: Optional[str] = None, language: Optional[str] = None) -> Tuple[Any, Any]:
        """Load CodeBERT model"""
        config = self.model_configs['codebert']
        
        # Get model configuration (with language-specific settings if provided)
        model_config = config.get_model_config(language)
        
        # Use provided path or config path
        path = model_path or config.model_path
        
        # Create model directory if it doesn't exist
        config.create_model_directory()
        
        try:
            if not os.path.exists(path) or not os.listdir(path):
                logger.info(f"Downloading CodeBERT model to {path}")
                # Use AutoModel instead of CodeBERTModel for better compatibility
                model = AutoModel.from_pretrained(
                    config.model_name,
                    cache_dir=path,
                    trust_remote_code=True
                )
                tokenizer = RobertaTokenizer.from_pretrained(
                    config.tokenizer_name,
                    cache_dir=path,
                    trust_remote_code=True
                )
                
                # Save model locally
                model.save_pretrained(path)
                tokenizer.save_pretrained(path)
            else:
                logger.info(f"Loading CodeBERT model from {path}")
                model = AutoModel.from_pretrained(
                    path,
                    trust_remote_code=True
                )
                tokenizer = RobertaTokenizer.from_pretrained(
                    path,
                    trust_remote_code=True
                )
        except Exception as e:
            logger.warning(f"Failed to load from local path, downloading from HuggingFace: {e}")
            model = AutoModel.from_pretrained(
                config.model_name,
                trust_remote_code=True
            )
            tokenizer = RobertaTokenizer.from_pretrained(
                config.tokenizer_name,
                trust_remote_code=True
            )
        
        # Set special tokens from config
        special_tokens = config.special_tokens
        if special_tokens.get('pad_token') and not tokenizer.pad_token:
            tokenizer.pad_token = special_tokens['pad_token']
        
        return model, tokenizer
    
    def _load_gpt2(self, model_path: Optional[str] = None) -> Tuple[Any, Any]:
        """Load GPT-2 model"""
        config = self.model_configs['gpt2']
        path = model_path or config['model_name']
        
        model = GPT2LMHeadModel.from_pretrained(path)
        tokenizer = GPT2Tokenizer.from_pretrained(path)
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        return model, tokenizer
    
    def _load_codet5(self, model_path: Optional[str] = None) -> Tuple[Any, Any]:
        """Load CodeT5 model"""
        config = self.model_configs['codet5']
        path = model_path or config['model_name']
        
        model = AutoModelForCausalLM.from_pretrained(path)
        tokenizer = AutoTokenizer.from_pretrained(path)
        
        return model, tokenizer
    
    def get_model_config(self, model_name: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Get model configuration"""
        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} not supported")
        
        config = self.model_configs[model_name]
        
        # For new config classes, use their methods
        if hasattr(config, 'get_model_config'):
            return config.get_model_config(language)
        else:
            return config
    
    def get_generation_config(self, model_name: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Get generation configuration for a model"""
        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} not supported")
        
        config = self.model_configs[model_name]
        
        # For new config classes, use their methods
        if hasattr(config, 'get_generation_config'):
            return config.get_generation_config(language)
        elif hasattr(config, 'generation_config'):
            return config.generation_config
        else:
            return {}
    
    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        # Try CodeGPT first (has more language support)
        codegpt_config = self.model_configs['codegpt']
        if hasattr(codegpt_config, 'detect_language_from_file'):
            lang = codegpt_config.detect_language_from_file(file_path)
            if lang:
                return lang
        
        # Fallback to CodeBERT
        codebert_config = self.model_configs['codebert']
        if hasattr(codebert_config, 'detect_language_from_file'):
            return codebert_config.detect_language_from_file(file_path)
        
        # Simple fallback detection
        ext = os.path.splitext(file_path)[1].lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'c#',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby'
        }
        return lang_map.get(ext)
    
    def get_model_info(self, model_name: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a loaded model"""
        cache_key = f"{model_name}_{language}" if language and model_name in ['codegpt', 'codebert'] else model_name
        
        if cache_key not in self.loaded_models:
            raise ValueError(f"Model {cache_key} not loaded")
        
        model, tokenizer = self.loaded_models[cache_key]
        
        info = {
            'model_name': model_name,
            'language': language,
            'cache_key': cache_key,
            'model_type': type(model).__name__,
            'tokenizer_type': type(tokenizer).__name__,
            'vocab_size': tokenizer.vocab_size,
            'max_length': getattr(tokenizer, 'model_max_length', 'unknown'),
            'device': str(model.device) if hasattr(model, 'device') else 'unknown',
            'parameters': sum(p.numel() for p in model.parameters()) if hasattr(model, 'parameters') else 0
        }
        
        # Add config-specific info
        if model_name in self.model_configs:
            config = self.model_configs[model_name]
            if hasattr(config, 'get_model_info'):
                config_info = config.get_model_info()
                info.update(config_info)
        
        return info
    
    def unload_model(self, model_name: str, language: Optional[str] = None):
        """Unload a model from memory"""
        cache_key = f"{model_name}_{language}" if language and model_name in ['codegpt', 'codebert'] else model_name
        
        if cache_key in self.loaded_models:
            del self.loaded_models[cache_key]
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info(f"Unloaded model: {cache_key}")
    
    def list_loaded_models(self) -> list:
        """List all currently loaded models"""
        return list(self.loaded_models.keys())
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        memory_info = {}
        
        if torch.cuda.is_available():
            memory_info['cuda_allocated'] = torch.cuda.memory_allocated() / 1024**2  # MB
            memory_info['cuda_reserved'] = torch.cuda.memory_reserved() / 1024**2  # MB
            memory_info['cuda_max_allocated'] = torch.cuda.max_memory_allocated() / 1024**2  # MB
        
        return memory_info
    
    def is_language_supported(self, model_name: str, language: str) -> bool:
        """Check if a language is supported by a model"""
        if model_name not in self.model_configs:
            return False
        
        config = self.model_configs[model_name]
        if hasattr(config, 'is_language_supported'):
            return config.is_language_supported(language)
        
        # Fallback check
        if hasattr(config, 'supported_languages'):
            return language in config.supported_languages
        
        return False