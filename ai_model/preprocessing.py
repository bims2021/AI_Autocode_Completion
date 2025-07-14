import re
from typing import Dict, List, Any, Optional
import logging

# NEW: Import new config classes
from .model_configs.codebert_config import CodeBERTConfig
from .model_configs.codegpt_config import CodeGPTConfig

logger = logging.getLogger(__name__)

class CodePreprocessor:
    """
    Preprocessor for code context before model inference
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize preprocessor with configuration
        
        Args:
            config: Model configuration dictionary (from new config classes)
        """
        self.config = config or {}
        
        # Extract max_context_length from config, with fallback
        self.max_context_length = self.config.get('max_length', 2048)
        self.min_context_length = 10
        
        # Language-specific configurations - now enhanced with config data
        self.language_configs = {
            'python': {
                'comment_prefix': '#',
                'string_delimiters': ['"', "'", '"""', "'''"],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'try', 'except'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '//', '%', '**'],
                'file_extensions': ['.py', '.pyx', '.pyi']
            },
            'javascript': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'", '`'],
                'indent_size': 2,
                'indent_style': 'spaces',
                'keywords': ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'try', 'catch'],
                'operators': ['=', '==', '===', '!=', '!==', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.js', '.jsx', '.mjs']
            },
            'typescript': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'", '`'],
                'indent_size': 2,
                'indent_style': 'spaces',
                'keywords': ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'try', 'catch', 'interface', 'type'],
                'operators': ['=', '==', '===', '!=', '!==', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.ts', '.tsx']
            },
            'java': {
                'comment_prefix': '//',
                'string_delimiters': ['"'],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['public', 'private', 'protected', 'class', 'interface', 'if', 'else', 'for', 'while', 'try', 'catch'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.java']
            },
            'cpp': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'"],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['class', 'struct', 'namespace', 'if', 'else', 'for', 'while', 'try', 'catch'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.cpp', '.cc', '.cxx', '.c++']
            },
            'c': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'"],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['struct', 'typedef', 'if', 'else', 'for', 'while', 'switch', 'case'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.c', '.h']
            },
            'c#': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'"],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['class', 'interface', 'namespace', 'public', 'private', 'protected', 'if', 'else', 'for', 'while', 'try', 'catch'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.cs']
            },
            'go': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'", '`'],
                'indent_size': 1,
                'indent_style': 'tabs',
                'keywords': ['func', 'package', 'import', 'if', 'else', 'for', 'switch', 'case', 'type', 'struct'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.go']
            },
            'rust': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'"],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['fn', 'struct', 'enum', 'impl', 'trait', 'if', 'else', 'for', 'while', 'match'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.rs']
            },
            'php': {
                'comment_prefix': '//',
                'string_delimiters': ['"', "'"],
                'indent_size': 4,
                'indent_style': 'spaces',
                'keywords': ['function', 'class', 'interface', 'if', 'else', 'for', 'while', 'try', 'catch'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.php', '.phtml']
            },
            'ruby': {
                'comment_prefix': '#',
                'string_delimiters': ['"', "'"],
                'indent_size': 2,
                'indent_style': 'spaces',
                'keywords': ['def', 'class', 'module', 'if', 'else', 'for', 'while', 'begin', 'rescue'],
                'operators': ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '%'],
                'file_extensions': ['.rb', '.rbw']
            },
            'html': {
                'comment_prefix': '<!-- -->',
                'string_delimiters': ['"', "'"],
                'indent_size': 2,
                'indent_style': 'spaces',
                'keywords': ['html', 'head', 'body', 'div', 'span', 'p', 'a', 'img'],
                'operators': ['='],
                'file_extensions': ['.html', '.htm', '.xhtml']
            },
            'css': {
                'comment_prefix': '/* */',
                'string_delimiters': ['"', "'"],
                'indent_size': 2,
                'indent_style': 'spaces',
                'keywords': ['@media', '@import', '@keyframes', 'color', 'background', 'margin', 'padding'],
                'operators': [':'],
                'file_extensions': ['.css', '.scss', '.sass', '.less']
            },
            'sql': {
                'comment_prefix': '--',
                'string_delimiters': ['"', "'"],
                'indent_size': 2,
                'indent_style': 'spaces',
                'keywords': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP'],
                'operators': ['=', '!=', '<', '>', '<=', '>='],
                'file_extensions': ['.sql']
            }
        }
        
        # Update language configs with data from new config classes if available
        self._update_language_configs_from_config()

    def _update_language_configs_from_config(self):
        """Update language configurations with data from new config classes"""
        if 'language_config' in self.config:
            lang_config = self.config['language_config']
            
            # Update specific language config if provided
            if 'language' in self.config:
                language = self.config['language']
                if language in self.language_configs:
                    self.language_configs[language].update({
                        'comment_style': lang_config.get('comment_style', '//'),
                        'indent_style': lang_config.get('indent_style', 'spaces'),
                        'indent_size': lang_config.get('indent_size', 4),
                        'file_extensions': lang_config.get('file_extensions', []),
                        'context_window': lang_config.get('context_window', self.max_context_length)
                    })
                    
                    # Update max_context_length if context_window is specified
                    if 'context_window' in lang_config:
                        self.max_context_length = lang_config['context_window']

    def preprocess_context(self, context: str, language: str = 'python') -> str:
        """
        Preprocess code context for model input

        Args:
            context: Raw code context
            language: Programming language

        Returns:
            Preprocessed context string
        """
        try:
            # Get language config, fallback to python if not found
            config = self.language_configs.get(language, self.language_configs['python'])
            
            # Get language-specific context window size
            context_window = self._get_context_window(language)

            # Clean and normalize context
            cleaned_context = self._clean_context(context)

            # Normalize whitespace and indentation
            normalized_context = self._normalize_indentation(cleaned_context, config)

            # Remove excessive blank lines
            normalized_context = self._remove_excessive_blank_lines(normalized_context)

            # Truncate if too long (use language-specific context window)
            if len(normalized_context) > context_window:
                normalized_context = self._smart_truncate(normalized_context, language, context_window)

            # Ensure minimum length
            if len(normalized_context) < self.min_context_length:
                normalized_context = self._pad_context(normalized_context, language)

            # Add language-specific preprocessing
            processed_context = self._language_specific_preprocessing(normalized_context, language)

            logger.debug(f"Preprocessed context for {language}: {len(context)} -> {len(processed_context)} chars")
            return processed_context

        except Exception as e:
            logger.error(f"Error preprocessing context for {language}: {e}")
            return context  # Return original if preprocessing fails

    def _get_context_window(self, language: str) -> int:
        """Get context window size for specific language"""
        if hasattr(self, 'config') and 'language_config' in self.config:
            return self.config['language_config'].get('context_window', self.max_context_length)
        
        # Check if language config has context_window
        lang_config = self.language_configs.get(language, {})
        return lang_config.get('context_window', self.max_context_length)

    def _clean_context(self, context: str) -> str:
        """Clean the context of unwanted characters"""
        # Remove null bytes and other control characters
        context = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', context)

        # Normalize line endings
        context = re.sub(r'\r\n|\r', '\n', context)

        # Remove trailing whitespace from lines
        lines = context.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]

        return '\n'.join(cleaned_lines)

    def _normalize_indentation(self, context: str, config: Dict) -> str:
        """Normalize indentation to consistent format based on language config"""
        lines = context.split('\n')
        normalized_lines = []
        
        indent_size = config.get('indent_size', 4)
        indent_style = config.get('indent_style', 'spaces')

        for line in lines:
            if line.strip():  # Only process non-empty lines
                # Convert tabs to spaces first for consistent processing
                line_no_tabs = line.expandtabs(indent_size)
                
                # Calculate leading spaces
                leading_spaces = len(line_no_tabs) - len(line_no_tabs.lstrip())
                
                # Normalize to multiple of indent_size
                normalized_indent_level = leading_spaces // indent_size
                
                # Apply correct indentation style
                if indent_style == 'tabs':
                    normalized_line = '\t' * normalized_indent_level + line_no_tabs.lstrip()
                else:  # spaces
                    normalized_line = ' ' * (normalized_indent_level * indent_size) + line_no_tabs.lstrip()

                normalized_lines.append(normalized_line)
            else:
                normalized_lines.append('')

        return '\n'.join(normalized_lines)

    def _remove_excessive_blank_lines(self, context: str) -> str:
        """Remove excessive blank lines"""
        # Replace multiple consecutive blank lines with maximum 2
        context = re.sub(r'\n\s*\n\s*\n+', '\n\n', context)
        return context

    def _smart_truncate(self, context: str, language: str, max_length: int) -> str:
        """Smart truncation that preserves code structure"""
        if len(context) <= max_length:
            return context

        lines = context.split('\n')
        config = self.language_configs.get(language, self.language_configs['python'])

        # Start from the end and work backwards
        truncated_lines = []
        current_length = 0

        for line in reversed(lines):
            line_length = len(line) + 1  # +1 for newline

            if current_length + line_length > max_length:
                # Check if we can find a good break point
                if self._is_good_break_point(line, config):
                    break
                # If not, continue but we're getting close to limit
                if current_length > max_length * 0.8:
                    break

            truncated_lines.append(line)
            current_length += line_length

        # Reverse back to original order
        truncated_lines.reverse()

        return '\n'.join(truncated_lines)

    def _is_good_break_point(self, line: str, config: Dict) -> bool:
        """Check if a line is a good truncation break point"""
        stripped = line.strip()

        # Empty lines are good break points
        if not stripped:
            return True

        # Function/class definitions are good break points
        keywords = config.get('keywords', [])
        for keyword in ['def', 'class', 'function', 'interface', 'func', 'fn']:
            if keyword in keywords and stripped.startswith(keyword):
                return True

        # Import statements are good break points
        if stripped.startswith(('import', 'from', 'package', 'use')):
            return True

        # Comments are okay break points
        comment_prefix = config.get('comment_prefix', '//')
        if comment_prefix == '<!-- -->' and stripped.startswith('<!--'):
            return True
        elif comment_prefix == '/* */' and stripped.startswith('/*'):
            return True
        elif stripped.startswith(comment_prefix.split()[0]):
            return True

        return False

    def _pad_context(self, context: str, language: str) -> str:
        """Pad context if it's too short"""
        if len(context) >= self.min_context_length:
            return context

        # Add language-specific padding
        config = self.language_configs.get(language, self.language_configs['python'])
        comment_prefix = config.get('comment_prefix', '//')
        
        if comment_prefix == '<!-- -->':
            padding = f"<!-- {language.title()} code context -->\n"
        elif comment_prefix == '/* */':
            padding = f"/* {language.title()} code context */\n"
        else:
            padding = f"{comment_prefix} {language.title()} code context\n"

        return padding + context

    def _language_specific_preprocessing(self, context: str, language: str) -> str:
        """Apply language-specific preprocessing"""
        if language == 'python':
            return self._preprocess_python(context)
        elif language in ['javascript', 'typescript']:
            return self._preprocess_javascript(context)
        elif language == 'java':
            return self._preprocess_java(context)
        elif language == 'go':
            return self._preprocess_go(context)
        elif language == 'rust':
            return self._preprocess_rust(context)
        elif language == 'html':
            return self._preprocess_html(context)
        elif language == 'css':
            return self._preprocess_css(context)
        else:
            return context

    def _preprocess_python(self, context: str) -> str:
        """Python-specific preprocessing"""
        lines = context.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            processed_lines.append(line)

            # Add hint for docstring after function definition
            if line.strip().startswith('def ') and line.strip().endswith(':'):
                # Check if next line is not already a docstring
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                    # Add docstring hint
                    indent = len(line) - len(line.lstrip()) + 4
                    processed_lines.append(' ' * indent + '"""')

        return '\n'.join(processed_lines)

    def _preprocess_javascript(self, context: str) -> str:
        """JavaScript-specific preprocessing"""
        lines = context.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            processed_lines.append(line)

            # Add JSDoc hint for function
            if 'function' in line and '{' in line:
                if i > 0 and not lines[i-1].strip().startswith('/**'):
                    indent = len(line) - len(line.lstrip())
                    processed_lines.insert(-1, ' ' * indent + '/**')
                    processed_lines.insert(-1, ' ' * indent + ' * ')
                    processed_lines.insert(-1, ' ' * indent + ' */')

        return '\n'.join(processed_lines)

    def _preprocess_java(self, context: str) -> str:
        """Java-specific preprocessing"""
        lines = context.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            processed_lines.append(line)

            # Add Javadoc hint for methods
            if any(keyword in line for keyword in ['public', 'private', 'protected']) and '(' in line:
                if i > 0 and not lines[i-1].strip().startswith('/**'):
                    indent = len(line) - len(line.lstrip())
                    processed_lines.insert(-1, ' ' * indent + '/**')
                    processed_lines.insert(-1, ' ' * indent + ' * ')
                    processed_lines.insert(-1, ' ' * indent + ' */')

        return '\n'.join(processed_lines)

    def _preprocess_go(self, context: str) -> str:
        """Go-specific preprocessing"""
        lines = context.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            processed_lines.append(line)

            # Add comment hint for functions
            if line.strip().startswith('func ') and '{' in line:
                if i > 0 and not lines[i-1].strip().startswith('//'):
                    indent = len(line) - len(line.lstrip())
                    processed_lines.insert(-1, ' ' * indent + '// ')

        return '\n'.join(processed_lines)

    def _preprocess_rust(self, context: str) -> str:
        """Rust-specific preprocessing"""
        lines = context.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            processed_lines.append(line)

            # Add comment hint for functions
            if line.strip().startswith('fn ') and '{' in line:
                if i > 0 and not lines[i-1].strip().startswith('//'):
                    indent = len(line) - len(line.lstrip())
                    processed_lines.insert(-1, ' ' * indent + '// ')

        return '\n'.join(processed_lines)

    def _preprocess_html(self, context: str) -> str:
        """HTML-specific preprocessing"""
        # Add basic HTML structure hints if missing
        if not re.search(r'<html|<HTML', context):
            return context
        return context

    def _preprocess_css(self, context: str) -> str:
        """CSS-specific preprocessing"""
        # Basic CSS formatting
        return context

    def extract_context_metadata(self, context: str, language: str) -> Dict[str, Any]:
        """Extract metadata from context for better completion"""
        metadata = {
            'language': language,
            'line_count': len(context.split('\n')),
            'char_count': len(context),
            'has_functions': False,
            'has_classes': False,
            'has_imports': False,
            'indentation_level': 0,
            'last_line_type': 'unknown',
            'context_window': self._get_context_window(language)
        }

        lines = context.split('\n')
        config = self.language_configs.get(language, self.language_configs['python'])

        # Analyze content
        for line in lines:
            stripped = line.strip()

            # Check for functions (language-specific)
            function_keywords = ['def ', 'function ', 'func ', 'fn ']
            if any(keyword in stripped for keyword in function_keywords):
                metadata['has_functions'] = True

            # Check for classes (language-specific)
            class_keywords = ['class ', 'interface ', 'struct ', 'enum ']
            if any(keyword in stripped for keyword in class_keywords):
                metadata['has_classes'] = True

            # Check for imports (language-specific)
            import_keywords = ['import', 'from', 'package', 'use', '#include']
            if any(stripped.startswith(keyword) for keyword in import_keywords):
                metadata['has_imports'] = True

        # Get indentation level of last non-empty line
        for line in reversed(lines):
            if line.strip():
                metadata['indentation_level'] = len(line) - len(line.lstrip())
                metadata['last_line_type'] = self._classify_line_type(line, config)
                break

        return metadata

    def _classify_line_type(self, line: str, config: Dict) -> str:
        """Classify the type of a code line"""
        stripped = line.strip()

        if not stripped:
            return 'empty'

        comment_prefix = config.get('comment_prefix', '//')
        if comment_prefix == '<!-- -->' and stripped.startswith('<!--'):
            return 'comment'
        elif comment_prefix == '/* */' and stripped.startswith('/*'):
            return 'comment'
        elif stripped.startswith(comment_prefix.split()[0]):
            return 'comment'

        keywords = config.get('keywords', [])
        if any(stripped.startswith(keyword) for keyword in keywords):
            return 'keyword'

        if stripped.endswith(':'):
            return 'block_start'

        if stripped.endswith((',', '\\', '+')):
            return 'continuation'

        operators = config.get('operators', [])
        if any(op in stripped for op in operators):
            return 'assignment'

        return 'statement'

    def detect_language_from_context(self, context: str, file_path: Optional[str] = None) -> str:
        """Detect programming language from context and file path"""
        if file_path:
            # Try to detect from file extension first
            import os
            file_ext = os.path.splitext(file_path)[1].lower()
            
            for lang, config in self.language_configs.items():
                if file_ext in config.get('file_extensions', []):
                    return lang
        
        # Fallback to context-based detection
        context_lower = context.lower()
        
        # Simple heuristics based on common patterns
        if 'def ' in context or 'import ' in context or 'from ' in context:
            return 'python'
        elif 'function' in context or 'var ' in context or 'let ' in context or 'const ' in context:
            if 'interface' in context or 'type ' in context:
                return 'typescript'
            return 'javascript'
        elif 'public class' in context or 'private ' in context or 'protected ' in context:
            return 'java'
        elif 'func ' in context or 'package ' in context:
            return 'go'
        elif 'fn ' in context or 'struct ' in context or 'impl ' in context:
            return 'rust'
        elif '#include' in context or 'int main' in context:
            return 'c'
        elif 'namespace' in context or 'std::' in context:
            return 'cpp'
        elif '<?php' in context or '$' in context:
            return 'php'
        elif 'def ' in context and 'end' in context:
            return 'ruby'
        elif '<html' in context or '<div' in context:
            return 'html'
        elif '{' in context and '}' in context and ':' in context and not 'function' in context:
            return 'css'
        elif 'select' in context_lower or 'from' in context_lower or 'where' in context_lower:
            return 'sql'
        
        return 'python'  # Default fallback