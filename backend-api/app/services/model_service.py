
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Any, Optional
import asyncio
import logging
import os
from pathlib import Path

from ..models.request_models import ProcessedContext
from ..models.response_models import Suggestion
from ..utils.config import get_settings

# Import new configuration classes
from ai_model.model_configs.codegpt_config import CodeGPTConfig
from ai_model.model_configs.codebert_config import CodeBERTConfig

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelService:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._initialized = False
        
        # Initialize new configuration classes
        self.codegpt_config = CodeGPTConfig()
        self.codebert_config = CodeBERTConfig()
        
        # Default model type
        self.default_model_type = 'codegpt'
        
        # Language detection mapping
        self.language_extensions = {
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
            '.rb': 'ruby',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql'
        }
    
    async def initialize(self):
        """Initialize models and tokenizers using new config system"""
        if self._initialized:
            return
        
        try:
            # Initialize CodeGPT model
            await self._initialize_codegpt()
            
            # Initialize CodeBERT model (optional)
            await self._initialize_codebert()
            
            self._initialized = True
            logger.info("Model service initialized successfully with new config system")
            
        except Exception as e:
            logger.error(f"Failed to initialize model service: {e}")
            raise
    
    async def _initialize_codegpt(self):
        """Initialize CodeGPT model using new configuration"""
        try:
            config = self.codegpt_config.get_model_config()
            
            # Create model directories
            self.codegpt_config.create_model_directory()
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                config['tokenizer_name'],
                cache_dir=config['model_path']
            )
            
            # Set special tokens
            for token_name, token_value in config['special_tokens'].items():
                if not hasattr(tokenizer, token_name) or getattr(tokenizer, token_name) is None:
                    setattr(tokenizer, token_name, token_value)
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                config['model_name'],
                cache_dir=config['model_path'],
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            model.to(self.device)
            model.eval()
            
            self.models['codegpt'] = model
            self.tokenizers['codegpt'] = tokenizer
            
            logger.info(f"CodeGPT model loaded: {config['model_name']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CodeGPT: {e}")
            # Fallback to GPT2 if CodeGPT fails
            await self._initialize_fallback_model()
    
    async def _initialize_codebert(self):
        """Initialize CodeBERT model using new configuration"""
        try:
            config = self.codebert_config.get_model_config('code_completion')
            
            # Create model directories
            self.codebert_config.create_model_directory()
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                config['tokenizer_name'],
                cache_dir=config['model_path']
            )
            
            # Set special tokens
            for token_name, token_value in config['special_tokens'].items():
                if not hasattr(tokenizer, token_name) or getattr(tokenizer, token_name) is None:
                    setattr(tokenizer, token_name, token_value)
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                config['model_name'],
                cache_dir=config['model_path'],
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            model.to(self.device)
            model.eval()
            
            self.models['codebert'] = model
            self.tokenizers['codebert'] = tokenizer
            
            logger.info(f"CodeBERT model loaded: {config['model_name']}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize CodeBERT: {e}")
            # CodeBERT is optional, continue without it
    
    async def _initialize_fallback_model(self):
        """Fallback to GPT2 if main models fail"""
        try:
            tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            tokenizer.pad_token = tokenizer.eos_token
            
            model = GPT2LMHeadModel.from_pretrained('gpt2')
            model.to(self.device)
            model.eval()
            
            self.models['gpt2'] = model
            self.tokenizers['gpt2'] = tokenizer
            
            logger.info("Fallback GPT2 model loaded")
            
        except Exception as e:
            logger.error(f"Failed to initialize fallback model: {e}")
            raise
    
    def detect_language(self, context: ProcessedContext) -> Optional[str]:
        """Detect programming language from context"""
        # Try to detect from file extension
        if hasattr(context, 'file_path') and context.file_path:
            ext = Path(context.file_path).suffix.lower()
            detected_lang = self.language_extensions.get(ext)
            if detected_lang:
                return detected_lang
        
        # Try to detect from explicit language field
        if hasattr(context, 'language') and context.language:
            return context.language.lower()
        
        # Fallback language detection based on code content
        code_snippet = context.code_snippet.lower()
        
        # Simple heuristic-based detection
        if 'def ' in code_snippet or 'import ' in code_snippet:
            return 'python'
        elif 'function ' in code_snippet or 'const ' in code_snippet:
            return 'javascript'
        elif 'public class' in code_snippet or 'public static' in code_snippet:
            return 'java'
        elif '#include' in code_snippet or 'int main' in code_snippet:
            return 'cpp'
        
        return 'python'  # Default fallback
    
    async def generate_suggestions(
        self,
        context: ProcessedContext,
        max_suggestions: int = 3,
        temperature: float = None,
        model_type: str = None
    ) -> List[Suggestion]:
        """Generate code suggestions using new configuration system"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Detect language
            language = self.detect_language(context)
            
            # Determine model type
            if model_type is None:
                model_type = self.default_model_type
            
            # Get language-specific configuration
            if model_type == 'codegpt':
                config = self.codegpt_config.get_model_config(language)
                generation_config = self.codegpt_config.get_generation_config(language)
            elif model_type == 'codebert':
                config = self.codebert_config.get_model_config('code_completion')
                generation_config = self.codebert_config.get_generation_config('code_completion')
            else:
                # Fallback configuration
                config = {'model_name': 'gpt2'}
                generation_config = {
                    'max_new_tokens': 100,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'do_sample': True,
                    'repetition_penalty': 1.1
                }
            
            # Override temperature if provided
            if temperature is not None:
                generation_config['temperature'] = temperature
            
            # Select model and tokenizer
            model = self.models.get(model_type) or self.models.get('gpt2')
            tokenizer = self.tokenizers.get(model_type) or self.tokenizers.get('gpt2')
            
            if not model or not tokenizer:
                logger.error(f"Model or tokenizer not found for {model_type}")
                return self._get_fallback_suggestions(context, language)
            
            # Get context window size
            max_length = self.codegpt_config.get_context_window(language) if model_type == 'codegpt' else 512
            
            # Tokenize input
            encoded = tokenizer(
                context.code_snippet,
                max_length=max_length,
                truncation=True,
                padding=True,
                return_tensors='pt'
            )
            
            input_ids = encoded['input_ids'].to(self.device)
            attention_mask = encoded['attention_mask'].to(self.device)
            
            # Generate suggestions
            with torch.no_grad():
                outputs = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=generation_config.get('max_new_tokens', 100),
                    num_return_sequences=max_suggestions,
                    temperature=generation_config.get('temperature', 0.7),
                    top_p=generation_config.get('top_p', 0.9),
                    top_k=generation_config.get('top_k', 50),
                    do_sample=generation_config.get('do_sample', True),
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    repetition_penalty=generation_config.get('repetition_penalty', 1.1),
                    length_penalty=generation_config.get('length_penalty', 1.0),
                    early_stopping=generation_config.get('early_stopping', True)
                )
            
            # Decode and format suggestions
            suggestions = []
            for i, output in enumerate(outputs):
                # Extract only new tokens
                new_tokens = output[len(input_ids[0]):]
                suggestion_text = tokenizer.decode(
                    new_tokens,
                    skip_special_tokens=True
                ).strip()
                
                if suggestion_text:
                    # Apply language-specific formatting
                    formatted_text = self._format_suggestion(suggestion_text, language)
                    
                    suggestions.append(Suggestion(
                        text=formatted_text,
                        confidence=0.95 - (i * 0.05),  # Higher confidence for better models
                        type="multi-line" if '\n' in formatted_text else "single-line",
                        description=f"AI-generated {language} suggestion {i + 1}",
                        cursorOffset=len(formatted_text),
                        languageSpecific=True,
                        formattingApplied=True
                    ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._get_fallback_suggestions(context, language)
    
    def _format_suggestion(self, text: str, language: str) -> str:
        """Apply language-specific formatting to suggestions"""
        if language == 'python':
            # Ensure proper Python indentation
            lines = text.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip():
                    # Add 4 spaces if line doesn't start with whitespace
                    if not line.startswith(' ') and not line.startswith('\t'):
                        formatted_lines.append('    ' + line)
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            return '\n'.join(formatted_lines)
        
        elif language in ['javascript', 'typescript']:
            # Ensure proper JS/TS indentation (2 spaces)
            lines = text.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip():
                    if not line.startswith(' ') and not line.startswith('\t'):
                        formatted_lines.append('  ' + line)
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            return '\n'.join(formatted_lines)
        
        elif language == 'go':
            # Go uses tabs
            lines = text.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip():
                    if not line.startswith('\t') and not line.startswith(' '):
                        formatted_lines.append('\t' + line)
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            return '\n'.join(formatted_lines)
        
        # Default formatting
        return text
    
    def _get_fallback_suggestions(self, context: ProcessedContext, language: str = 'python') -> List[Suggestion]:
        """Enhanced fallback suggestions based on language"""
        fallback_suggestions = {
            'python': [
                Suggestion(
                    text="pass",
                    confidence=0.5,
                    type="single-line",
                    description="Python placeholder statement",
                    cursorOffset=4,
                    languageSpecific=True
                ),
                Suggestion(
                    text="# TODO: Implement this",
                    confidence=0.4,
                    type="single-line",
                    description="Python TODO comment",
                    cursorOffset=21,
                    languageSpecific=True
                )
            ],
            'javascript': [
                Suggestion(
                    text="// TODO: Implement this",
                    confidence=0.5,
                    type="single-line",
                    description="JavaScript TODO comment",
                    cursorOffset=23,
                    languageSpecific=True
                ),
                Suggestion(
                    text="console.log('TODO');",
                    confidence=0.4,
                    type="single-line",
                    description="JavaScript console log",
                    cursorOffset=20,
                    languageSpecific=True
                )
            ],
            'java': [
                Suggestion(
                    text="// TODO: Implement this method",
                    confidence=0.5,
                    type="single-line",
                    description="Java TODO comment",
                    cursorOffset=30,
                    languageSpecific=True
                )
            ]
        }
        
        return fallback_suggestions.get(language, fallback_suggestions['python'])
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        return self.codegpt_config.supported_languages
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported"""
        return self.codegpt_config.is_language_supported(language)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            'loaded_models': list(self.models.keys()),
            'default_model': self.default_model_type,
            'supported_languages': self.get_supported_languages(),
            'device': str(self.device),
            'codegpt_config': self.codegpt_config.get_model_info(),
            'codebert_config': self.codebert_config.get_model_info()
        }
    
    def update_model_config(self, model_type: str, language: str = None, **kwargs):
        """Update model configuration dynamically"""
        if model_type == 'codegpt':
            if language:
                self.codegpt_config.update_language_config(language, **kwargs)
            else:
                self.codegpt_config.update_generation_config(**kwargs)
        elif model_type == 'codebert':
            if 'task' in kwargs:
                self.codebert_config.update_task_config(kwargs['task'], **kwargs)