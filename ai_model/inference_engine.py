
import torch
import torch.nn.functional as F
from transformers import StoppingCriteria, StoppingCriteriaList
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import re

from .model_loader import ModelLoader
from .preprocessing import CodePreprocessor
from .postprocessing import CodePostprocessor

logger = logging.getLogger(__name__)

class CustomStoppingCriteria(StoppingCriteria):
    """Custom stopping criteria for code generation"""
    
    def __init__(self, stop_tokens: List[str], tokenizer):
        self.stop_tokens = stop_tokens
        self.tokenizer = tokenizer
        self.stop_token_ids = [tokenizer.encode(token, add_special_tokens=False) for token in stop_tokens]
    
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Check if any stop token sequence is at the end
        for stop_ids in self.stop_token_ids:
            if len(stop_ids) > 0 and input_ids[0][-len(stop_ids):].tolist() == stop_ids:
                return True
        return False


class InferenceEngine:
    """
    High-performance inference engine for code completion
    """
    
    def __init__(self, model_name: str = 'gpt2', model_path: Optional[str] = None):
        self.model_loader = ModelLoader()
        self.preprocessor = CodePreprocessor()
        self.postprocessor = CodePostprocessor()
        
        # Load model
        self.model_name = model_name
        self.model, self.tokenizer = self.model_loader.load_model(model_name, model_path)
        
        # Generation parameters
        self.default_params = {
            'max_new_tokens': 100,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'do_sample': True,
            'num_return_sequences': 1,
            'repetition_penalty': 1.1,
            'length_penalty': 1.0,
            'early_stopping': True
        }
        
        # Performance tracking
        self.inference_stats = {
            'total_requests': 0,
            'total_time': 0,
            'avg_time': 0,
            'cache_hits': 0
        }
        
        # Simple cache for repeated requests
        self.cache = {}
        self.cache_max_size = 1000
        
        logger.info(f"Inference engine initialized with model: {model_name}")
    
    def generate_completion(
        self,
        context: str,
        language: str = 'python',
        max_suggestions: int = 3,
        **generation_params
    ) -> List[Dict[str, Any]]:
        """
        Generate code completions for given context
        
        Args:
            context: Code context to complete
            language: Programming language
            max_suggestions: Number of suggestions to generate
            **generation_params: Additional generation parameters
            
        Returns:
            List of completion suggestions
        """
        start_time = time.time()
        
        try:
            # Create cache key
            cache_key = self._create_cache_key(context, language, max_suggestions, generation_params)
            
            # Check cache
            if cache_key in self.cache:
                self.inference_stats['cache_hits'] += 1
                logger.debug("Cache hit for completion request")
                return self.cache[cache_key]
            
            # Preprocess context
            processed_context = self.preprocessor.preprocess_context(context, language)
            
            # Prepare generation parameters
            params = {**self.default_params, **generation_params}
            params['num_return_sequences'] = max_suggestions
            
            # Generate completions
            completions = self._generate_with_model(processed_context, params)
            
            # Postprocess results
            results = []
            for i, completion in enumerate(completions):
                processed_completion = self.postprocessor.postprocess_completion(
                    completion, context, language
                )
                
                suggestion = {
                    'text': processed_completion['text'],
                    'confidence': processed_completion['confidence'],
                    'type': processed_completion['type'],
                    'description': f"AI-generated suggestion {i + 1}",
                    'cursorOffset': len(processed_completion['text']),
                    'metadata': {
                        'language': language,
                        'model': self.model_name,
                        'generation_time': processed_completion.get('generation_time', 0)
                    }
                }
                results.append(suggestion)
            
            # Cache results
            if len(self.cache) < self.cache_max_size:
                self.cache[cache_key] = results
            
            # Update stats
            inference_time = time.time() - start_time
            self.inference_stats['total_requests'] += 1
            self.inference_stats['total_time'] += inference_time
            self.inference_stats['avg_time'] = (
                self.inference_stats['total_time'] / self.inference_stats['total_requests']
            )
            
            logger.info(f"Generated {len(results)} completions in {inference_time:.3f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return self._get_fallback_completions(context, language, max_suggestions)
    
    def _generate_with_model(self, context: str, params: Dict[str, Any]) -> List[str]:
        """Generate completions using the loaded model"""
        # Tokenize input
        inputs = self.tokenizer(
            context,
            return_tensors='pt',
            max_length=self.tokenizer.model_max_length - params['max_new_tokens'],
            truncation=True,
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Setup stopping criteria
        stop_tokens = ['\n\n', '```', 'def ', 'class ', 'import ', 'from ']
        stopping_criteria = StoppingCriteriaList([
            CustomStoppingCriteria(stop_tokens, self.tokenizer)
        ])
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=params['max_new_tokens'],
                temperature=params['temperature'],
                top_p=params['top_p'],
                top_k=params['top_k'],
                do_sample=params['do_sample'],
                num_return_sequences=params['num_return_sequences'],
                repetition_penalty=params['repetition_penalty'],
                length_penalty=params['length_penalty'],
                early_stopping=params['early_stopping'],
                stopping_criteria=stopping_criteria,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True
            )
        
        # Decode outputs
        completions = []
        input_length = inputs['input_ids'].shape[1]
        
        for output in outputs:
            # Extract only new tokens
            new_tokens = output[input_length:]
            completion = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
            
            # Clean up completion
            completion = completion.strip()
            if completion:
                completions.append(completion)
        
        return completions
    
    def _create_cache_key(self, context: str, language: str, max_suggestions: int, params: Dict) -> str:
        """Create cache key for request"""
        import hashlib
        
        # Create hash of context and parameters
        cache_data = f"{context}_{language}_{max_suggestions}_{sorted(params.items())}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_fallback_completions(self, context: str, language: str, max_suggestions: int) -> List[Dict[str, Any]]:
        """Generate fallback completions when model fails"""
        fallbacks = []
        
        if language == 'python':
            fallback_suggestions = ['pass', 'return None', '# TODO: implement']
        elif language in ['javascript', 'typescript']:
            fallback_suggestions = ['return;', '// TODO: implement', 'throw new Error("Not implemented");']
        elif language == 'java':
            fallback_suggestions = ['return null;', '// TODO: implement', 'throw new UnsupportedOperationException();']
        else:
            fallback_suggestions = ['// TODO: implement', 'return;', 'pass']
        
        for i, suggestion in enumerate(fallback_suggestions[:max_suggestions]):
            fallbacks.append({
                'text': suggestion,
                'confidence': 0.3,
                'type': 'single-line',
                'description': f"Fallback suggestion {i + 1}",
                'cursorOffset': len(suggestion),
                'metadata': {
                    'language': language,
                    'model': 'fallback',
                    'generation_time': 0
                }
            })
        
        return fallbacks
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get model and inference statistics"""
        model_info = self.model_loader.get_model_info(self.model_name)
        memory_usage = self.model_loader.get_memory_usage()
        
        return {
            'model_info': model_info,
            'memory_usage': memory_usage,
            'inference_stats': self.inference_stats,
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """Clear the completion cache"""
        self.cache.clear()
        logger.info("Inference cache cleared")
    
    def warm_up(self, sample_contexts: List[str]):
        """Warm up the model with sample contexts"""
        logger.info("Warming up model...")
        
        for context in sample_contexts:
            try:
                self.generate_completion(context, max_suggestions=1)
            except Exception as e:
                logger.warning(f"Warm-up failed for context: {e}")
        
        logger.info("Model warm-up completed")