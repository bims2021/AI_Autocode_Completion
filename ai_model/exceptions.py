class AIModelException(Exception):
    """Base exception for AI model operations"""
    pass

class ModelLoadError(AIModelException):
    """Exception raised when model loading fails"""
    pass

class ModelNotFoundError(AIModelException):
    """Exception raised when model is not found"""
    pass

class InferenceError(AIModelException):
    """Exception raised during inference"""
    pass

class PreprocessingError(AIModelException):
    """Exception raised during preprocessing"""
    pass

class PostprocessingError(AIModelException):
    """Exception raised during postprocessing"""
    pass

class ConfigurationError(AIModelException):
    """Exception raised for configuration errors"""
    pass

class ModelNotLoadedError(AIModelException):
    """Exception raised when trying to use unloaded model"""
    pass

class UnsupportedLanguageError(AIModelException):
    """Exception raised for unsupported programming languages"""
    pass

class InsufficientMemoryError(AIModelException):
    """Exception raised when there's insufficient memory"""
    pass