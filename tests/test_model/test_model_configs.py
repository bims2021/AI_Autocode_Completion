# tests/test_model/test_model_configs.py
"""
Test model configuration classes
"""
import pytest
import os
from unittest.mock import patch

class TestCodeGPTConfig:
    """Test CodeGPT configuration"""
    
    def test_default_initialization(self, codegpt_config):
        """Test default configuration initialization"""
        assert codegpt_config.model_name == "microsoft/CodeGPT-small-py"
        assert codegpt_config.tokenizer_name == "microsoft/CodeGPT-small-py"
        assert codegpt_config.max_length == 1024
        assert codegpt_config.vocab_size == 50257
        assert codegpt_config.hidden_size == 768
        assert codegpt_config.num_layers == 12
        assert codegpt_config.num_heads == 12
    
    def test_generation_config(self, codegpt_config):
        """Test generation configuration"""
        gen_config = codegpt_config.generation_config
        
        assert gen_config['max_new_tokens'] == 150
        assert gen_config['temperature'] == 0.7
        assert gen_config['top_p'] == 0.9
        assert gen_config['top_k'] == 50
        assert gen_config['repetition_penalty'] == 1.1
        assert gen_config['do_sample'] is True
        assert gen_config['early_stopping'] is True
    
    def test_supported_languages(self, codegpt_config):
        """Test supported languages list"""
        expected_languages = [
            'python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'c#', 
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 
            'html', 'css', 'sql', 'bash', 'powershell'
        ]
        
        for lang in expected_languages:
            assert lang in codegpt_config.supported_languages
    
    def test_language_specific_config(self, codegpt_config):
        """Test language-specific configurations"""
        python_config = codegpt_config.get_language_config('python')
        
        assert python_config['max_new_tokens'] == 150
        assert python_config['temperature'] == 0.6
        assert python_config['top_p'] == 0.85
        assert python_config['context_window'] == 2048
        assert python_config['comment_style'] == "#"
        assert python_config['indent_style'] == "spaces"
        assert python_config['indent_size'] == 4
        assert '.py' in python_config['file_extensions']
    
    def test_get_model_config_with_language(self, codegpt_config):
        """Test getting model config for specific language"""
        config = codegpt_config.get_model_config('python')
        
        assert config['model_name'] == codegpt_config.model_name
        assert config['generation_config']['temperature'] == 0.6  # Python-specific
        assert config['generation_config']['top_p'] == 0.85  # Python-specific
        assert 'language_config' in config
    
    def test_get_generation_config_for_language(self, codegpt_config):
        """Test getting generation config for specific language"""
        gen_config = codegpt_config.get_generation_config('javascript')
        
        assert gen_config['max_new_tokens'] == 120  # JavaScript-specific
        assert gen_config['temperature'] == 0.7  # JavaScript-specific
        assert gen_config['top_p'] == 0.9  # JavaScript-specific
    
    def test_detect_language_from_file(self, codegpt_config):
        """Test language detection from file extension"""
        assert codegpt_config.detect_language_from_file('test.py') == 'python'
        assert codegpt_config.detect_language_from_file('test.js') == 'javascript'
        assert codegpt_config.detect_language_from_file('test.java') == 'java'
        assert codegpt_config.detect_language_from_file('test.cpp') == 'cpp'
        assert codegpt_config.detect_language_from_file('test.unknown') is None
    
    def test_is_language_supported(self, codegpt_config):
        """Test language support checking"""
        assert codegpt_config.is_language_supported('python') is True
        assert codegpt_config.is_language_supported('PYTHON') is True  # Case insensitive
        assert codegpt_config.is_language_supported('unsupported') is False
    
    def test_add_supported_language(self, codegpt_config):
        """Test adding new supported language"""
        new_lang_config = {
            'max_new_tokens': 100,
            'temperature': 0.5,
            'file_extensions': ['.dart']
        }
        
        codegpt_config.add_supported_language('dart', new_lang_config)
        
        assert 'dart' in codegpt_config.supported_languages
        assert codegpt_config.get_language_config('dart') == new_lang_config
    
    def test_update_generation_config(self, codegpt_config):
        """Test updating generation configuration"""
        original_temp = codegpt_config.generation_config['temperature']
        
        codegpt_config.update_generation_config(temperature=0.5, top_k=30)
        
        assert codegpt_config.generation_config['temperature'] == 0.5
        assert codegpt_config.generation_config['top_k'] == 30
        assert codegpt_config.generation_config['temperature'] != original_temp
    
    def test_get_context_window(self, codegpt_config):
        """Test getting context window for languages"""
        assert codegpt_config.get_context_window('python') == 2048
        assert codegpt_config.get_context_window('javascript') == 1536
        assert codegpt_config.get_context_window('unknown') == 1024  # Default
    
    def test_get_model_info(self, codegpt_config):
        """Test getting model information"""
        info = codegpt_config.get_model_info()
        
        assert info['name'] == codegpt_config.model_name
        assert info['max_length'] == codegpt_config.max_length
        assert info['vocab_size'] == codegpt_config.vocab_size
        assert isinstance(info['supported_languages'], list)
        assert isinstance(info['language_configs'], list)

