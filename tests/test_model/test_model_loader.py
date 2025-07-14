# tests/test_model/test_model_loader.py
"""
Test model loading functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import torch

class TestModelLoader:
    """Test model loading functionality"""
    
    @patch('ai_model.model_loader.AutoTokenizer')
    @patch('ai_model.model_loader.AutoModel')
    def test_load_codegpt_model(self, mock_model, mock_tokenizer, codegpt_config):
        """Test loading CodeGPT model"""
        # Mock the model and tokenizer
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model.from_pretrained.return_value = Mock()
        
        from ai_model.model_loader import ModelLoader
        
        loader = ModelLoader(codegpt_config)
        model, tokenizer = loader.load_model()
        
        assert model is not None
        assert tokenizer is not None
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
    
    @patch('ai_model.model_loader.AutoTokenizer')
    @patch('ai_model.model_loader.AutoModel')
    def test_load_codebert_model(self, mock_model, mock_tokenizer, codebert_config):
        """Test loading CodeBERT model"""
        # Mock the model and tokenizer
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model.from_pretrained.return_value = Mock()
        
        from ai_model.model_loader import ModelLoader
        
        loader = ModelLoader(codebert_config)
        model, tokenizer = loader.load_model()
        
        assert model is not None
        assert tokenizer is not None
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
    
    @patch('ai_model.model_loader.torch.cuda.is_available')
    def test_device_selection(self, mock_cuda_available):
        """Test device selection for model loading"""
        from ai_model.model_loader import ModelLoader
        
        # Test CUDA available
        mock_cuda_available.return_value = True
        loader = ModelLoader(Mock())
        assert loader.device == 'cuda'
        
        # Test CUDA not available
        mock_cuda_available.return_value = False
        loader = ModelLoader(Mock())
        assert loader.device == 'cpu'
    
    def test_model_caching(self, codegpt_config):
        """Test model caching functionality"""
        from ai_model.model_loader import ModelLoader
        
        with patch('ai_model.model_loader.AutoTokenizer') as mock_tokenizer, \
             patch('ai_model.model_loader.AutoModel') as mock_model:
            
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            loader = ModelLoader(codegpt_config)
            
            # First load
            model1, tokenizer1 = loader.load_model()
            
            # Second load should use cache
            model2, tokenizer2 = loader.load_model()
            
            # Should only call from_pretrained once due to caching
            assert mock_model.from_pretrained.call_count == 1
            assert mock_tokenizer.from_pretrained.call_count == 1
    
    def test_model_loading_error_handling(self, codegpt_config):
        """Test error handling during model loading"""
        from ai_model.model_loader import ModelLoader
        
        with patch('ai_model.model_loader.AutoModel') as mock_model:
            mock_model.from_pretrained.side_effect = Exception("Model loading failed")
            
            loader = ModelLoader(codegpt_config)
            
            with pytest.raises(Exception):
                loader.load_model()