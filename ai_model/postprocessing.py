import re
from typing import Dict, List, Any, Optional
import logging
import os

# Updated imports to use new config classes
from .model_configs.codebert_config import CodeBERTConfig
from .model_configs.codegpt_config import CodeGPTConfig

logger = logging.getLogger(__name__)

class CodePostprocessor:
    """
    Postprocessor for model outputs to improve completion quality
    """
    
    def __init__(self, model_type: str = 'codegpt'):
        """
        Initialize postprocessor with model configuration
        
        Args:
            model_type: Type of model ('codegpt' or 'codebert')
        """
        self.model_type = model_type
        
        # Initialize appropriate config
        if model_type.lower() == 'codebert':
            self.model_config = CodeBERTConfig()
        else:
            self.model_config = CodeGPTConfig()
        
        # Build language configs from model configuration
        self.language_configs = self._build_language_configs()
        
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    def _build_language_configs(self) -> Dict[str, Dict[str, Any]]:
        """Build language-specific configurations from model config"""
        configs = {}
        
        # Get supported languages from model config
        supported_languages = self.model_config.supported_languages
        
        # Default language mappings for postprocessing
        default_mappings = {
            'python': {
                'comment_prefix': '#',
                'string_delimiters': ['"', "'", '"""', "'''"],
                'block_keywords': ['if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'def', 'class', 'with'],
                'line_terminators': [':']
            },
            'javascript': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'", '`'],
                'block_keywords': ['if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'function'],
                'line_terminators': [';', '{', '}']
            },
            'typescript': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'", '`'],
                'block_keywords': ['if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'function', 'interface', 'type'],
                'line_terminators': [';', '{', '}']
            },
            'java': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'public', 'private', 'protected'],
                'line_terminators': [';', '{', '}']
            },
            'c': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'do', 'switch', 'case'],
                'line_terminators': [';', '{', '}']
            },
            'cpp': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'class', 'namespace'],
                'line_terminators': [';', '{', '}']
            },
            'c#': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'class', 'namespace'],
                'line_terminators': [';', '{', '}']
            },
            'go': {
                'comment_prefix': '//',
                'string_delimiters': ['"', '`'],
                'block_keywords': ['if', 'else', 'for', 'switch', 'case', 'func', 'type'],
                'line_terminators': ['{', '}']
            },
            'rust': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'match', 'fn', 'struct', 'enum', 'impl'],
                'line_terminators': [';', '{', '}']
            },
            'php': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'"],
                'block_keywords': ['if', 'else', 'elseif', 'for', 'while', 'foreach', 'function', 'class'],
                'line_terminators': [';', '{', '}']
            },
            'ruby': {
                'comment_prefix': '#',
                'string_delimiters': ['"', "'"],
                'block_keywords': ['if', 'else', 'elsif', 'for', 'while', 'def', 'class', 'module'],
                'line_terminators': ['end']
            },
            'swift': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'switch', 'case', 'func', 'class', 'struct'],
                'line_terminators': ['{', '}']
            },
            'kotlin': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'when', 'fun', 'class', 'interface'],
                'line_terminators': [';', '{', '}']
            },
            'scala': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'block_keywords': ['if', 'else', 'for', 'while', 'match', 'def', 'class', 'object'],
                'line_terminators': ['{', '}']
            },
            'html': {
                'comment_prefix': '<!--',
                'string_delimiters': ['"', "'"],
                'block_keywords': ['<div>', '<span>', '<p>', '<table>', '<form>'],
                'line_terminators': ['>', '/>']
            },
            'css': {
                'comment_prefix': '/*',
                'string_delimiters': ['"', "'"],
                'block_keywords': [],
                'line_terminators': [';', '{', '}']
            },
            'sql': {
                'comment_prefix': '--',
                'string_delimiters': ['"', "'"],
                'block_keywords': ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING'],
                'line_terminators': [';']
            },
            'bash': {
                'comment_prefix': '#',
                'string_delimiters': ['"', "'"],
                'block_keywords': ['if', 'else', 'elif', 'for', 'while', 'function'],
                'line_terminators': [';']
            },
            'powershell': {
                'comment_prefix': '#',
                'string_delimiters': ['"', "'"],
                'block_keywords': ['if', 'else', 'elseif', 'foreach', 'while', 'function'],
                'line_terminators': [';']
            }
        }
        
        # Build configs for each supported language
        for language in supported_languages:
            lang_config = default_mappings.get(language, default_mappings['python'])
            
            # Get language-specific config from model if available
            if hasattr(self.model_config, 'get_language_config'):
                model_lang_config = self.model_config.get_language_config(language)
                if model_lang_config:
                    # Merge with default config
                    lang_config = {**lang_config}
                    lang_config['indent_size'] = model_lang_config.get('indent_size', 4)
                    lang_config['comment_style'] = model_lang_config.get('comment_style', lang_config['comment_prefix'])
                    lang_config['indent_style'] = model_lang_config.get('indent_style', 'spaces')
            
            configs[language] = lang_config
        
        return configs
    
    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        if hasattr(self.model_config, 'detect_language_from_file'):
            return self.model_config.detect_language_from_file(file_path)
        
        # Fallback detection
        file_ext = os.path.splitext(file_path)[1].lower()
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'c#',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.ps1': 'powershell'
        }
        
        return extension_map.get(file_ext)
    
    def postprocess_completion(
        self, 
        completion: str, 
        original_context: str, 
        language: str = 'python',
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Postprocess a completion to improve quality and extract metadata
        
        Args:
            completion: Raw completion from model
            original_context: Original context that was completed
            language: Programming language
            file_path: Optional file path for language detection
            
        Returns:
            Dictionary with processed completion and metadata
        """
        try:
            # Detect language from file if not provided
            if file_path and not language:
                detected_lang = self.detect_language_from_file(file_path)
                if detected_lang:
                    language = detected_lang
            
            # Ensure language is supported
            if not self.model_config.is_language_supported(language):
                logger.warning(f"Language '{language}' not supported, falling back to python")
                language = 'python'
            
            # Get language-specific configuration
            config = self.language_configs.get(language, self.language_configs['python'])
            
            # Clean the completion
            cleaned_completion = self._clean_completion(completion)
            
            # Remove context repetition
            deduplicated_completion = self._remove_context_repetition(
                cleaned_completion, original_context
            )
            
            # Fix indentation using language-specific config
            fixed_completion = self._fix_indentation(
                deduplicated_completion, original_context, config
            )
            
            # Remove incomplete lines
            trimmed_completion = self._trim_incomplete_lines(fixed_completion, config)
            
            # Apply language-specific postprocessing
            processed_completion = self._apply_language_specific_processing(
                trimmed_completion, language, config
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                processed_completion, original_context, language
            )
            
            # Determine completion type
            completion_type = self._determine_completion_type(processed_completion, config)
            
            # Validate syntax
            is_valid = self._validate_syntax(processed_completion, language)
            
            result = {
                'text': processed_completion,
                'confidence': confidence,
                'type': completion_type,
                'is_valid': is_valid,
                'language': language,
                'metadata': {
                    'original_length': len(completion),
                    'processed_length': len(processed_completion),
                    'line_count': len(processed_completion.split('\n')),
                    'has_syntax_errors': not is_valid,
                    'confidence_level': self._get_confidence_level(confidence),
                    'model_type': self.model_type,
                    'language_config': config
                }
            }
            
            logger.debug(f"Postprocessed completion: {len(completion)} -> {len(processed_completion)} chars")
            return result
            
        except Exception as e:
            logger.error(f"Error postprocessing completion: {e}")
            return {
                'text': completion,
                'confidence': 0.3,
                'type': 'unknown',
                'is_valid': False,
                'language': language,
                'metadata': {'error': str(e)}
            }
    
    def _apply_language_specific_processing(
        self, 
        completion: str, 
        language: str, 
        config: Dict[str, Any]
    ) -> str:
        """Apply language-specific postprocessing"""
        try:
            # Get language-specific config from model if available
            if hasattr(self.model_config, 'get_language_config'):
                model_lang_config = self.model_config.get_language_config(language)
                
                if model_lang_config:
                    # Apply comment style formatting
                    completion = self._format_comments(completion, model_lang_config)
                    
                    # Apply indentation style
                    completion = self._apply_indentation_style(completion, model_lang_config)
            
            return completion
            
        except Exception as e:
            logger.warning(f"Error applying language-specific processing: {e}")
            return completion
    
    def _format_comments(self, completion: str, lang_config: Dict[str, Any]) -> str:
        """Format comments according to language style"""
        comment_style = lang_config.get('comment_style', '//')
        
        # Simple comment formatting - can be expanded
        lines = completion.split('\n')
        formatted_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') and comment_style != '#':
                # Convert Python-style comments to language-appropriate style
                if comment_style == '//':
                    formatted_line = line.replace('#', '//', 1)
                elif comment_style == '--':
                    formatted_line = line.replace('#', '--', 1)
                else:
                    formatted_line = line
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_indentation_style(self, completion: str, lang_config: Dict[str, Any]) -> str:
        """Apply indentation style (spaces vs tabs)"""
        indent_style = lang_config.get('indent_style', 'spaces')
        indent_size = lang_config.get('indent_size', 4)
        
        if indent_style == 'tabs':
            # Convert spaces to tabs
            lines = completion.split('\n')
            converted_lines = []
            
            for line in lines:
                if line.startswith(' '):
                    # Count leading spaces
                    leading_spaces = len(line) - len(line.lstrip())
                    if leading_spaces > 0:
                        # Convert to tabs
                        tab_count = leading_spaces // indent_size
                        remaining_spaces = leading_spaces % indent_size
                        new_line = '\t' * tab_count + ' ' * remaining_spaces + line.lstrip()
                        converted_lines.append(new_line)
                    else:
                        converted_lines.append(line)
                else:
                    converted_lines.append(line)
            
            return '\n'.join(converted_lines)
        
        return completion
    
    def _clean_completion(self, completion: str) -> str:
        """Clean the raw completion"""
        # Remove leading/trailing whitespace
        cleaned = completion.strip()
        
        # Remove control characters
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
        
        # Normalize line endings
        cleaned = re.sub(r'\r\n|\r', '\n', cleaned)
        
        # Remove excessive blank lines
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        return cleaned
    
    def _remove_context_repetition(self, completion: str, context: str) -> str:
        """Remove any repetition of the original context"""
        # Get the last few lines of context to check for repetition
        context_lines = context.split('\n')
        completion_lines = completion.split('\n')
        
        # Find where completion actually starts (not repeating context)
        start_idx = 0
        context_suffix = context_lines[-3:] if len(context_lines) >= 3 else context_lines
        
        for i, comp_line in enumerate(completion_lines):
            if i >= len(context_suffix):
                break
            
            # Check if completion line matches context
            if comp_line.strip() == context_suffix[i].strip():
                start_idx = i + 1
            else:
                break
        
        # Return completion without repetition
        return '\n'.join(completion_lines[start_idx:])
    
    def _fix_indentation(self, completion: str, context: str, config: Dict) -> str:
        """Fix indentation to match context"""
        context_lines = context.split('\n')
        completion_lines = completion.split('\n')
        
        # Determine expected indentation from context
        expected_indent = 0
        indent_size = config.get('indent_size', 4)
        
        for line in reversed(context_lines):
            if line.strip():
                expected_indent = len(line) - len(line.lstrip())
                
                # If line ends with colon (Python) or opening brace, increase indent
                if line.strip().endswith(':') or line.strip().endswith('{'):
                    expected_indent += indent_size
                break
        
        # Fix indentation of completion lines
        fixed_lines = []
        for line in completion_lines:
            if line.strip():  # Only fix non-empty lines
                # Calculate relative indentation
                current_indent = len(line) - len(line.lstrip())
                
                # Adjust to expected indentation
                if current_indent == 0 and expected_indent > 0:
                    # Add expected indentation
                    fixed_line = ' ' * expected_indent + line.lstrip()
                else:
                    # Preserve relative indentation
                    fixed_line = line
                
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _trim_incomplete_lines(self, completion: str, config: Dict) -> str:
        """Remove incomplete lines from the end"""
        lines = completion.split('\n')
        
        # Work backwards to find the last complete line
        complete_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if line appears incomplete
            if self._is_incomplete_line(stripped, config):
                # Don't include this line and stop here
                break
            
            complete_lines.append(line)
        
        # If we removed all lines, keep at least the first one
        if not complete_lines and lines:
            complete_lines = [lines[0]]
        
        return '\n'.join(complete_lines)
    
    def _is_incomplete_line(self, line: str, config: Dict) -> bool:
        """Check if a line appears incomplete"""
        if not line:
            return False
        
        # Check for incomplete string literals
        for delimiter in config['string_delimiters']:
            if line.count(delimiter) % 2 == 1:  # Odd number of delimiters
                return True
        
        # Check for incomplete expressions
        incomplete_patterns = [
            r'[+\-*/=]$',  # Ends with operator
            r'[,\[]$',     # Ends with comma or opening bracket
            r'^\s*[)}]',   # Starts with closing bracket (likely incomplete)
            r'[a-zA-Z_][a-zA-Z0-9_]*\s*\($',  # Function call without closing paren
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, line):
                return True
        
        # Language-specific incomplete patterns
        if 'python' in str(config):
            # Python: lines ending with backslash are continuation
            if line.endswith('\\'):
                return True
        
        return False
    
    def _calculate_confidence(self, completion: str, context: str, language: str) -> float:
        """Calculate confidence score for the completion"""
        if not completion or not completion.strip():
            return 0.0
        
        confidence_factors = []
        
        # Length factor (not too short, not too long)
        length_score = min(len(completion) / 100, 1.0)  # Normalize to 0-1
        if length_score < 0.1:
            length_score = 0.1  # Minimum score for very short completions
        confidence_factors.append(length_score)
        
        # Syntax validity factor
        syntax_score = 1.0 if self._validate_syntax(completion, language) else 0.5
        confidence_factors.append(syntax_score)
        
        # Indentation consistency factor
        indent_score = self._calculate_indentation_consistency(completion)
        confidence_factors.append(indent_score)
        
        # Context relevance factor
        relevance_score = self._calculate_context_relevance(completion, context)
        confidence_factors.append(relevance_score)
        
        # Completeness factor
        completeness_score = self._calculate_completeness(completion)
        confidence_factors.append(completeness_score)
        
        # Language-specific confidence factor
        lang_score = self._calculate_language_specific_confidence(completion, language)
        confidence_factors.append(lang_score)
        
        # Calculate weighted average
        weights = [0.1, 0.25, 0.15, 0.25, 0.15, 0.1]  # Prioritize syntax and relevance
        weighted_score = sum(f * w for f, w in zip(confidence_factors, weights))
        
        return max(0.0, min(1.0, weighted_score))
    
    def _calculate_language_specific_confidence(self, completion: str, language: str) -> float:
        """Calculate language-specific confidence score"""
        try:
            # Get language-specific patterns or keywords
            config = self.language_configs.get(language, {})
            keywords = config.get('block_keywords', [])
            
            # Check for presence of language-appropriate keywords
            keyword_count = 0
            for keyword in keywords:
                if keyword in completion:
                    keyword_count += 1
            
            # Normalize score
            if keywords:
                keyword_score = min(keyword_count / len(keywords), 1.0)
                return max(0.5, keyword_score)  # Minimum 0.5 for any language
            
            return 0.7  # Default for languages without specific keywords
            
        except Exception:
            return 0.7
    
    def _calculate_indentation_consistency(self, completion: str) -> float:
        """Calculate how consistent the indentation is"""
        lines = [line for line in completion.split('\n') if line.strip()]
        
        if len(lines) <= 1:
            return 1.0
        
        # Check if indentation follows a pattern
        indentations = [len(line) - len(line.lstrip()) for line in lines]
        
        # Check for consistent indentation levels
        unique_indents = set(indentations)
        if len(unique_indents) <= 2:  # At most 2 different indentation levels
            return 1.0
        elif len(unique_indents) <= 4:  # Reasonable number of levels
            return 0.8
        else:
            return 0.5
    
    def _calculate_context_relevance(self, completion: str, context: str) -> float:
        """Calculate how relevant the completion is to the context"""
        # Simple relevance based on common words/tokens
        context_tokens = set(re.findall(r'\b\w+\b', context.lower()))
        completion_tokens = set(re.findall(r'\b\w+\b', completion.lower()))
        
        if not context_tokens or not completion_tokens:
            return 0.5
        
        # Calculate overlap
        overlap = len(context_tokens & completion_tokens)
        relevance = overlap / max(len(context_tokens), len(completion_tokens))
        
        return min(1.0, relevance + 0.3)  # Add base relevance
    
    def _calculate_completeness(self, completion: str) -> float:
        """Calculate how complete the completion appears"""
        lines = completion.split('\n')
        
        if not lines:
            return 0.0
        
        # Check last line for completeness indicators
        last_line = lines[-1].strip()
        
        # Complete if ends with typical terminators
        complete_endings = [';', ':', '}', ')', ']', 'pass', 'return', 'break', 'continue']
        
        for ending in complete_endings:
            if last_line.endswith(ending):
                return 1.0
        
        # Partial completeness for other patterns
        if last_line and not last_line.endswith((',', '+', '-', '*', '/', '=')):
            return 0.8
        
        return 0.4
    
    def _determine_completion_type(self, completion: str, config: Dict) -> str:
        """Determine the type of completion"""
        lines = completion.split('\n')
        
        if len(lines) == 1:
            return 'single-line'
        elif len(lines) <= 5:
            return 'multi-line'
        else:
            return 'block'
    
    def _validate_syntax(self, completion: str, language: str) -> bool:
        """Basic syntax validation"""
        try:
            if language == 'python':
                return self._validate_python_syntax(completion)
            elif language in ['javascript', 'typescript']:
                return self._validate_javascript_syntax(completion)
            elif language == 'java':
                return self._validate_java_syntax(completion)
            else:
                return True  # Assume valid for unknown languages
        except:
            return False
    
    def _validate_python_syntax(self, completion: str) -> bool:
        """Validate Python syntax"""
        try:
            import ast
            # Try to parse as a statement or expression
            ast.parse(completion)
            return True
        except:
            # Try to parse as part of a larger structure
            try:
                ast.parse(f"def dummy():\n    {completion}")
                return True
            except:
                return False
    
    def _validate_javascript_syntax(self, completion: str) -> bool:
        """Basic JavaScript syntax validation"""
        # Simple checks for common syntax errors
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in completion:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return False
                if brackets[stack[-1]] != char:
                    return False
                stack.pop()
        
        # Check for balanced quotes
        single_quotes = completion.count("'")
        double_quotes = completion.count('"')
        
        return single_quotes % 2 == 0 and double_quotes % 2 == 0
    
    def _validate_java_syntax(self, completion: str) -> bool:
        """Basic Java syntax validation"""
        # Similar to JavaScript validation
        return self._validate_javascript_syntax(completion)
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level category"""
        if confidence >= self.confidence_thresholds['high']:
            return 'high'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'medium'
        elif confidence >= self.confidence_thresholds['low']:
            return 'low'
        else:
            return 'very_low'
    
    def filter_completions(
        self, 
        completions: List[Dict[str, Any]], 
        min_confidence: float = 0.5,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Filter and rank completions"""
        # Filter by confidence
        filtered = [comp for comp in completions if comp['confidence'] >= min_confidence]
        
        # Sort by confidence (descending)
        filtered.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Limit results
        return filtered[:max_results]
    
    def get_context_window(self, language: str) -> int:
        """Get context window size for a specific language"""
        if hasattr(self.model_config, 'get_context_window'):
            return self.model_config.get_context_window(language)
        return getattr(self.model_config, 'max_length', 1024)
    
    def update_model_config(self, model_type: str):
        """Update model configuration"""
        if model_type.lower() == 'codebert':
            self.model_config = CodeBERTConfig()
        else:
            self.model_config = CodeGPTConfig()
        
        self.model_type = model_type
        self.language_configs = self._build_language_configs()
        
        logger.info(f"Updated postprocessor for model type: {model_type}")
