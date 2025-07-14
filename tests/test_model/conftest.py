# tests/test_model/conftest.py
"""
Pytest configuration for model tests
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import torch
import numpy as np

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer for testing"""
    tokenizer = Mock()
    tokenizer.encode.return_value = [1, 2, 3, 4, 5]
    tokenizer.decode.return_value = "decoded text"
    tokenizer.vocab_size = 50000
    tokenizer.pad_token_id = 0
    tokenizer.eos_token_id = 2
    tokenizer.bos_token_id = 1
    return tokenizer

@pytest.fixture
def mock_model():
    """Mock model for testing"""
    model = Mock()
    model.eval.return_value = None
    model.config.vocab_size = 50000
    model.config.max_position_embeddings = 1024
    
    # Mock model output
    mock_output = Mock()
    mock_output.logits = torch.randn(1, 10, 50000)
    mock_output.past_key_values = None
    model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    model.forward.return_value = mock_output
    
    return model

@pytest.fixture
def codegpt_config():
    """CodeGPT configuration for testing"""
    from ai_model.model_configs.codegpt_config_enhanced import CodeGPTConfig
    return CodeGPTConfig()

@pytest.fixture
def codebert_config():
    """CodeBERT configuration for testing"""
    from ai_model.model_configs.codebert_config_clean import CodeBERTConfig
    return CodeBERTConfig()

@pytest.fixture
def sample_code_input():
    """Sample code input for testing"""
    return {
        "python": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return ",
        "javascript": "function factorial(n) {\n    if (n <= 1) return 1;\n    return ",
        "java": "public class Calculator {\n    public int add(int a, int b) {\n        return ",
        "cpp": "#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "
    }
