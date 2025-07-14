
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Suggestion(BaseModel):
    text: str
    confidence: float
    type: str = "single-line"
    description: Optional[str] = None
    cursorOffset: int = 0
    replaceRange: Optional[Dict[str, int]] = None

class CompletionMetadata(BaseModel):
    processingTimeMs: int
    modelVersion: str
    cacheHit: bool
    contextHash: str

class CompletionResponse(BaseModel):
    suggestions: List[Suggestion]
    metadata: CompletionMetadata
    status: str = "success"
    errorMessage: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: Optional[str] = None