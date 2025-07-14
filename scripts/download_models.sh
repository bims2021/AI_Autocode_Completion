#!/usr/bin/env python3
"""
download_models.py - Download and setup AI models for code autocompletion

This script downloads and caches the required AI models (CodeGPT and CodeBERT)
for the code autocompletion system.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
import shutil
from tqdm import tqdm
import requests
from transformers import AutoTokenizer, AutoModel, GPT2LMHeadModel, RobertaModel
import torch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configurations
try:
    from ai_model.model_configs.codegpt_config_enhanced import CodeGPTConfig
    from ai_model.model_configs.codebert_config_clean import CodeBERTConfig
except ImportError as e:
    print(f"Error importing configuration: {e}")
    print("Please ensure you're running this script from the project root")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Download and setup AI models for code autocompletion"""
    
    def __init__(self, force_download: bool = False, cache_dir: Optional[str] = None):
        self.force_download = force_download
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/ai-model")
        
        # Initialize configurations
        self.codegpt_config = CodeGPTConfig()
        self.codebert_config = CodeBERTConfig()
        
        # Model definitions
        self.models = {
            'codegpt': {
                'name': self.codegpt_config.model_name,
                'tokenizer_name': self.codegpt_config.tokenizer_name,
                'cache_path': self.codegpt_config.model_path,
                'model_class': GPT2LMHeadModel,
                'description': 'CodeGPT model for code generation and completion'
            },
            'codebert': {
                'name': self.codebert_config.model_name,
                'tokenizer_name': self.codebert_config.tokenizer_name,
                'cache_path': self.codebert_config.model_path,
                'model_class': RobertaModel,
                'description': 'CodeBERT model for code understanding and analysis'
            }
        }
    
    def check_disk_space(self, required_gb: float = 5.0) -> bool:
        """Check if there's enough disk space for model downloads"""
        try:
            statvfs = os.statvfs(self.cache_dir)
            available_gb = (statvfs.f_bavail * statvfs.f_frsize) / (1024**3)
            
            if available_gb < required_gb:
                logger.warning(f"Low disk space: {available_gb:.2f}GB available, {required_gb}GB required")
                return False
            
            logger.info(f"Disk space check passed: {available_gb:.2f}GB available")
            return True
            
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            return True  # Assume it's okay if we can't check
    
    def create_cache_directories(self) -> None:
        """Create cache directories for models"""
        for model_info in self.models.values():
            cache_path = model_info['cache_path']
            os.makedirs(cache_path, exist_ok=True)
            logger.info(f"Created cache directory: {cache_path}")
    
    def is_model_cached(self, model_key: str) -> bool:
        """Check if model is already cached"""
        model_info = self.models[model_key]
        cache_path = model_info['cache_path']
        
        # Check for essential files
        essential_files = [
            'config.json',
            'tokenizer.json',
            'tokenizer_config.json',
            'vocab.json'
        ]
        
        # Check for model files (either pytorch_model.bin or model.safetensors)
        model_files = ['pytorch_model.bin', 'model.safetensors']
        
        try:
            # Check essential files
            for file in essential_files:
                if not os.path.exists(os.path.join(cache_path, file)):
                    return False
            
            # Check for at least one model file
            if not any(os.path.exists(os.path.join(cache_path, file)) for file in model_files):
                return False
            
            logger.info(f"Model {model_key} is already cached at {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking cache for {model_key}: {e}")
            return False
    
    def download_model(self, model_key: str) -> bool:
        """Download a specific model"""
        model_info = self.models[model_key]
        model_name = model_info['name']
        cache_path = model_info['cache_path']
        
        logger.info(f"Downloading {model_info['description']}...")
        logger.info(f"Model: {model_name}")
        logger.info(f"Cache path: {cache_path}")
        
        try:
            # Download tokenizer
            logger.info("Downloading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_info['tokenizer_name'],
                cache_dir=cache_path
            )
            tokenizer.save_pretrained(cache_path)
            
            # Download model
            logger.info("Downloading model...")
            model = model_info['model_class'].from_pretrained(
                model_name,
                cache_dir=cache_path
            )
            model.save_pretrained(cache_path)
            
            logger.info(f"Successfully downloaded {model_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {model_key}: {e}")
            return False
    
    def verify_model(self, model_key: str) -> bool:
        """Verify that a downloaded model works correctly"""
        model_info = self.models[model_key]
        cache_path = model_info['cache_path']
        
        try:
            logger.info(f"Verifying {model_key}...")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(cache_path)
            
            # Load model
            model = model_info['model_class'].from_pretrained(cache_path)
            
            # Test with a simple input
            test_input = "def hello_world():"
            tokens = tokenizer.encode(test_input, return_tensors='pt')
            
            # Test model inference
            with torch.no_grad():
                if model_key == 'codegpt':
                    output = model(tokens)
                    assert hasattr(output, 'logits'), "Model output should have logits"
                else:  # codebert
                    output = model(tokens)
                    assert hasattr(output, 'last_hidden_state'), "Model output should have last_hidden_state"
            
            logger.info(f"Model {model_key} verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Model {model_key} verification failed: {e}")
            return False
    
    def get_model_info(self, model_key: str) -> Dict:
        """Get detailed information about a model"""
        model_info = self.models[model_key]
        cache_path = model_info['cache_path']
        
        info = {
            'name': model_info['name'],
            'description': model_info['description'],
            'cache_path': cache_path,
            'cached': self.is_model_cached(model_key),
            'size': '0 MB'
        }
        
        if info['cached']:
            try:
                # Calculate cache size
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(cache_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                
                info['size'] = f"{total_size / (1024**2):.1f} MB"
            except Exception as e:
                logger.warning(f"Could not calculate size for {model_key}: {e}")
        
        return info
    
    def clean_cache(self, model_key: Optional[str] = None) -> None:
        """Clean model cache"""
        if model_key:
            if model_key in self.models:
                cache_path = self.models[model_key]['cache_path']
                if os.path.exists(cache_path):
                    shutil.rmtree(cache_path)
                    logger.info(f"Cleaned cache for {model_key}")
                else:
                    logger.info(f"No cache found for {model_key}")
            else:
                logger.error(f"Unknown model key: {model_key}")
        else:
            # Clean all caches
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                logger.info(f"Cleaned all model caches")
            else:
                logger.info("No cache directory found")
    
    def download_all_models(self) -> bool:
        """Download all required models"""
        logger.info("Starting model download process...")
        
        if not self.check_disk_space():
            logger.error("Insufficient disk space for model downloads")
            return False
        
        self.create_cache_directories()
        
        success = True
        for model_key in self.models.keys():
            if not self.force_download and self.is_model_cached(model_key):
                logger.info(f"Skipping {model_key} (already cached)")
                continue
            
            if not self.download_model(model_key):
                success = False
                continue
            
            if not self.verify_model(model_key):
                success = False
                continue
        
        return success
    
    def list_models(self) -> None:
        """List all available models and their status"""
        print("\nAvailable Models:")
        print("=" * 80)
        
        for model_key, model_info in self.models.items():
            info = self.get_model_info(model_key)
            status = "✓ Cached" if info['cached'] else "✗ Not cached"
            
            print(f"Model: {model_key}")
            print(f"  Name: {info['name']}")
            print(f"  Description: {info['description']}")
            print(f"  Status: {status}")
            print(f"  Size: {info['size']}")
            print(f"  Cache Path: {info['cache_path']}")
            print()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Download and setup AI models for code autocompletion"
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force download even if models are already cached'
    )
    
    parser.add_argument(
        '--cache-dir', '-c',
        type=str,
        help='Custom cache directory for models'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        choices=['codegpt', 'codebert'],
        help='Download specific model only'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available models and their status'
    )
    
    parser.add_argument(
        '--clean',
        type=str,
        nargs='?',
        const='all',
        help='Clean model cache (specify model name or "all")'
    )
    
    parser.add_argument(
        '--verify', '-v',
        action='store_true',
        help='Verify downloaded models'
    )
    
    args = parser.parse_args()
    
    # Create downloader instance
    downloader = ModelDownloader(
        force_download=args.force,
        cache_dir=args.cache_dir
    )
    
    # Handle different operations
    if args.list:
        downloader.list_models()
        return
    
    if args.clean:
        if args.clean == 'all':
            downloader.clean_cache()
        else:
            downloader.clean_cache(args.clean)
        return
    
    if args.verify:
        success = True
        models_to_verify = [args.model] if args.model else list(downloader.models.keys())
        
        for model_key in models_to_verify:
            if not downloader.verify_model(model_key):
                success = False
        
        sys.exit(0 if success else 1)
    
    # Download models
    try:
        if args.model:
            # Download specific model
            if downloader.download_model(args.model):
                if downloader.verify_model(args.model):
                    logger.info(f"Successfully setup {args.model}")
                    sys.exit(0)
                else:
                    logger.error(f"Failed to verify {args.model}")
                    sys.exit(1)
            else:
                logger.error(f"Failed to download {args.model}")
                sys.exit(1)
        else:
            # Download all models
            if downloader.download_all_models():
                logger.info("All models downloaded and verified successfully!")
                sys.exit(0)
            else:
                logger.error("Some models failed to download or verify")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()