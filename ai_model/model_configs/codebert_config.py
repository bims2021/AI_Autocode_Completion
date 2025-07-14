"""
CodeBERT model configuration
"""
from typing import Dict, Any
import os

class CodeBERTConfig:
    """Configuration for CodeBERT model"""
   
    def __init__(self):
        self.model_name = "microsoft/codebert-base"
        self.tokenizer_name = "microsoft/codebert-base"
        self.model_path = os.path.join(os.path.expanduser("~"), ".cache", "ai-model", "codebert")
       
        # Model parameters
        self.max_length = 512
        self.vocab_size = 50265
        self.hidden_size = 768
        self.num_layers = 12
        self.num_heads = 12
        self.intermediate_size = 3072
       
        # Task-specific configurations
        self.task_configs = {
            'code_completion': {
                'max_new_tokens': 100,
                'temperature': 0.8,
                'top_p': 0.95,
                'top_k': 40,
                'repetition_penalty': 1.05,
                'do_sample': True,
                'pad_token_id': 1,
                'eos_token_id': 2,
                'length_penalty': 1.0,
                'early_stopping': True,
                'num_return_sequences': 1
            },
            'code_search': {
                'max_length': 256,
                'pooling_mode': 'mean',
                'temperature': 0.1,
                'top_p': 0.9
            },
            'code_documentation': {
                'max_new_tokens': 200,
                'temperature': 0.6,
                'top_p': 0.9,
                'repetition_penalty': 1.2,
                'do_sample': True
            },
            'code_analysis': {
                'max_new_tokens': 100,
                'temperature': 0.1,
                'top_p': 0.95,
                'focus': 'semantic_analysis'
            },
            'bug_detection': {
                'max_new_tokens': 80,
                'temperature': 0.2,
                'top_p': 0.9,
                'focus': 'pattern_recognition'
            }
        }
       
        # Supported languages
        self.supported_languages = [
            'python', 'java', 'javascript', 'php', 'ruby', 'go', 'c', 'cpp', 'c#'
        ]
       
        # Special tokens
        self.special_tokens = {
            'cls_token': '<s>',
            'sep_token': '</s>',
            'pad_token': '<pad>',
            'unk_token': '<unk>',
            'mask_token': '<mask>'
        }
   
    def get_model_config(self, task: str = 'code_completion') -> Dict[str, Any]:
        """Get model configuration for specific task"""
        base_config = {
            'model_name': self.model_name,
            'tokenizer_name': self.tokenizer_name,
            'model_path': self.model_path,
            'max_length': self.max_length,
            'vocab_size': self.vocab_size,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'num_heads': self.num_heads,
            'intermediate_size': self.intermediate_size,
            'supported_languages': self.supported_languages,
            'special_tokens': self.special_tokens
        }
       
        if task in self.task_configs:
            base_config['task_config'] = self.task_configs[task]
       
        return base_config
   
    def update_task_config(self, task: str, **kwargs):
        """Update task-specific configuration"""
        if task not in self.task_configs:
            self.task_configs[task] = {}
        self.task_configs[task].update(kwargs)
   
    def create_model_directory(self):
        """Create model directory if it doesn't exist"""
        os.makedirs(self.model_path, exist_ok=True)
        
    def get_generation_config(self, task: str = 'code_completion') -> Dict[str, Any]:
        """Get generation configuration for specific task"""
        if task in self.task_configs:
            return self.task_configs[task]
        return self.task_configs['code_completion']  # Default fallback
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a programming language is supported"""
        return language.lower() in [lang.lower() for lang in self.supported_languages]
    
    def add_supported_language(self, language: str):
        """Add a new supported language"""
        if language not in self.supported_languages:
            self.supported_languages.append(language)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get basic model information"""
        return {
            'name': self.model_name,
            'max_length': self.max_length,
            'vocab_size': self.vocab_size,
            'supported_languages': self.supported_languages,
            'available_tasks': list(self.task_configs.keys())
        }

# Create default instance
default_codebert_config = CodeBERTConfig()
