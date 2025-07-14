"""
Dataset loader for various programming languages
"""
import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
from datasets import Dataset, load_dataset
import requests
from tqdm import tqdm

# Import new configs
from ..ai_model.model_configs.codebert_config import CodeBERTConfig
from ..ai_model.model_configs.codegpt_config import CodeGPTConfig

logger = logging.getLogger(__name__)

class DatasetLoader:
    """Load and manage datasets for different programming languages"""
    
    def __init__(self, config_type: str = "codegpt"):
        """
        Initialize dataset loader
        
        Args:
            config_type: Type of config to use ('codebert' or 'codegpt')
        """
        if config_type == "codebert":
            self.config = CodeBERTConfig()
        else:
            self.config = CodeGPTConfig()
        
        self.config_type = config_type
        self.supported_languages = self.config.supported_languages
        
        # Dataset sources
        self.dataset_sources = {
            "python": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/python/", "datasets/python/"],
                "extensions": [".py", ".pyx", ".pyi"],
                "filters": {"language": "Python"}
            },
            "javascript": {
                "huggingface": "codeparrot/github-code-clean", 
                "local_paths": ["data/javascript/", "datasets/js/"],
                "extensions": [".js", ".jsx", ".mjs"],
                "filters": {"language": "JavaScript"}
            },
            "typescript": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/typescript/", "datasets/ts/"],
                "extensions": [".ts", ".tsx"],
                "filters": {"language": "TypeScript"}
            },
            "java": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/java/", "datasets/java/"],
                "extensions": [".java"],
                "filters": {"language": "Java"}
            },
            "go": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/go/", "datasets/go/"],
                "extensions": [".go"],
                "filters": {"language": "Go"}
            },
            "rust": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/rust/", "datasets/rust/"],
                "extensions": [".rs"],
                "filters": {"language": "Rust"}
            },
            "cpp": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/cpp/", "datasets/cpp/"],
                "extensions": [".cpp", ".cc", ".cxx", ".c++"],
                "filters": {"language": "C++"}
            },
            "c": {
                "huggingface": "codeparrot/github-code-clean",
                "local_paths": ["data/c/", "datasets/c/"],
                "extensions": [".c", ".h"],
                "filters": {"language": "C"}
            }
        }
        
        # Data paths
        self.data_dir = Path("data")
        self.cache_dir = Path("cache")
        self.processed_dir = Path("processed")
        
        # Create directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        for dir_path in [self.data_dir, self.cache_dir, self.processed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create language-specific subdirectories
            for lang in self.supported_languages:
                (dir_path / lang).mkdir(parents=True, exist_ok=True)
    
    def load_huggingface_dataset(self, language: str, split: str = "train", 
                                num_samples: Optional[int] = None) -> Dataset:
        """
        Load dataset from Hugging Face Hub
        
        Args:
            language: Programming language
            split: Dataset split ('train', 'test', 'validation')
            num_samples: Number of samples to load (None for all)
            
        Returns:
            Dataset object
        """
        if language not in self.supported_languages:
            raise ValueError(f"Language {language} not supported")
        
        try:
            source_info = self.dataset_sources[language]
            dataset_name = source_info["huggingface"]
            filters = source_info.get("filters", {})
            
            logger.info(f"Loading {language} dataset from {dataset_name}")
            
            # Load dataset
            dataset = load_dataset(
                dataset_name,
                split=split,
                streaming=num_samples is not None
            )
            
            # Filter by language if needed
            if filters:
                dataset = dataset.filter(
                    lambda x: any(f in str(x).lower() for f in filters.values())
                )
            
            # Limit samples if specified
            if num_samples:
                dataset = dataset.take(num_samples)
            
            # Cache the dataset
            cache_path = self.cache_dir / language / f"{split}_dataset.json"
            self._save_dataset_cache(dataset, cache_path)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to load {language} dataset: {e}")
            raise
    
    def load_local_dataset(self, language: str, data_path: str) -> List[Dict]:
        """
        Load dataset from local files
        
        Args:
            language: Programming language
            data_path: Path to local data directory
            
        Returns:
            List of code samples
        """
        if language not in self.supported_languages:
            raise ValueError(f"Language {language} not supported")
        
        data_path = Path(data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Data path {data_path} does not exist")
        
        source_info = self.dataset_sources[language]
        extensions = source_info["extensions"]
        
        samples = []
        
        # Walk through directory and collect code files
        for ext in extensions:
            files = list(data_path.rglob(f"*{ext}"))
            
            for file_path in tqdm(files, desc=f"Loading {language} files"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Get context window for the language
                    max_length = self.config.get_context_window(language) if hasattr(self.config, 'get_context_window') else self.config.max_length
                    
                    # Skip very short or very long files
                    if 50 <= len(content) <= max_length * 10:
                        sample = {
                            "text": content,
                            "language": language,
                            "file_path": str(file_path),
                            "file_name": file_path.name,
                            "file_size": len(content),
                            "extension": ext
                        }
                        samples.append(sample)
                        
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue
        
        logger.info(f"Loaded {len(samples)} {language} samples from local files")
        return samples
    
    def create_completion_dataset(self, samples: List[Dict], 
                                 context_window: int = 512) -> List[Dict]:
        """
        Create completion dataset from code samples
        
        Args:
            samples: List of code samples
            context_window: Context window size
            
        Returns:
            List of completion examples
        """
        completion_samples = []
        
        for sample in tqdm(samples, desc="Creating completion examples"):
            text = sample["text"]
            language = sample["language"]
            
            # Get language-specific config
            lang_config = {}
            if hasattr(self.config, 'get_language_config'):
                lang_config = self.config.get_language_config(language)
            
            # Split text into lines
            lines = text.split('\n')
            
            # Create multiple completion examples per sample
            for i in range(1, len(lines) - 1):  # Skip first and last line
                context_lines = lines[:i]
                target_line = lines[i]
                
                # Skip empty target lines
                if not target_line.strip():
                    continue
                
                # Create context
                context = '\n'.join(context_lines)
                
                # Limit context to window size
                if len(context) > context_window:
                    context = context[-context_window:]
                
                completion_example = {
                    "context": context,
                    "target": target_line,
                    "language": language,
                    "file_name": sample.get("file_name", "unknown"),
                    "line_number": i + 1,
                    "context_length": len(context),
                    "target_length": len(target_line)
                }
                
                # Add language-specific metadata
                if lang_config:
                    completion_example["language_config"] = {
                        "comment_style": lang_config.get("comment_style", "//"),
                        "indent_style": lang_config.get("indent_style", "spaces"),
                        "indent_size": lang_config.get("indent_size", 4)
                    }
                
                completion_samples.append(completion_example)
        
        return completion_samples
    
    def load_and_prepare_dataset(self, language: str, source: str = "local", 
                                data_path: Optional[str] = None, 
                                num_samples: Optional[int] = None) -> List[Dict]:
        """
        Load and prepare dataset for training
        
        Args:
            language: Programming language
            source: Data source ('local' or 'huggingface')
            data_path: Path to local data (if source is 'local')
            num_samples: Number of samples to load
            
        Returns:
            Prepared dataset
        """
        if source == "local":
            if not data_path:
                # Try default local paths
                for path in self.dataset_sources[language]["local_paths"]:
                    if Path(path).exists():
                        data_path = path
                        break
                else:
                    raise ValueError(f"No local data path found for {language}")
            
            samples = self.load_local_dataset(language, data_path)
        
        elif source == "huggingface":
            hf_dataset = self.load_huggingface_dataset(language, num_samples=num_samples)
            samples = [{"text": item["text"], "language": language} for item in hf_dataset]
        
        else:
            raise ValueError(f"Unknown source: {source}")
        
        # Limit samples if specified
        if num_samples and len(samples) > num_samples:
            samples = samples[:num_samples]
        
        # Get context window for the language
        context_window = self.config.max_length
        if hasattr(self.config, 'get_context_window'):
            context_window = self.config.get_context_window(language)
        
        # Create completion dataset
        completion_dataset = self.create_completion_dataset(samples, context_window)
        
        return completion_dataset
    
    def save_dataset(self, dataset: List[Dict], language: str, 
                    dataset_type: str = "completion") -> str:
        """
        Save dataset to disk
        
        Args:
            dataset: Dataset to save
            language: Programming language
            dataset_type: Type of dataset ('completion', 'raw', etc.)
            
        Returns:
            Path to saved dataset
        """
        filename = f"{language}_{dataset_type}_dataset.json"
        filepath = self.processed_dir / language / filename
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(dataset)} samples to {filepath}")
        return str(filepath)
    
    def load_saved_dataset(self, language: str, dataset_type: str = "completion") -> List[Dict]:
        """
        Load saved dataset from disk
        
        Args:
            language: Programming language
            dataset_type: Type of dataset
            
        Returns:
            Loaded dataset
        """
        filename = f"{language}_{dataset_type}_dataset.json"
        filepath = self.processed_dir / language / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset {filepath} not found")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        logger.info(f"Loaded {len(dataset)} samples from {filepath}")
        return dataset
    
    def _save_dataset_cache(self, dataset: Dataset, cache_path: Path):
        """Save dataset to cache"""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dataset to list for JSON serialization
        dataset_list = []
        for item in dataset:
            dataset_list.append(item)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_list, f, indent=2, ensure_ascii=False)
    
    def get_dataset_stats(self, dataset: List[Dict]) -> Dict:
        """
        Get statistics about the dataset
        
        Args:
            dataset: Dataset to analyze
            
        Returns:
            Statistics dictionary
        """
        if not dataset:
            return {"total_samples": 0}
        
        stats = {
            "total_samples": len(dataset),
            "languages": {},
            "avg_context_length": 0,
            "avg_target_length": 0,
            "min_context_length": float('inf'),
            "max_context_length": 0,
            "min_target_length": float('inf'),
            "max_target_length": 0
        }
        
        context_lengths = []
        target_lengths = []
        
        for sample in dataset:
            language = sample.get("language", "unknown")
            context_length = sample.get("context_length", len(sample.get("context", "")))
            target_length = sample.get("target_length", len(sample.get("target", "")))
            
            # Language distribution
            stats["languages"][language] = stats["languages"].get(language, 0) + 1
            
            # Length statistics
            context_lengths.append(context_length)
            target_lengths.append(target_length)
            
            stats["min_context_length"] = min(stats["min_context_length"], context_length)
            stats["max_context_length"] = max(stats["max_context_length"], context_length)
            stats["min_target_length"] = min(stats["min_target_length"], target_length)
            stats["max_target_length"] = max(stats["max_target_length"], target_length)
        
        # Calculate averages
        if context_lengths:
            stats["avg_context_length"] = sum(context_lengths) / len(context_lengths)
        if target_lengths:
            stats["avg_target_length"] = sum(target_lengths) / len(target_lengths)
        
        return stats
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language: str) -> bool:
        """Check if language is supported"""
        return self.config.is_language_supported(language)


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = DatasetLoader(config_type="codegpt")
    
    # Load and prepare Python dataset
    python_dataset = loader.load_and_prepare_dataset(
        language="python",
        source="local",
        data_path="data/python",
        num_samples=1000
    )
    
    # Save dataset
    loader.save_dataset(python_dataset, "python", "completion")
    
    # Get statistics
    stats = loader.get_dataset_stats(python_dataset)
    print(f"Dataset stats: {stats}")