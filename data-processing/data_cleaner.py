"""
Data cleaning and filtering utilities for code datasets
"""
import re
import ast
import json
import logging
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
import hashlib
from collections import defaultdict
import unicodedata

# Import new configs
from ..ai_model.model_configs.codebert_config import CodeBERTConfig
from ..ai_model.model_configs.codegpt_config import CodeGPTConfig

logger = logging.getLogger(__name__)

class DataCleaner:
    """Clean and filter code datasets"""
    
    def __init__(self, config_type: str = "codegpt"):
        """
        Initialize data cleaner
        
        Args:
            config_type: Type of config to use ('codebert' or 'codegpt')
        """
        if config_type == "codebert":
            self.config = CodeBERTConfig()
        else:
            self.config = CodeGPTConfig()
        
        self.config_type = config_type
        self.supported_languages = self.config.supported_languages
        
        # Language-specific patterns
        self.language_patterns = {
            "python": {
                "comment_patterns": [r'#.*$', r'""".*?"""', r"'''.*?'''"],
                "string_patterns": [r'"[^"]*"', r"'[^']*'", r'""".*?"""', r"'''.*?'''"],
                "import_patterns": [r'^import\s+\w+', r'^from\s+\w+\s+import'],
                "function_patterns": [r'def\s+\w+\s*\(', r'class\s+\w+\s*\('],
                "invalid_patterns": [r'^\s*$', r'^\s*#.*$'],
                "syntax_check": True
            },
            "javascript": {
                "comment_patterns": [r'//.*$', r'/\*.*?\*/'],
                "string_patterns": [r'"[^"]*"', r"'[^']*'", r'`[^`]*`'],
                "import_patterns": [r'import\s+.*from', r'require\s*\('],
                "function_patterns": [r'function\s+\w+\s*\(', r'const\s+\w+\s*=', r'let\s+\w+\s*='],
                "invalid_patterns": [r'^\s*$', r'^\s*//.*$'],
                "syntax_check": False
            },
            "typescript": {
                "comment_patterns": [r'//.*$', r'/\*.*?\*/'],
                "string_patterns": [r'"[^"]*"', r"'[^']*'", r'`[^`]*`'],
                "import_patterns": [r'import\s+.*from', r'require\s*\('],
                "function_patterns": [r'function\s+\w+\s*\(', r'const\s+\w+\s*:', r'let\s+\w+\s*:'],
                "invalid_patterns": [r'^\s*$', r'^\s*//.*$'],
                "syntax_check": False
            },
            "java": {
                "comment_patterns": [r'//.*$', r'/\*.*?\*/'],
                "string_patterns": [r'"[^"]*"'],
                "import_patterns": [r'import\s+[\w.]+;'],
                "function_patterns": [r'public\s+.*\s+\w+\s*\(', r'private\s+.*\s+\w+\s*\('],
                "invalid_patterns": [r'^\s*$', r'^\s*//.*$'],
                "syntax_check": False
            }
        }
        
        # Quality filters
        self.quality_filters = {
            "min_length": 20,
            "max_length": 10000,
            "min_lines": 2,
            "max_lines": 500,
            "min_tokens": 5,
            "max_tokens": 2000,
            "min_code_ratio": 0.3,  # Minimum ratio of code to comments
            "max_duplicate_lines": 0.7,  # Maximum ratio of duplicate lines
            "min_complexity": 1,  # Minimum cyclomatic complexity
            "max_complexity": 50   # Maximum cyclomatic complexity
        }
        
        # Deduplication
        self.seen_hashes = set()
        self.duplicate_count = 0
        
        # Statistics
        self.stats = {
            "total_samples": 0,
            "filtered_samples": 0,
            "duplicate_samples": 0,
            "invalid_syntax": 0,
            "too_short": 0,
            "too_long": 0,
            "low_quality": 0,
            "cleaned_samples": 0
        }
    
    def clean_text(self, text: str, language: str) -> str:
        """
        Clean text content
        
        Args:
            text: Raw text content
            language: Programming language
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces
        
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
        # Language-specific cleaning
        if language in self.language_patterns:
            text = self._clean_language_specific(text, language)
        
        return text.strip()
    
    def _clean_language_specific(self, text: str, language: str) -> str:
        """Apply language-specific cleaning"""
        patterns = self.language_patterns[language]
        
        # Remove excessive comments (keep some for context)
        comment_patterns = patterns.get("comment_patterns", [])
        for pattern in comment_patterns:
            # Count comment lines
            comment_lines = len(re.findall(pattern, text, re.MULTILINE))
            total_lines = len(text.split('\n'))
            
            # If more than 70% are comments, it's likely documentation
            if total_lines > 0 and comment_lines / total_lines > 0.7:
                return ""  # Skip this sample
        
        return text
    
    def is_valid_syntax(self, text: str, language: str) -> bool:
        """
        Check if code has valid syntax
        
        Args:
            text: Code text
            language: Programming language
            
        Returns:
            True if syntax is valid
        """
        if not text.strip():
            return False
        
        # Python syntax validation
        if language == "python":
            try:
                ast.parse(text)
                return True
            except SyntaxError:
                return False
        
        # For other languages, use basic pattern matching
        patterns = self.language_patterns.get(language, {})
        invalid_patterns = patterns.get("invalid_patterns", [])
        
        # Check for invalid patterns
        for pattern in invalid_patterns:
            if re.search(pattern, text, re.MULTILINE):
                continue
        
        # Basic validation: should contain some code constructs
        function_patterns = patterns.get("function_patterns", [])
        has_code_constructs = any(re.search(pattern, text, re.MULTILINE) for pattern in function_patterns)
        
        return has_code_constructs or len(text.split('\n')) > 5
    
    def calculate_code_quality(self, text: str, language: str) -> Dict[str, float]:
        """
        Calculate code quality metrics
        
        Args:
            text: Code text
            language: Programming language
            
        Returns:
            Quality metrics dictionary
        """
        if not text:
            return {"overall_score": 0.0}
        
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        metrics = {
            "length": len(text),
            "lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "avg_line_length": sum(len(line) for line in non_empty_lines) / max(len(non_empty_lines), 1),
            "code_ratio": 0.0,
            "complexity": 0.0,
            "duplicate_ratio": 0.0,
            "overall_score": 0.0
        }
        
        # Calculate code vs comment ratio
        if language in self.language_patterns:
            patterns = self.language_patterns[language]
            comment_patterns = patterns.get("comment_patterns", [])
            
            comment_lines = 0
            for pattern in comment_patterns:
                comment_lines += len(re.findall(pattern, text, re.MULTILINE))
            
            metrics["code_ratio"] = max(0, (len(non_empty_lines) - comment_lines) / max(len(non_empty_lines), 1))
        
        # Calculate complexity (simplified)
        complexity_keywords = ['if', 'else', 'elif', 'for', 'while', 'try', 'except', 'catch', 'switch', 'case']
        complexity_count = sum(len(re.findall(rf'\b{keyword}\b', text, re.IGNORECASE)) for keyword in complexity_keywords)
        metrics["complexity"] = complexity_count / max(len(non_empty_lines), 1)
        
        # Calculate duplicate lines ratio
        line_counts = defaultdict(int)
        for line in non_empty_lines:
            normalized_line = re.sub(r'\s+', ' ', line.strip())
            if normalized_line:
                line_counts[normalized_line] += 1
        
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        metrics["duplicate_ratio"] = duplicate_lines / max(len(non_empty_lines), 1)
        
        # Calculate overall score
        score = 0.0
        
        # Length score (0-1)
        length_score = min(1.0, max(0.0, (metrics["length"] - 20) / 1000))
        score += length_score * 0.2
        
        # Code ratio score (0-1)
        score += metrics["code_ratio"] * 0.3
        
        # Complexity score (0-1)
        complexity_score = min(1.0, max(0.0, metrics["complexity"] / 0.5))
        score += complexity_score * 0.2
        
        # Duplicate penalty
        duplicate_penalty = max(0.0, 1.0 - metrics["duplicate_ratio"] * 2)
        score += duplicate_penalty * 0.3
        
        metrics["overall_score"] = score
        
        return metrics
    
    def is_duplicate(self, text: str) -> bool:
        """
        Check if text is a duplicate
        
        Args:
            text: Text to check
            
        Returns:
            True if duplicate
        """
        # Create hash of normalized text
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        text_hash = hashlib.md5(normalized.encode()).hexdigest()
        
        if text_hash in self.seen_hashes:
            self.duplicate_count += 1
            return True
        
        self.seen_hashes.add(text_hash)
        return False
    
    def filter_sample(self, sample: Dict) -> Tuple[bool, str]:
        """
        Filter a single sample
        
        Args:
            sample: Sample to filter
            
        Returns:
            Tuple of (is_valid, reason)
        """
        text = sample.get("text", "")
        language = sample.get("language", "unknown")
        
        # Basic validation
        if not text or not isinstance(text, str):
            return False, "empty_or_invalid_text"
        
        # Check language support
        if language not in self.supported_languages:
            return False, "unsupported_language"
        
        # Check for duplicates
        if self.is_duplicate(text):
            return False, "duplicate"
        
        # Length filters
        if len(text) < self.quality_filters["min_length"]:
            return False, "too_short"
        
        if len(text) > self.quality_filters["max_length"]:
            return False, "too_long"
        
        # Line count filters
        lines = text.split('\n')
        if len(lines) < self.quality_filters["min_lines"]:
            return False, "too_few_lines"
        
        if len(lines) > self.quality_filters["max_lines"]:
            return False, "too_many_lines"
        
        # Syntax validation
        if not self.is_valid_syntax(text, language):
            return False, "invalid_syntax"
        
        # Quality assessment
        quality_metrics = self.calculate_code_quality(text, language)
        
        if quality_metrics["code_ratio"] < self.quality_filters["min_code_ratio"]:
            return False, "low_code_ratio"
        
        if quality_metrics["duplicate_ratio"] > self.quality_filters["max_duplicate_lines"]:
            return False, "high_duplicate_ratio"
        
        if quality_metrics["overall_score"] < 0.3:  # Minimum quality threshold
            return False, "low_quality"
        
        return True, "valid"
    
    def clean_dataset(self, dataset: List[Dict]) -> List[Dict]:
        """
        Clean and filter entire dataset
        
        Args:
            dataset: List of samples to clean
            
        Returns:
            Cleaned dataset
        """
        cleaned_dataset = []
        
        for sample in dataset:
            self.stats["total_samples"] += 1
            
            # Clean text
            text = sample.get("text", "")
            language = sample.get("language", "unknown")
            
            if text:
                cleaned_text = self.clean_text(text, language)
                sample["text"] = cleaned_text
            
            # Filter sample
            is_valid, reason = self.filter_sample(sample)
            
            if is_valid:
                cleaned_dataset.append(sample)
                self.stats["cleaned_samples"] += 1
            else:
                self.stats["filtered_samples"] += 1
                
                # Track specific filter reasons
                if reason == "duplicate":
                    self.stats["duplicate_samples"] += 1
                elif reason == "invalid_syntax":
                    self.stats["invalid_syntax"] += 1
                elif reason in ["too_short", "too_few_lines"]:
                    self.stats["too_short"] += 1
                elif reason in ["too_long", "too_many_lines"]:
                    self.stats["too_long"] += 1
                elif reason in ["low_code_ratio", "high_duplicate_ratio", "low_quality"]:
                    self.stats["low_quality"] += 1
        
        return cleaned_dataset
    
    def save_cleaned_dataset(self, dataset: List[Dict], output_path: str):
        """
        Save cleaned dataset to file
        
        Args:
            dataset: Cleaned dataset
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in dataset:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(dataset)} cleaned samples to {output_path}")
    
    def get_statistics(self) -> Dict:
        """Get cleaning statistics"""
        stats = self.stats.copy()
        
        if stats["total_samples"] > 0:
            stats["filter_rate"] = stats["filtered_samples"] / stats["total_samples"]
            stats["duplicate_rate"] = stats["duplicate_samples"] / stats["total_samples"]
            stats["clean_rate"] = stats["cleaned_samples"] / stats["total_samples"]
        
        return stats
    
    def print_statistics(self):
        """Print cleaning statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("DATA CLEANING STATISTICS")
        print("="*50)
        print(f"Total samples: {stats['total_samples']}")
        print(f"Cleaned samples: {stats['cleaned_samples']}")
        print(f"Filtered samples: {stats['filtered_samples']}")
        print(f"Filter rate: {stats.get('filter_rate', 0):.2%}")
        print(f"Clean rate: {stats.get('clean_rate', 0):.2%}")
        print("\nFilter breakdown:")
        print(f"- Duplicates: {stats['duplicate_samples']}")
        print(f"- Invalid syntax: {stats['invalid_syntax']}")
        print(f"- Too short: {stats['too_short']}")
        print(f"- Too long: {stats['too_long']}")
        print(f"- Low quality: {stats['low_quality']}")
        print("="*50)
    
    def reset_statistics(self):
        """Reset all statistics"""
        self.stats = {
            "total_samples": 0,
            "filtered_samples": 0,
            "duplicate_samples": 0,
            "invalid_syntax": 0,
            "too_short": 0,
            "too_long": 0,
            "low_quality": 0,
            "cleaned_samples": 0
        }
        self.seen_hashes.clear()
        self.duplicate_count = 0

# Example usage
def main():
    """Example usage of DataCleaner"""
    
    # Sample dataset
    sample_data = [
        {
            "text": "def hello_world():\n    print('Hello, World!')\n    return True",
            "language": "python"
        },
        {
            "text": "x = 1",  # Too short
            "language": "python"
        },
        {
            "text": "function greet(name) {\n    console.log('Hello, ' + name);\n}",
            "language": "javascript"
        },
        {
            "text": "def hello_world():\n    print('Hello, World!')\n    return True",  # Duplicate
            "language": "python"
        }
    ]
    
    # Initialize cleaner
    cleaner = DataCleaner(config_type="codegpt")
    
    # Clean dataset
    cleaned_data = cleaner.clean_dataset(sample_data)
    
    # Print statistics
    cleaner.print_statistics()
    
    # Save cleaned dataset
    cleaner.save_cleaned_dataset(cleaned_data, "cleaned_dataset.jsonl")

if __name__ == "__main__":
    main()