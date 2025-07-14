"""
Code tokenization module for CodeGPT and CodeBERT models
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from transformers import AutoTokenizer, PreTrainedTokenizer
import logging

# Import config classes
from .codegpt_config_enhanced import CodeGPTConfig, default_codegpt_config
from .codebert_config_clean import CodeBERTConfig, default_codebert_config

logger = logging.getLogger(__name__)

class CodeTokenizer:
    """Universal tokenizer for code models"""
    
    def __init__(self, model_type: str = "codegpt", config: Optional[Union[CodeGPTConfig, CodeBERTConfig]] = None):
        """
        Initialize tokenizer
        
        Args:
            model_type: Type of model ("codegpt" or "codebert")
            config: Model configuration object
        """
        self.model_type = model_type.lower()
        
        # Set default config if none provided
        if config is None:
            if self.model_type == "codegpt":
                self.config = default_codegpt_config
            elif self.model_type == "codebert":
                self.config = default_codebert_config
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        else:
            self.config = config
            
        self.tokenizer = None
        self._load_tokenizer()
        
        # Language-specific patterns for better tokenization
        self.language_patterns = {
            'python': {
                'string_patterns': [r'""".*?"""', r"'''.*?'''", r'".*?"', r"'.*?'"],
                'comment_patterns': [r'#.*?$'],
                'function_patterns': [r'def\s+\w+\s*\(', r'class\s+\w+\s*\('],
                'indent_token': '<INDENT>',
                'dedent_token': '<DEDENT>'
            },
            'java': {
                'string_patterns': [r'".*?"'],
                'comment_patterns': [r'//.*?$', r'/\*.*?\*/'],
                'function_patterns': [r'public\s+\w+\s+\w+\s*\(', r'private\s+\w+\s+\w+\s*\('],
                'block_start': '<BLOCK_START>',
                'block_end': '<BLOCK_END>'
            },
            'javascript': {
                'string_patterns': [r'".*?"', r"'.*?'", r'`.*?`'],
                'comment_patterns': [r'//.*?$', r'/\*.*?\*/'],
                'function_patterns': [r'function\s+\w+\s*\(', r'\w+\s*=\s*\(.*?\)\s*=>'],
                'arrow_function': '<ARROW_FUNC>'
            }
        }
    
    def _load_tokenizer(self):
        """Load the appropriate tokenizer"""
        try:
            tokenizer_name = self.config.tokenizer_name
            
            # Try to load from local cache first
            if os.path.exists(self.config.model_path):
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_path)
                    logger.info(f"Loaded tokenizer from local cache: {self.config.model_path}")
                except Exception as e:
                    logger.warning(f"Failed to load from cache: {e}")
            
            # Fallback to downloading from HuggingFace
            if self.tokenizer is None:
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
                logger.info(f"Loaded tokenizer from HuggingFace: {tokenizer_name}")
                
                # Cache the tokenizer
                self.config.create_model_directory()
                self.tokenizer.save_pretrained(self.config.model_path)
                logger.info(f"Cached tokenizer to: {self.config.model_path}")
            
            # Add special tokens if they don't exist
            self._add_special_tokens()
            
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise
    
    def _add_special_tokens(self):
        """Add model-specific special tokens"""
        special_tokens = self.config.special_tokens
        tokens_to_add = []
        
        for token_type, token_value in special_tokens.items():
            if not hasattr(self.tokenizer, token_type) or getattr(self.tokenizer, token_type) is None:
                tokens_to_add.append(token_value)
        
        # Add language-specific tokens
        for lang_patterns in self.language_patterns.values():
            for key, value in lang_patterns.items():
                if key.endswith('_token') and value not in tokens_to_add:
                    tokens_to_add.append(value)
        
        if tokens_to_add:
            self.tokenizer.add_special_tokens({
                'additional_special_tokens': tokens_to_add
            })
            logger.info(f"Added special tokens: {tokens_to_add}")
    
    def preprocess_code(self, code: str, language: str = "python") -> str:
        """
        Preprocess code before tokenization
        
        Args:
            code: Raw code string
            language: Programming language
            
        Returns:
            Preprocessed code string
        """
        # Basic cleaning
        code = code.strip()
        
        # Language-specific preprocessing
        if language in self.language_patterns:
            patterns = self.language_patterns[language]
            
            # Handle Python indentation
            if language == "python":
                code = self._handle_python_indentation(code)
            
            # Handle Java/C-style blocks
            elif language in ["java", "c", "cpp", "c#", "javascript"]:
                code = self._handle_block_structure(code, language)
        
        return code
    
    def _handle_python_indentation(self, code: str) -> str:
        """Handle Python indentation with special tokens"""
        lines = code.split('\n')
        processed_lines = []
        indent_stack = [0]
        
        for line in lines:
            if line.strip():  # Skip empty lines
                # Calculate indentation
                indent = len(line) - len(line.lstrip())
                
                # Handle indentation changes
                if indent > indent_stack[-1]:
                    indent_stack.append(indent)
                    processed_lines.append('<INDENT>' + line)
                elif indent < indent_stack[-1]:
                    while indent_stack and indent < indent_stack[-1]:
                        indent_stack.pop()
                        processed_lines.append('<DEDENT>')
                    processed_lines.append(line)
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _handle_block_structure(self, code: str, language: str) -> str:
        """Handle block structure for C-style languages"""
        # Add block markers for { and }
        code = re.sub(r'\{', '<BLOCK_START>{', code)
        code = re.sub(r'\}', '}<BLOCK_END>', code)
        
        return code
    
    def tokenize(self, 
                 code: str, 
                 language: str = "python", 
                 max_length: Optional[int] = None,
                 truncation: bool = True,
                 padding: bool = True,
                 return_tensors: str = "pt") -> Dict[str, Any]:
        """
        Tokenize code
        
        Args:
            code: Code string to tokenize
            language: Programming language
            max_length: Maximum sequence length
            truncation: Whether to truncate long sequences
            padding: Whether to pad sequences
            return_tensors: Format of returned tensors
            
        Returns:
            Dictionary with tokenized inputs
        """
        # Get language-specific max length
        if max_length is None:
            if hasattr(self.config, 'get_context_window'):
                max_length = self.config.get_context_window(language)
            else:
                max_length = self.config.max_length
        
        # Preprocess code
        preprocessed_code = self.preprocess_code(code, language)
        
        # Tokenize
        encoded = self.tokenizer(
            preprocessed_code,
            max_length=max_length,
            truncation=truncation,
            padding=padding,
            return_tensors=return_tensors,
            return_attention_mask=True,
            return_token_type_ids=True if self.model_type == "codebert" else False
        )
        
        # Add metadata
        encoded['language'] = language
        encoded['original_length'] = len(code)
        encoded['preprocessed_length'] = len(preprocessed_code)
        
        return encoded
    
    def batch_tokenize(self,
                      codes: List[str],
                      languages: List[str] = None,
                      max_length: Optional[int] = None,
                      truncation: bool = True,
                      padding: bool = True,
                      return_tensors: str = "pt") -> Dict[str, Any]:
        """
        Tokenize multiple code samples
        
        Args:
            codes: List of code strings
            languages: List of programming languages
            max_length: Maximum sequence length
            truncation: Whether to truncate long sequences
            padding: Whether to pad sequences
            return_tensors: Format of returned tensors
            
        Returns:
            Dictionary with batch tokenized inputs
        """
        if languages is None:
            languages = ["python"] * len(codes)
        
        if len(codes) != len(languages):
            raise ValueError("Number of codes and languages must match")
        
        # Preprocess all codes
        preprocessed_codes = []
        for code, lang in zip(codes, languages):
            preprocessed_codes.append(self.preprocess_code(code, lang))
        
        # Get max length
        if max_length is None:
            max_length = self.config.max_length
        
        # Batch tokenize
        encoded = self.tokenizer(
            preprocessed_codes,
            max_length=max_length,
            truncation=truncation,
            padding=padding,
            return_tensors=return_tensors,
            return_attention_mask=True,
            return_token_type_ids=True if self.model_type == "codebert" else False
        )
        
        # Add metadata
        encoded['languages'] = languages
        encoded['batch_size'] = len(codes)
        
        return encoded
    
    def decode(self, token_ids: Union[List[int], List[List[int]]], 
               skip_special_tokens: bool = True,
               clean_up_tokenization_spaces: bool = True) -> Union[str, List[str]]:
        """
        Decode token IDs back to text
        
        Args:
            token_ids: Token IDs to decode
            skip_special_tokens: Whether to skip special tokens
            clean_up_tokenization_spaces: Whether to clean up tokenization spaces
            
        Returns:
            Decoded text or list of texts
        """
        decoded = self.tokenizer.decode(
            token_ids,
            skip_special_tokens=skip_special_tokens,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces
        )
        
        # Post-process to remove custom special tokens
        if isinstance(decoded, str):
            decoded = self._postprocess_decoded_text(decoded)
        elif isinstance(decoded, list):
            decoded = [self._postprocess_decoded_text(text) for text in decoded]
        
        return decoded
    
    def _postprocess_decoded_text(self, text: str) -> str:
        """Remove custom special tokens from decoded text"""
        # Remove custom tokens
        tokens_to_remove = [
            '<INDENT>', '<DEDENT>', '<BLOCK_START>', '<BLOCK_END>', 
            '<ARROW_FUNC>', '<NEWLINE>', '<TAB>'
        ]
        
        for token in tokens_to_remove:
            text = text.replace(token, '')
        
        return text.strip()
    
    def get_vocab_size(self) -> int:
        """Get vocabulary size"""
        return len(self.tokenizer)
    
    def get_special_tokens(self) -> Dict[str, str]:
        """Get special tokens mapping"""
        return {
            'pad_token': self.tokenizer.pad_token,
            'eos_token': self.tokenizer.eos_token,
            'bos_token': self.tokenizer.bos_token,
            'unk_token': self.tokenizer.unk_token,
            'sep_token': getattr(self.tokenizer, 'sep_token', None),
            'cls_token': getattr(self.tokenizer, 'cls_token', None),
            'mask_token': getattr(self.tokenizer, 'mask_token', None)
        }
    
    def analyze_tokenization(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analyze tokenization statistics
        
        Args:
            code: Code string to analyze
            language: Programming language
            
        Returns:
            Dictionary with tokenization statistics
        """
        # Tokenize
        encoded = self.tokenize(code, language, return_tensors="pt")
        
        # Get tokens
        tokens = self.tokenizer.convert_ids_to_tokens(encoded['input_ids'][0])
        
        # Calculate statistics
        stats = {
            'original_length': len(code),
            'token_count': len(tokens),
            'unique_tokens': len(set(tokens)),
            'compression_ratio': len(code) / len(tokens),
            'special_token_count': sum(1 for token in tokens if token.startswith('<') and token.endswith('>')),
            'average_token_length': sum(len(token) for token in tokens) / len(tokens),
            'tokens': tokens[:50],  # First 50 tokens for inspection
            'language': language
        }
        
        return stats
    
    def save_tokenizer(self, path: str):
        """Save tokenizer to specified path"""
        self.tokenizer.save_pretrained(path)
        logger.info(f"Tokenizer saved to: {path}")
    
    def load_tokenizer(self, path: str):
        """Load tokenizer from specified path"""
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        logger.info(f"Tokenizer loaded from: {path}")


