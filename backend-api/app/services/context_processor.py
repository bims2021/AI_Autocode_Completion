import hashlib
import re
from typing import Dict, Any, List, Optional, NamedTuple
import logging

from ..models.request_models import CompletionRequest, ProcessedContext
from ai_model.model_configs.codebert_config import CodeBERTConfig
from ai_model.model_configs.codegpt_config import CodeGPTConfig

logger = logging.getLogger(__name__)

class LanguageParser:
    """Base class for language-specific parsers"""
    
    def extract_function_signature(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract current function signature"""
        raise NotImplementedError
    
    def extract_class_info(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract class information"""
        raise NotImplementedError
    
    def extract_imports(self, lines: List[str]) -> List[str]:
        """Extract import statements"""
        raise NotImplementedError
    
    def extract_variables(self, lines: List[str]) -> List[Dict[str, str]]:
        """Extract variable declarations"""
        raise NotImplementedError

class PythonParser(LanguageParser):
    def extract_function_signature(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract Python function signature"""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('def '):
                match = re.match(r'def\s+(\w+)\s*\((.*?)\)\s*(?:->\s*(.+?))?\s*:', line)
                if match:
                    func_name, params, return_type = match.groups()
                    return {
                        'name': func_name,
                        'parameters': [p.strip() for p in params.split(',') if p.strip()],
                        'return_type': return_type.strip() if return_type else None
                    }
        return None
    
    def extract_class_info(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract Python class information"""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                match = re.match(r'class\s+(\w+)(?:\((.*?)\))?\s*:', line)
                if match:
                    class_name, inheritance = match.groups()
                    return {
                        'name': class_name,
                        'inheritance': inheritance.strip() if inheritance else None
                    }
        return None
    
    def extract_imports(self, lines: List[str]) -> List[str]:
        """Extract Python imports"""
        imports = []
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        return imports
    
    def extract_variables(self, lines: List[str]) -> List[Dict[str, str]]:
        """Extract Python variable declarations"""
        variables = []
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    var_name, value = match.groups()
                    variables.append({
                        'name': var_name,
                        'value': value.strip(),
                        'scope': 'local'
                    })
        return variables

class JavaScriptParser(LanguageParser):
    def extract_function_signature(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract JavaScript function signature"""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            # Function declaration
            if line.startswith('function '):
                match = re.match(r'function\s+(\w+)\s*\((.*?)\)', line)
                if match:
                    func_name, params = match.groups()
                    return {
                        'name': func_name,
                        'parameters': [p.strip() for p in params.split(',') if p.strip()],
                        'return_type': None
                    }
            # Arrow function
            elif '=>' in line:
                match = re.match(r'(?:const|let|var)\s+(\w+)\s*=\s*\((.*?)\)\s*=>', line)
                if match:
                    func_name, params = match.groups()
                    return {
                        'name': func_name,
                        'parameters': [p.strip() for p in params.split(',') if p.strip()],
                        'return_type': None
                    }
        return None
    
    def extract_imports(self, lines: List[str]) -> List[str]:
        """Extract JavaScript imports"""
        imports = []
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('const ') and 'require(' in line:
                imports.append(line)
        return imports
    
    def extract_variables(self, lines: List[str]) -> List[Dict[str, str]]:
        """Extract JavaScript variable declarations"""
        variables = []
        for line in lines:
            line = line.strip()
            if any(line.startswith(keyword) for keyword in ['const ', 'let ', 'var ']):
                match = re.match(r'(const|let|var)\s+(\w+)\s*=\s*(.+)', line)
                if match:
                    keyword, var_name, value = match.groups()
                    variables.append({
                        'name': var_name,
                        'value': value.strip(),
                        'scope': 'local'
                    })
        return variables

class ContextProcessor:
    def __init__(self, codegpt_config: CodeGPTConfig = None, codebert_config: CodeBERTConfig = None):
        self.codegpt_config = codegpt_config or CodeGPTConfig()
        self.codebert_config = codebert_config or CodeBERTConfig()
        
        self.parsers = {
            'python': PythonParser(),
            'javascript': JavaScriptParser(),
            'typescript': JavaScriptParser(),  # Use JS parser for TS
            'java': PythonParser(),  # Simplified for now
        }
        
        # Default max context lines
        self.default_max_context_lines = 50
    
    def detect_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect language from file path using CodeGPT config"""
        return self.codegpt_config.detect_language_from_file(file_path)
    
    def get_context_window_size(self, language: str) -> int:
        """Get context window size for language"""
        return self.codegpt_config.get_context_window(language)
    
    def get_max_context_lines(self, language: str) -> int:
        """Get maximum context lines based on language configuration"""
        context_window = self.get_context_window_size(language)
        # Estimate lines based on context window (rough approximation)
        estimated_lines = min(context_window // 20, self.default_max_context_lines)
        return max(estimated_lines, 10)  # At least 10 lines
    
    async def process_context(self, request: CompletionRequest) -> ProcessedContext:
        """Process and analyze code context"""
        context = request.context
        language = context.get('language', 'python')
        
        # Auto-detect language if file path is provided
        if 'filePath' in context and not language:
            detected_lang = self.detect_language_from_file(context['filePath'])
            if detected_lang:
                language = detected_lang
        
        # Validate context
        self._validate_context(context)
        
        # Get appropriate parser
        parser = self.parsers.get(language, self.parsers['python'])
        
        # Build code snippet
        previous_lines = context.get('previousLines', [])
        current_line = context.get('currentLine', '')
        
        # Get language-specific context limits
        max_context_lines = self.get_max_context_lines(language)
        
        # Limit context size based on language configuration
        if len(previous_lines) > max_context_lines:
            previous_lines = previous_lines[-max_context_lines:]
        
        all_lines = previous_lines + [current_line] if current_line else previous_lines
        code_snippet = '\n'.join(all_lines)
        
        # Extract language-specific context
        function_signature = parser.extract_function_signature(previous_lines)
        class_info = parser.extract_class_info(previous_lines)
        imports = parser.extract_imports(previous_lines)
        variables = parser.extract_variables(previous_lines)
        
        # Get language-specific configuration
        lang_config = self.codegpt_config.get_language_config(language)
        
        # Generate context hash
        context_hash = hashlib.md5(
            (code_snippet + language + str(function_signature)).encode()
        ).hexdigest()
        
        return ProcessedContext(
            code_snippet=code_snippet,
            function_signature=function_signature,
            class_info=class_info,
            imports=imports,
            variables=variables,
            context_hash=context_hash,
            language=language,
            language_config=lang_config,
            context_window_size=self.get_context_window_size(language)
        )
    
    def _validate_context(self, context: Dict[str, Any]):
        """Validate context structure"""
        required_fields = ['position']
        
        for field in required_fields:
            if field not in context:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate position
        position = context['position']
        if not isinstance(position, dict) or 'line' not in position:
            raise ValueError("Invalid position structure")
        
        # Validate language if provided
        if 'language' in context:
            language = context['language']
            if not self.codegpt_config.is_language_supported(language):
                logger.warning(f"Language '{language}' may not be fully supported")
    
    def get_language_specific_settings(self, language: str) -> Dict[str, Any]:
        """Get language-specific settings for context processing"""
        lang_config = self.codegpt_config.get_language_config(language)
        return {
            'context_window': self.get_context_window_size(language),
            'max_context_lines': self.get_max_context_lines(language),
            'comment_style': lang_config.get('comment_style', '#'),
            'indent_style': lang_config.get('indent_style', 'spaces'),
            'indent_size': lang_config.get('indent_size', 4),
            'file_extensions': lang_config.get('file_extensions', [])
        }
    
    def estimate_token_count(self, text: str, language: str) -> int:
        """Estimate token count for given text and language"""
        # Simple estimation: assume average 4 characters per token
        # This is a rough approximation and could be improved with actual tokenization
        return len(text) // 4
    
    def trim_context_to_fit(self, context: str, language: str) -> str:
        """Trim context to fit within language-specific limits"""
        max_tokens = self.get_context_window_size(language)
        estimated_tokens = self.estimate_token_count(context, language)
        
        if estimated_tokens <= max_tokens:
            return context
        
        # Trim from the beginning to keep the most recent context
        lines = context.split('\n')
        while lines and self.estimate_token_count('\n'.join(lines), language) > max_tokens:
            lines.pop(0)
        
        return '\n'.join(lines)