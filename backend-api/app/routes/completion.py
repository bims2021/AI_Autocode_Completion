from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional
import time
import logging

from ..models.request_models import CompletionRequest
from ..models.response_models import CompletionResponse, ErrorResponse
from ..services.model_service import ModelService
from ..services.context_processor import ContextProcessor
from ..services.cache_service import CacheService
from ..utils.rate_limiter import RateLimiter
from ..utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

completion_router = APIRouter(tags=["completion"])

# Global service instances (singleton pattern)
_model_service: Optional[ModelService] = None
_context_processor: Optional[ContextProcessor] = None
_cache_service: Optional[CacheService] = None
_rate_limiter: Optional[RateLimiter] = None

# Dependencies with singleton pattern
async def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
        await _model_service.initialize()
    return _model_service

async def get_context_processor() -> ContextProcessor:
    global _context_processor
    if _context_processor is None:
        _context_processor = ContextProcessor()
    return _context_processor

async def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

async def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

@completion_router.post("/completion", response_model=CompletionResponse)
async def get_completion(
    request: CompletionRequest,
    http_request: Request,
    model_service: ModelService = Depends(get_model_service),
    context_processor: ContextProcessor = Depends(get_context_processor),
    cache_service: CacheService = Depends(get_cache_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """Main completion endpoint with language-specific support"""
    start_time = time.time()
    
    try:
        # Check rate limit
        user_id = request.user_id or 'anonymous'
        rate_limit_result = await rate_limiter.check_rate_limit(user_id)
        
        if not rate_limit_result['allowed']:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(rate_limit_result['reset_in'])}
            )
        
        # Detect and validate language
        detected_language = None
        if hasattr(request, 'language') and request.language:
            detected_language = request.language.lower()
        elif hasattr(request, 'file_path') and request.file_path:
            # Use model service to detect language from file extension
            detected_language = model_service.detect_language_from_file(request.file_path)
        
        # Validate language support
        if detected_language and not model_service.is_language_supported(detected_language):
            logger.warning(f"Unsupported language: {detected_language}")
            detected_language = 'python'  # Fallback to Python
        
        # Process context with language information
        processed_context = await context_processor.process_context(request)
        
        # Generate cache key that includes language
        cache_key = f"{processed_context.context_hash}_{detected_language or 'default'}"
        
        # Check cache with language-specific key
        cached_suggestions = await cache_service.get_cached_suggestions(cache_key)
        
        if cached_suggestions:
            return CompletionResponse(
                suggestions=cached_suggestions,
                metadata={
                    "processingTimeMs": int((time.time() - start_time) * 1000),
                    "modelVersion": "cached",
                    "cacheHit": True,
                    "contextHash": processed_context.context_hash,
                    "languageDetected": detected_language,
                    "configUsed": "cached",
                    "modelType": "cached"
                },
                status="success"
            )
        
        # Determine model type based on request or language
        model_type = getattr(request, 'model_type', 'codegpt')
        
        # Get language-specific generation parameters
        generation_params = {
            'max_suggestions': request.max_suggestions,
            'temperature': request.temperature,
            'model_type': model_type
        }
        
        # Override with language-specific parameters if available
        if detected_language:
            if model_type == 'codegpt':
                lang_config = model_service.codegpt_config.get_language_config(detected_language)
                if lang_config:
                    generation_params['temperature'] = lang_config.get('temperature', request.temperature)
            elif model_type == 'codebert':
                task_config = model_service.codebert_config.get_generation_config('code_completion')
                if task_config:
                    generation_params['temperature'] = task_config.get('temperature', request.temperature)
        
        # Generate suggestions with language-specific configuration
        suggestions = await model_service.generate_suggestions(
            processed_context,
            **generation_params
        )
        
        # Cache suggestions with language-specific key
        await cache_service.cache_suggestions(cache_key, suggestions)
        
        # Determine model version string
        model_version = f"{model_type}"
        if detected_language:
            model_version += f"-{detected_language}"
        
        return CompletionResponse(
            suggestions=suggestions,
            metadata={
                "processingTimeMs": int((time.time() - start_time) * 1000),
                "modelVersion": model_version,
                "cacheHit": False,
                "contextHash": processed_context.context_hash,
                "languageDetected": detected_language,
                "configUsed": model_type,
                "modelType": model_type
            },
            status="success"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@completion_router.get("/languages")
async def get_supported_languages(
    model_service: ModelService = Depends(get_model_service)
):
    """Get list of supported programming languages"""
    try:
        languages = model_service.get_supported_languages()
        return {
            "supported_languages": languages,
            "total_count": len(languages),
            "default_language": "python"
        }
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@completion_router.get("/language/{language}/config")
async def get_language_config(
    language: str,
    model_service: ModelService = Depends(get_model_service)
):
    """Get configuration for a specific language"""
    try:
        if not model_service.is_language_supported(language):
            raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
        
        codegpt_config = model_service.codegpt_config.get_language_config(language)
        codebert_config = model_service.codebert_config.get_generation_config('code_completion')
        
        return {
            "language": language,
            "codegpt_config": codegpt_config,
            "codebert_config": codebert_config,
            "context_window": model_service.codegpt_config.get_context_window(language)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting language config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@completion_router.post("/language/{language}/config")
async def update_language_config(
    language: str,
    config_update: Dict[str, Any],
    model_service: ModelService = Depends(get_model_service)
):
    """Update configuration for a specific language"""
    try:
        if not model_service.is_language_supported(language):
            raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
        
        # Update CodeGPT config
        if 'codegpt' in config_update:
            model_service.update_model_config('codegpt', language, **config_update['codegpt'])
        
        # Update CodeBERT config
        if 'codebert' in config_update:
            model_service.update_model_config('codebert', task='code_completion', **config_update['codebert'])
        
        return {
            "status": "success",
            "language": language,
            "updated_config": config_update
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating language config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@completion_router.get("/models/info")
async def get_model_info(
    model_service: ModelService = Depends(get_model_service)
):
    """Get information about loaded models"""
    try:
        model_info = model_service.get_model_info()
        return {
            "model_info": model_info,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@completion_router.get("/metrics")
async def get_metrics(
    model_service: ModelService = Depends(get_model_service)
):
    """Enhanced metrics endpoint with language-specific data"""
    try:
        # Get basic metrics
        basic_metrics = {
            "requests_total": 1000,
            "cache_hit_rate": 0.75,
            "avg_response_time": 150,
            "active_users": 50
        }
        
        # Add model-specific metrics
        model_info = model_service.get_model_info()
        
        enhanced_metrics = {
            **basic_metrics,
            "loaded_models": model_info.get("loaded_models", []),
            "supported_languages": model_info.get("supported_languages", []),
            "default_model": model_info.get("default_model", "codegpt"),
            "device": model_info.get("device", "cpu"),
            "language_support_count": len(model_info.get("supported_languages", []))
        }
        
        return enhanced_metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@completion_router.post("/models/reload")
async def reload_models(
    model_service: ModelService = Depends(get_model_service)
):
    """Reload models (useful for development/debugging)"""
    try:
        # Reset initialized flag to force reload
        model_service._initialized = False
        await model_service.initialize()
        
        return {
            "status": "success",
            "message": "Models reloaded successfully",
            "model_info": model_service.get_model_info()
        }
    except Exception as e:
        logger.error(f"Error reloading models: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload models")