class CodeGPTTokenizer(CodeTokenizer):
    """Specialized tokenizer for CodeGPT"""
    
    def __init__(self, config: Optional[CodeGPTConfig] = None):
        super().__init__("codegpt", config)


class CodeBERTTokenizer(CodeTokenizer):
    """Specialized tokenizer for CodeBERT"""
    
    def __init__(self, config: Optional[CodeBERTConfig] = None):
        super().__init__("codebert", config)
    
    def tokenize_for_mlm(self, code: str, language: str = "python", 
                        mask_probability: float = 0.15) -> Dict[str, Any]:
        """
        Tokenize code for masked language modeling
        
        Args:
            code: Code string to tokenize
            language: Programming language
            mask_probability: Probability of masking tokens
            
        Returns:
            Dictionary with tokenized inputs and labels
        """
        import torch
        import random
        
        # Regular tokenization
        encoded = self.tokenize(code, language)
        
        # Create masked version
        input_ids = encoded['input_ids'][0].clone()
        labels = input_ids.clone()
        
        # Mask tokens
        mask_token_id = self.tokenizer.mask_token_id
        special_token_ids = set(self.tokenizer.all_special_ids)
        
        for i in range(len(input_ids)):
            if input_ids[i] not in special_token_ids and random.random() < mask_probability:
                input_ids[i] = mask_token_id
            else:
                labels[i] = -100  # Ignore in loss calculation
        
        return {
            'input_ids': input_ids.unsqueeze(0),
            'attention_mask': encoded['attention_mask'],
            'labels': labels.unsqueeze(0),
            'language': language
        }