class TestCodeBERTConfig:
    """Test CodeBERT configuration"""
    
    def test_default_initialization(self, codebert_config):
        """Test default configuration initialization"""
        assert codebert_config.model_name == "microsoft/codebert-base"
        assert codebert_config.tokenizer_name == "microsoft/codebert-base"
        assert codebert_config.max_length == 512
        assert codebert_config.vocab_size == 50265
        assert codebert_config.hidden_size == 768
        assert codebert_config.num_layers == 12
        assert codebert_config.num_heads == 12
        assert codebert_config.intermediate_size == 3072
    
    def test_task_configurations(self, codebert_config):
        """Test task-specific configurations"""
        expected_tasks = [
            'code_completion', 'code_search', 'code_documentation',
            'code_analysis', 'bug_detection'
        ]
        
        for task in expected_tasks:
            assert task in codebert_config.task_configs
    
    def test_code_completion_config(self, codebert_config):
        """Test code completion task configuration"""
        completion_config = codebert_config.task_configs['code_completion']
        
        assert completion_config['max_new_tokens'] == 100
        assert completion_config['temperature'] == 0.8
        assert completion_config['top_p'] == 0.95
        assert completion_config['top_k'] == 40
        assert completion_config['repetition_penalty'] == 1.05
        assert completion_config['do_sample'] is True
    
    def test_get_model_config_with_task(self, codebert_config):
        """Test getting model config for specific task"""
        config = codebert_config.get_model_config('code_search')
        
        assert config['model_name'] == codebert_config.model_name
        assert 'task_config' in config
        assert config['task_config']['max_length'] == 256
        assert config['task_config']['pooling_mode'] == 'mean'
    
    def test_get_generation_config_for_task(self, codebert_config):
        """Test getting generation config for specific task"""
        gen_config = codebert_config.get_generation_config('code_documentation')
        
        assert gen_config['max_new_tokens'] == 200
        assert gen_config['temperature'] == 0.6
        assert gen_config['repetition_penalty'] == 1.2
    
    def test_update_task_config(self, codebert_config):
        """Test updating task configuration"""
        original_temp = codebert_config.task_configs['code_completion']['temperature']
        
        codebert_config.update_task_config('code_completion', temperature=0.5)
        
        assert codebert_config.task_configs['code_completion']['temperature'] == 0.5
        assert codebert_config.task_configs['code_completion']['temperature'] != original_temp
    
    def test_special_tokens(self, codebert_config):
        """Test special tokens configuration"""
        tokens = codebert_config.special_tokens
        
        assert tokens['cls_token'] == '<s>'
        assert tokens['sep_token'] == '</s>'
        assert tokens['pad_token'] == '<pad>'
        assert tokens['unk_token'] == '<unk>'
        assert tokens['mask_token'] == '<mask>'
    
    def test_get_model_info(self, codebert_config):
        """Test getting model information"""
        info = codebert_config.get_model_info()
        
        assert info['name'] == codebert_config.model_name
        assert info['max_length'] == codebert_config.max_length
        assert info['vocab_size'] == codebert_config.vocab_size
        assert isinstance(info['supported_languages'], list)
        assert isinstance(info['available_tasks'], list)
        assert 'code_completion' in info['available_tasks']

