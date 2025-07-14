import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class ModelUtils:
    """Utility functions for AI model operations"""
    
    @staticmethod
    def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        if log_file:
            logging.basicConfig(
                level=getattr(logging, log_level.upper()),
                format=log_format,
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=getattr(logging, log_level.upper()),
                format=log_format
            )
    
    @staticmethod
    def create_cache_key(data: Dict[str, Any]) -> str:
        """Create a cache key from data dictionary"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    @staticmethod
    def ensure_directory(path: str) -> str:
        """Ensure directory exists and return path"""
        Path(path).mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Get MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def load_json_config(config_path: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
    
    @staticmethod
    def save_json_config(config: Dict[str, Any], config_path: str):
        """Save configuration to JSON file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def get_model_size(model_path: str) -> int:
        """Get total size of model files"""
        total_size = 0
        if os.path.isfile(model_path):
            return os.path.getsize(model_path)
        
        for dirpath, dirnames, filenames in os.walk(model_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        return total_size
    
    @staticmethod
    def benchmark_inference(inference_func, num_runs: int = 10) -> Dict[str, float]:
        """Benchmark inference function performance"""
        times = []
        
        for _ in range(num_runs):
            start_time = time.time()
            inference_func()
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_time': sum(times)
        }
    
    @staticmethod
    def validate_model_config(config: Dict[str, Any]) -> bool:
        """Validate model configuration"""
        required_keys = ['model_name', 'tokenizer_name', 'model_path']
        
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required configuration key: {key}")
                return False
        
        return True
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available model configurations"""
        models = []
        
        # Check for model configs
        config_dir = Path(__file__).parent / 'model_configs'
        if config_dir.exists():
            for config_file in config_dir.glob('*_config.py'):
                model_name = config_file.stem.replace('_config', '')
                models.append(model_name)
        
        return models
    
    @staticmethod
    def cleanup_old_cache_files(cache_dir: str, max_age_days: int = 30):
        """Clean up old cache files"""
        if not os.path.exists(cache_dir):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old cache file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove cache file {file_path}: {e}")