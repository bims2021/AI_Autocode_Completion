# tests/test_model/test_postprocessing.py
"""
Test postprocessing functionality
"""
import pytest

class TestPostprocessing:
    """Test code postprocessing functionality"""
    
    def test_code_formatting(self):
        """Test code formatting"""
        from ai_model.postprocessing import CodePostprocessor
        
        postprocessor = CodePostprocessor()
        
        # Test with unformatted code
        unformatted_code = "def test():x=1;y=2;return x+y"
        
        formatted = postprocessor.format_code(unformatted_code, "python")
        
        assert isinstance(formatted, str)
        # Should have proper formatting
        assert "\n" in formatted
        assert "def test():" in formatted
    
    def test_syntax_validation(self):
        """Test syntax validation"""
        from ai_model.postprocessing import CodePostprocessor
        
        postprocessor = CodePostprocessor()
        
        # Test valid syntax
        valid_code = "def test():\n    return 42"
        assert postprocessor.validate_syntax(valid_code, "python") is True
        
        # Test invalid syntax
        invalid_code = "def test(\n    return 42"
        assert postprocessor.validate_syntax(invalid_code, "python") is False
    
    def test_completion_filtering(self):
        """Test filtering of generated completions"""
        from ai_model.postprocessing import CodePostprocessor
        
        postprocessor = CodePostprocessor()
        
        completions = [
            {"code": "def valid_function():\n    return 42", "confidence": 0.9},
            {"code": "invalid syntax def(", "confidence": 0.3},
            {"code": "print('hello world')", "confidence": 0.8},
            {"code": "# just a comment", "confidence": 0.2}
        ]
        
        filtered = postprocessor.filter_completions(completions, "python")
        
        assert len(filtered) <= len(completions)
        # Should filter out invalid syntax
        for completion in filtered:
            assert postprocessor.validate_syntax(completion["code"], "python")
    
    def test_confidence_adjustment(self):
        """Test confidence score adjustment"""
        from ai_model.postprocessing import CodePostprocessor
        
        postprocessor = CodePostprocessor()
        
        # Test with various completion qualities
        test_cases = [
            {"code": "def complete_function():\n    return sum(range(10))", "initial_confidence": 0.8},
            {"code": "incomplete_func", "initial_confidence": 0.8},
            {"code": "print('hello')", "initial_confidence": 0.6}
        ]
        
        for case in test_cases:
            adjusted = postprocessor.adjust_confidence(
                case["code"], 
                case["initial_confidence"], 
                "python"
            )
            
            assert isinstance(adjusted, float)
            assert 0 <= adjusted <= 1
    
    def test_duplicate_removal(self):
        """Test removal of duplicate completions"""
        from ai_model.postprocessing import CodePostprocessor
        
        postprocessor = CodePostprocessor()
        
        completions = [
            {"code": "def test():\n    return 1", "confidence": 0.9},
            {"code": "def test():\n    return 1", "confidence": 0.8},  # Duplicate
            {"code": "def test():\n    return 2", "confidence": 0.7},
            {"code": "def different():\n    return 1", "confidence": 0.6}
        ]
        
        unique = postprocessor.remove_duplicates(completions)
        
        assert len(unique) == 3  # Should remove one duplicate
        # Should keep the one with higher confidence
        test_completions = [c for c in unique if "def test():" in c["code"] and "return 1" in c["code"]]
        assert len(test_completions) == 1
        assert test_completions[0]["confidence"] == 0.9

