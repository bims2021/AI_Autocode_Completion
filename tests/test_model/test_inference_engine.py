# tests/test_model/test_inference_engine.py
"""
Test inference engine functionality
"""
import pytest
import torch
from unittest.mock import Mock, patch, MagicMock

class TestInferenceEngine:
    """Test inference engine functionality"""
    
    def test_inference_engine_initialization(self, mock_model, mock_tokenizer, codegpt_config):
        """Test inference engine initialization"""
        from ai_model.inference_engine import InferenceEngine
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        assert engine.model == mock_model
        assert engine.tokenizer == mock_tokenizer
        assert engine.config == codegpt_config
        assert engine.device is not None
    
    def test_generate_completion_basic(self, mock_model, mock_tokenizer, codegpt_config, sample_code_input):
        """Test basic code completion generation"""
        from ai_model.inference_engine import InferenceEngine
        
        # Setup mocks
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return n + fibonacci(n-1)"
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8]])
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        result = engine.generate_completion(
            code=sample_code_input["python"],
            language="python",
            max_tokens=50
        )
        
        assert "code" in result
        assert "confidence" in result
        assert "language" in result
        assert result["language"] == "python"
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1
    
    def test_generate_completion_with_temperature(self, mock_model, mock_tokenizer, codegpt_config, sample_code_input):
        """Test completion generation with different temperatures"""
        from ai_model.inference_engine import InferenceEngine
        
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "completed code"
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5, 6]])
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        # Test with low temperature (more deterministic)
        result_low = engine.generate_completion(
            code=sample_code_input["python"],
            language="python",
            temperature=0.1
        )
        
        # Test with high temperature (more creative)
        result_high = engine.generate_completion(
            code=sample_code_input["python"],
            language="python",
            temperature=0.9
        )
        
        assert "code" in result_low
        assert "code" in result_high
        # Both should generate valid completions
        assert len(result_low["code"]) > 0
        assert len(result_high["code"]) > 0
    
    def test_generate_completion_multiple_languages(self, mock_model, mock_tokenizer, codegpt_config, sample_code_input):
        """Test completion generation for multiple languages"""
        from ai_model.inference_engine import InferenceEngine
        
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5, 6]])
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        languages = ["python", "javascript", "java", "cpp"]
        
        for lang in languages:
            mock_tokenizer.decode.return_value = f"completed {lang} code"
            
            result = engine.generate_completion(
                code=sample_code_input.get(lang, "test code"),
                language=lang,
                max_tokens=50
            )
            
            assert "code" in result
            assert result["language"] == lang
            assert lang in result["code"]
    
    def test_batch_generation(self, mock_model, mock_tokenizer, codegpt_config, sample_code_input):
        """Test batch completion generation"""
        from ai_model.inference_engine import InferenceEngine
        
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "completed code"
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5, 6]])
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        batch_requests = [
            {"code": sample_code_input["python"], "language": "python"},
            {"code": sample_code_input["javascript"], "language": "javascript"},
            {"code": sample_code_input["java"], "language": "java"}
        ]
        
        results = engine.generate_batch_completions(batch_requests)
        
        assert len(results) == 3
        for result in results:
            assert "code" in result
            assert "confidence" in result
            assert "language" in result
    
    def test_context_window_handling(self, mock_model, mock_tokenizer, codegpt_config):
        """Test handling of context window limits"""
        from ai_model.inference_engine import InferenceEngine
        
        # Create a very long code input
        long_code = "def test():\n    " + "x = 1\n    " * 1000
        
        mock_tokenizer.encode.return_value = list(range(2000))  # Exceeds context window
        mock_tokenizer.decode.return_value = "truncated completion"
        mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        result = engine.generate_completion(
            code=long_code,
            language="python",
            max_tokens=50
        )
        
        assert "code" in result
        # Should handle long input gracefully
        assert len(result["code"]) > 0
    
    def test_error_handling_in_generation(self, mock_model, mock_tokenizer, codegpt_config):
        """Test error handling during generation"""
        from ai_model.inference_engine import InferenceEngine
        
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_model.generate.side_effect = Exception("Generation failed")
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        with pytest.raises(Exception):
            engine.generate_completion(
                code="def test():",
                language="python",
                max_tokens=50
            )
    
    def test_confidence_calculation(self, mock_model, mock_tokenizer, codegpt_config):
        """Test confidence score calculation"""
        from ai_model.inference_engine import InferenceEngine
        
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        mock_tokenizer.decode.return_value = "completed code"
        
        # Mock model output with logits for confidence calculation
        mock_output = Mock()
        mock_output.logits = torch.tensor([[[0.1, 0.8, 0.1], [0.2, 0.6, 0.2]]])
        mock_model.generate.return_value = torch.tensor([[1, 2]])
        mock_model.forward.return_value = mock_output
        
        engine = InferenceEngine(mock_model, mock_tokenizer, codegpt_config)
        
        result = engine.generate_completion(
            code="def test():",
            language="python",
            max_tokens=10
        )
        
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1