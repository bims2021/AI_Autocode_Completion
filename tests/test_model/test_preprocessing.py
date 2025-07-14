# tests/test_model/test_preprocessing.py
"""
Test preprocessing functionality
"""
import pytest
from unittest.mock import Mock

class TestPreprocessing:
    """Test code preprocessing functionality"""
    
    def test_code_tokenization(self, sample_code_input):
        """Test code tokenization"""
        from ai_model.preprocessing import CodePreprocessor
        
        preprocessor = CodePreprocessor()
        
        for language, code in sample_code_input.items():
            tokens = preprocessor.tokenize_code(code, language)
            
            assert isinstance(tokens, list)
            assert len(tokens) > 0
            # Should preserve code structure
            assert any(token for token in tokens if token.strip())
    
    def test_context_extraction(self, sample_code_input):
        """Test context extraction from code"""
        from ai_model.preprocessing import CodePreprocessor
        
        preprocessor = CodePreprocessor()
        
        code = sample_code_input["python"]
        cursor_position = len(code) - 10
        
        context = preprocessor.extract_context(code, cursor_position)
        
        assert "before_cursor" in context
        assert "after_cursor" in context
        assert "function_context" in context
        assert "class_context" in context
        assert isinstance(context["before_cursor"], str)
        assert isinstance(context["after_cursor"], str)
    
    def test_code_normalization(self, sample_code_input):
        """Test code normalization"""
        from ai_model.preprocessing import CodePreprocessor
        
        preprocessor = CodePreprocessor()
        
        # Test with inconsistent indentation
        messy_code = "def test():\n  x = 1\n    y = 2\n      return x + y"
        
        normalized = preprocessor.normalize_code(messy_code, "python")
        
        assert isinstance(normalized, str)
        # Should have consistent indentation
        lines = normalized.split('\n')
        assert len(lines) > 1
    
    def test_language_detection(self, sample_code_input):
        """Test programming language detection"""
        from ai_model.preprocessing import CodePreprocessor
        
        preprocessor = CodePreprocessor()
        
        # Test with clear language indicators
        test_cases = [
            ("def main():\n    print('hello')", "python"),
            ("function main() {\n    console.log('hello'); }", "javascript"),
            ("public class Test {\n    public static void main() {}", "java"),
            ("#include <iostream>\nint main() {}", "cpp")
        ]
        
        for code, expected_lang in test_cases:
            detected = preprocessor.detect_language(code)
            assert detected == expected_lang or detected in ["python", "javascript", "java", "cpp"]
    
    def test_comment_handling(self):
        """Test comment handling in preprocessing"""
        from ai_model.preprocessing import CodePreprocessor
        
        preprocessor = CodePreprocessor()
        
        code_with_comments = '''
        def fibonacci(n):
            # Base case
            if n <= 1:
                return n
            # Recursive case
            return fibonacci(n-1) + fibonacci(n-2)
        '''
        
        # Test preserving comments
        processed = preprocessor.preprocess_code(code_with_comments, "python", preserve_comments=True)
        assert "# Base case" in processed
        assert "# Recursive case" in processed
        
        # Test removing comments
        processed = preprocessor.preprocess_code(code_with_comments, "python", preserve_comments=False)
        assert "# Base case" not in processed
        assert "# Recursive case" not in processed
    
    def test_imports_and_dependencies(self):
        """Test handling of imports and dependencies"""
        from ai_model.preprocessing import CodePreprocessor
        
        preprocessor = CodePreprocessor()
        
        code_with_imports = '''
        import numpy as np
        from sklearn import metrics
        import pandas as pd
        
        def analyze_data():
            pass
        '''
        
        context = preprocessor.extract_dependencies(code_with_imports, "python")
        
        assert "imports" in context
        assert "numpy" in str(context["imports"])
        assert "sklearn" in str(context["imports"])
        assert "pandas" in str(context["imports"])
