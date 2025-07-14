
"""
AI Model Package for Code Completion and Analysis
"""

__version__ = "1.0.0"
__author__ = "Bimal Kumar Chand"
__email__ = "bkc_kbps@ymail.com"

from .model_loader import ModelLoader
from .inference_engine import InferenceEngine
from .preprocessing import CodePreprocessor
from .postprocessing import CodePostprocessor
from .exceptions import (
    AIModelException,
    ModelLoadError,
    ModelNotFoundError,
    InferenceError,
    PreprocessingError,
    PostprocessingError,
    ConfigurationError,
    ModelNotLoadedError,
    UnsupportedLanguageError,
    InsufficientMemoryError
)

# Main API class
class AIModel:
    """
    Main AI Model class that orchestrates all components
    """
    
    def __init__(self, model_name: str = "codegpt", config: dict = None):
        """
        Initialize AI Model
        
        Args:
            model_name: Name of the model to load
            config: Optional configuration dictionary
        """
        self.model_name = model_name
        self.config = config or {}
        
        # Initialize components
        self.model_loader = ModelLoader()
        self.inference_engine = InferenceEngine()
        self.preprocessor = CodePreprocessor()
        self.postprocessor = CodePostprocessor()
        
        # Model state
        self.is_loaded = False
        self.model_config = None
    
    def load_model(self, force_reload: bool = False):
        """Load the specified model"""
        if self.is_loaded and not force_reload:
            return
        
        try:
            # Load model and tokenizer
            model, tokenizer, config = self.model_loader.load_model(
                self.model_name, 
                **self.config
            )
            
            # Initialize inference engine
            self.inference_engine.load_model(model, tokenizer, config)
            
            self.is_loaded = True
            self.model_config = config
            
        except Exception as e:
            raise ModelLoadError(f"Failed to load model {self.model_name}: {e}")
    
    def complete_code(self, code: str, language: str = "python", **kwargs):
        """
        Complete code using the loaded model
        
        Args:
            code: Input code to complete
            language: Programming language
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary with completion results
        """
        if not self.is_loaded:
            raise ModelNotLoadedError("Model not loaded. Call load_model() first.")
        
        try:
            # Preprocess input
            preprocessed = self.preprocessor.preprocess_code(code, language)
            
            # Generate completion
            raw_completion = self.inference_engine.generate_completion(
                preprocessed['text'], 
                language=language,
                **kwargs
            )
            
            # Postprocess output
            processed_completion = self.postprocessor.postprocess_completion(
                raw_completion,
                code,
                language
            )
            
            return {
                'original': code,
                'completion': processed_completion['text'],
                'confidence': processed_completion['confidence'],
                'metadata': processed_completion['metadata']
            }
            
        except Exception as e:
            raise InferenceError(f"Code completion failed: {e}")
    
    def analyze_code(self, code: str, language: str = "python"):
        """
        Analyze code structure and extract metadata
        
        Args:
            code: Input code to analyze
            language: Programming language
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Preprocess and analyze
            analysis = self.preprocessor.preprocess_code(code, language)
            
            return {
                'language': language,
                'metadata': analysis['metadata'],
                'structure': analysis.get('structure', {}),
                'complexity': analysis.get('complexity', 'unknown')
            }
            
        except Exception as e:
            raise PreprocessingError(f"Code analysis failed: {e}")
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": self.model_name,
            "config": self.model_config,
            "supported_languages": self.model_config.get('supported_languages', [])
        }
    
    def unload_model(self):
        """Unload the model to free memory"""
        if self.is_loaded:
            self.inference_engine.unload_model()
            self.is_loaded = False
            self.model_config = None


# Convenience functions
def load_model(model_name: str = "codegpt", **kwargs):
    """
    Load and return an AI model instance
    
    Args:
        model_name: Name of the model to load
        **kwargs: Additional configuration parameters
        
    Returns:
        AIModel instance
    """
    model = AIModel(model_name, kwargs)
    model.load_model()
    return model

def complete_code(code: str, language: str = "python", model_name: str = "codegpt", **kwargs):
    """
    Quick code completion function
    
    Args:
        code: Input code to complete
        language: Programming language
        model_name: Name of the model to use
        **kwargs: Additional parameters
        
    Returns:
        Completion string
    """
    model = load_model(model_name, **kwargs)
    result = model.complete_code(code, language, **kwargs)
    return result['completion']

def analyze_code(code: str, language: str = "python", model_name: str = "codegpt", **kwargs):
    """
    Quick code analysis function
    
    Args:
        code: Input code to analyze
        language: Programming language
        model_name: Name of the model to use
        **kwargs: Additional parameters
        
    Returns:
        Analysis dictionary
    """
    model = AIModel(model_name, kwargs)
    return model.analyze_code(code, language)