# Factory function
def create_tokenizer(model_type: str, config: Optional[Union[CodeGPTConfig, CodeBERTConfig]] = None) -> CodeTokenizer:
    """
    Factory function to create appropriate tokenizer
    
    Args:
        model_type: Type of model ("codegpt" or "codebert")
        config: Model configuration
        
    Returns:
        Tokenizer instance
    """
    if model_type.lower() == "codegpt":
        return CodeGPTTokenizer(config)
    elif model_type.lower() == "codebert":
        return CodeBERTTokenizer(config)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


# Example usage
if __name__ == "__main__":
    # Example with CodeGPT
    codegpt_tokenizer = create_tokenizer("codegpt")
    
    sample_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Test the function
print(fibonacci(10))
'''
    
    # Tokenize
    encoded = codegpt_tokenizer.tokenize(sample_code, "python")
    print("Tokenized shape:", encoded['input_ids'].shape)
    
    # Analyze
    stats = codegpt_tokenizer.analyze_tokenization(sample_code, "python")
    print("Tokenization stats:", stats)
    
    # Example with CodeBERT
    codebert_tokenizer = create_tokenizer("codebert")
    
    # Tokenize for MLM
    mlm_encoded = codebert_tokenizer.tokenize_for_mlm(sample_code, "python")
    print("MLM tokenized shape:", mlm_encoded['input_ids'].shape)