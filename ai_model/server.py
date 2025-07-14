
"""
HTTP Server for AI Model API
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import AIModel, load_model
from .utils import ModelUtils
from .exceptions import AIModelException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class CodeCompletionRequest(BaseModel):
    code: str = Field(..., description="Input code to complete")
    language: str = Field(default="python", description="Programming language")
    model: str = Field(default="codegpt", description="Model to use")
    max_tokens: int = Field(default=100, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Generation temperature")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")
    top_k: int = Field(default=50, description="Top-k sampling parameter")

class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., description="Input code to analyze")
    language: str = Field(default="python", description="Programming language")
    model: str = Field(default="codegpt", description="Model to use")

class ModelLoadRequest(BaseModel):
    model: str = Field(..., description="Model name to load")
    force_reload: bool = Field(default=False, description="Force reload if already loaded")

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Global model cache
model_cache: Dict[str, AIModel] = {}

# FastAPI app
app = FastAPI(
    title="AI Model API",
    description="HTTP API for AI-powered code completion and analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
async def get_or_load_model(model_name: str) -> AIModel:
    """Get model from cache or load it"""
    if model_name not in model_cache:
        try:
            model = AIModel(model_name)
            model.load_model()
            model_cache[model_name] = model
            logger.info(f"Loaded model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")
    
    return model_cache[model_name]

def create_response(success: bool, data: Any = None, error: str = None) -> APIResponse:
    """Create standardized API response"""
    return APIResponse(success=success, data=data, error=error)

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Model API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return create_response(
        success=True,
        data={
            "status": "healthy",
            "loaded_models": list(model_cache.keys()),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.post("/complete")
async def complete_code_endpoint(request: CodeCompletionRequest):
    """Code completion endpoint"""
    try:
        # Get model
        model = await get_or_load_model(request.model)
        
        # Generate completion
        result = model.complete_code(
            code=request.code,
            language=request.language,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        return create_response(success=True, data=result)
        
    except AIModelException as e:
        logger.error(f"Model error in completion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in completion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/analyze")
async def analyze_code_endpoint(request: CodeAnalysisRequest):
    """Code analysis endpoint"""
    try:
        # Get model
        model = await get_or_load_model(request.model)
        
        # Analyze code
        result = model.analyze_code(
            code=request.code,
            language=request.language
        )
        
        return create_response(success=True, data=result)
        
    except AIModelException as e:
        logger.error(f"Model error in analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/models/load")
async def load_model_endpoint(request: ModelLoadRequest, background_tasks: BackgroundTasks):
    """Load model endpoint"""
    try:
        if request.model in model_cache and not request.force_reload:
            return create_response(
                success=True,
                data={"message": f"Model {request.model} already loaded"}
            )
        
        # Load model in background if force_reload
        if request.force_reload:
            background_tasks.add_task(reload_model, request.model)
            return create_response(
                success=True,
                data={"message": f"Model {request.model} reload started"}
            )
        
        # Load model
        model = AIModel(request.model)
        model.load_model()
        model_cache[request.model] = model
        
        return create_response(
            success=True,
            data={"message": f"Model {request.model} loaded successfully"}
        )
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/models/{model_name}")
async def unload_model_endpoint(model_name: str):
    """Unload model endpoint"""
    try:
        if model_name in model_cache:
            model_cache[model_name].unload_model()
            del model_cache[model_name]
            
            return create_response(
                success=True,
                data={"message": f"Model {model_name} unloaded successfully"}
            )
        else:
            return create_response(
                success=False,
                error=f"Model {model_name} not found in cache"
            )
            
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models_endpoint():
    """List available models endpoint"""
    try:
        available_models = ModelUtils.get_available_models()
        loaded_models = list(model_cache.keys())
        
        return create_response(
            success=True,
            data={
                "available_models": available_models,
                "loaded_models": loaded_models
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{model_name}/info")
async def model_info_endpoint(model_name: str):
    """Get model information endpoint"""
    try:
        if model_name in model_cache:
            info = model_cache[model_name].get_model_info()
            return create_response(success=True, data=info)
        else:
            return create_response(
                success=False,
                error=f"Model {model_name} not loaded"
            )
            
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def stats_endpoint():
    """Get server statistics"""
    try:
        stats = {
            "loaded_models": len(model_cache),
            "model_names": list(model_cache.keys()),
            "server_uptime": datetime.now().isoformat(),
            "memory_usage": "N/A"  # Could be enhanced with psutil
        }
        
        return create_response(success=True, data=stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def reload_model(model_name: str):
    """Reload model in background"""
    try:
        if model_name in model_cache:
            model_cache[model_name].unload_model()
            del model_cache[model_name]
        
        model = AIModel(model_name)
        model.load_model()
        model_cache[model_name] = model
        
        logger.info(f"Model {model_name} reloaded successfully")
        
    except Exception as e:
        logger.error(f"Error reloading model {model_name}: {e}")

# Server startup and shutdown
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("AI Model API server starting up...")
    
    # Optionally preload default model
    try:
        default_model = AIModel("codegpt")
        default_model.load_model()
        model_cache["codegpt"] = default_model
        logger.info("Default model 'codegpt' preloaded")
    except Exception as e:
        logger.warning(f"Failed to preload default model: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("AI Model API server shutting down...")
    
    # Unload all models
    for model_name, model in model_cache.items():
        try:
            model.unload_model()
            logger.info(f"Unloaded model: {model_name}")
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {e}")
    
    model_cache.clear()

# Main server runner
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the API server"""
    uvicorn.run(
        "ai_model.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()