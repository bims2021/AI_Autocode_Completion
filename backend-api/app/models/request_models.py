
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional, List, NamedTuple
import re

class CompletionRequest(BaseModel):
    context: Dict[str, Any]
    max_suggestions: int = 3
    max_length: int = 100
    temperature: float = 0.7
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('max_suggestions')
    def validate_max_suggestions(cls, v):
        if not (1 <= v <= 10):
            raise ValueError('max_suggestions must be between 1 and 10')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not (0.1 <= v <= 2.0):
            raise ValueError('temperature must be between 0.1 and 2.0')
        return v
    
    @validator('max_length')
    def validate_max_length(cls, v):
        if not (10 <= v <= 500):
            raise ValueError('max_length must be between 10 and 500')
        return v

class ProcessedContext(BaseModel):
    code_snippet: str
    function_signature: Optional[Dict[str, Any]] = None
    class_info: Optional[Dict[str, Any]] = None
    imports: List[str] = []
    variables: List[Dict[str, str]] = []
    context_hash: str
    language: str