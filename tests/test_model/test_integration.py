# tests/test_model/test_integration.py
"""
Integration tests for model components
"""
import pytest
from unittest.mock import Mock, patch
import torch

class TestModelIntegration:
    """Test integration between model components"""
    
    @patch('ai_model.model_loader.AutoTokenizer')
    @patch('ai_model.model_loader.AutoModel')
    def test_end_to_end_completion(self, mock_model_class, mock_tokenizer_class, codegpt_config):
        """Test end-to-end completion generation"""
        # Setup mocks
        mock_tokenizer = Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        
        mock_model = Mock()
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
        mock_model.eval.return_value = None
        mock_model_class.from_pretrained.return_value = mock_model
        
        # Test the full pipeline
        from ai_model.model_loader import ModelLoader
        from ai_model.inference_engine import InferenceEngine
        from ai_model.preprocessing import CodePreprocessor
        from ai_model.postprocessing import CodePostprocessor
        
        # Load model
        loader = ModelLoader(codegpt_config)
        model, tokenizer = loader.load_model()
        
        # Create inference engine
        engine = InferenceEngine(model, tokenizer, codegpt_config)
        
        # Preprocess input
        preprocessor = CodePreprocessor()
        input_code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return "
        processed_input = preprocessor.preprocess_code(input_code, "python")
        
        # Generate completion
        result = engine.generate_completion(
            code=processed_input,
            language="python",
            max_tokens=50
        )
        
        # Postprocess result
        postprocessor = CodePostprocessor()
        final_result = postprocessor.format_code(result["code"], "python")
        
        assert isinstance(final_result, str)
        assert len(final_result) > 0
        assert "fibonacci" in final_result
    
    def test_configuration_consistency(self, codegpt_config, codebert_config):
        """Test consistency between different configurations"""
        # Test that both configs have required methods
        required_methods = ['get_model_config', 'get_generation_config', 'is_language_supported']
        
        for method in required_methods:
            assert hasattr(codegpt_config, method)
            assert hasattr(codebert_config, method)
            assert callable(getattr(codegpt_config, method))
            assert callable(getattr(codebert_config, method))
    
    def test_language_support_consistency(self, codegpt_config, codebert_config):
        """Test language support consistency"""
        # Common languages should be supported by both
        common_languages = ['python', 'java', 'javascript', 'c', 'cpp']
        
        for lang in common_languages:
            assert codegpt_config.is_language_supported(lang)
            # Note: CodeBERT may have different language support
            # Just ensure the method works
            result = codebert_config.is_language_supported(lang)
            assert isinstance(result, bool)
    
    def test_model_switching(self, codegpt_config, codebert_config):
        """Test switching between different models"""
        with patch('ai_model.model_loader.AutoTokenizer') as mock_tokenizer, \
             patch('ai_model.model_loader.AutoModel') as mock_model:
            
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            from ai_model.model_loader import ModelLoader
            
            # Load CodeGPT
            loader_gpt = ModelLoader(codegpt_config)
            model_gpt, tokenizer_gpt = loader_gpt.load_model()
            
            # Load CodeBERT
            loader_bert = ModelLoader(codebert_config)
            model_bert, tokenizer_bert = loader_bert.load_model()
            
            # Both should load successfully
            assert model_gpt is not None
            assert tokenizer_gpt is not None
            assert model_bert is not None
            assert tokenizer_bert is not None
    
    def test_error_propagation(self, codegpt_config):
        """Test error propagation through the pipeline"""
        with patch('ai_model.model_loader.AutoModel') as mock_model:
            mock_model.from_pretrained.side_effect = Exception("Model loading failed")
            
            from ai_model.model_loader import ModelLoader
            
            loader = ModelLoader(codegpt_config)
            
            # Error should propagate properly
            with pytest.raises(Exception) as exc_info:
                loader.load_model()
            
            assert "Model loading failed" in str(exc_info.value)
    
    def test_memory_management(self, codegpt_config):
        """Test memory management in model operations"""
        with patch('ai_model.model_loader.AutoTokenizer') as mock_tokenizer, \
             patch('ai_model.model_loader.AutoModel') as mock_model, \
             patch('torch.cuda.empty_cache') as mock_empty_cache:
            
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            from ai_model.model_loader import ModelLoader
            
            loader = ModelLoader(codegpt_config)
            
            # Test cleanup
            loader.cleanup()
            
            # Should call cache cleanup if using CUDA
            if torch.cuda.is_available():
                mock_empty_cache.assert_called()
    
    def test_concurrent_requests(self, codegpt_config):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        with patch('ai_model.model_loader.AutoTokenizer') as mock_tokenizer, \
             patch('ai_model.model_loader.AutoModel') as mock_model:
            
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model_instance = Mock()
            mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
            mock_model.from_pretrained.return_value = mock_model_instance
            
            from ai_model.model_loader import ModelLoader
            from ai_model.inference_engine import InferenceEngine
            
            loader = ModelLoader(codegpt_config)
            model, tokenizer = loader.load_model()
            engine = InferenceEngine(model, tokenizer, codegpt_config)
            
            results = []
            errors = []
            
            def generate_completion():
                try:
                    result = engine.generate_completion(
                        code="def test():",
                        language="python",
                        max_tokens=10
                    )
                    results.append(result)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=generate_completion)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 5
            
            for result in results:
                assert "code" in result
                assert "confidence" in result