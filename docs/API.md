# API Documentation - Python Code Autocompletion

This document provides detailed information about the REST API endpoints, request/response formats, and usage examples for the Python Code Autocompletion backend.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing API key authentication or OAuth.

## API Endpoints

### 1. Code Completion

**POST** `/api/v1/completion`

Generate code completions based on the provided context.

#### Request Body

```json
{
  "code": "def calculate_fibonacci(n):",
  "cursor_position": 26,
  "language": "python",
  "max_completions": 3,
  "context": {
    "file_path": "/path/to/file.py",
    "project_context": "mathematical functions",
    "imports": ["import math", "import numpy as np"]
  },
  "options": {
    "temperature": 0.7,
    "max_tokens": 100,
    "top_p": 0.9
  }
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | The code context before the cursor |
| `cursor_position` | integer | Yes | Position of the cursor in the code |
| `language` | string | Yes | Programming language (python, javascript, java, etc.) |
| `max_completions` | integer | No | Maximum number of completions to return (default: 3) |
| `context` | object | No | Additional context information |
| `options` | object | No | Generation parameters override |

#### Response

```json
{
  "completions": [
    {
      "text": "\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
      "confidence": 0.95,
      "language": "python",
      "completion_type": "function_body"
    },
    {
      "text": "\n    # Base cases\n    if n <= 1:\n        return n\n    # Recursive case\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
      "confidence": 0.89,
      "language": "python",
      "completion_type": "function_body"
    }
  ],
  "metadata": {
    "model_used": "microsoft/CodeGPT-small-py",
    "processing_time": 0.234,
    "language_detected": "python",
    "context_length": 26
  }
}
```

#### Error Response

```json
{
  "error": {
    "code": "INVALID_LANGUAGE",
    "message": "Unsupported programming language: xyz",
    "details": {
      "supported_languages": ["python", "javascript", "java", "cpp", "go"]
    }
  }
}
```

### 2. Code Analysis

**POST** `/api/v1/analysis`

Analyze code for potential issues, improvements, or documentation.

#### Request Body

```json
{
  "code": "def divide(a, b):\n    return a / b",
  "language": "python",
  "analysis_type": "bug_detection",
  "options": {
    "check_style": true,
    "check_performance": true,
    "check_security": true
  }
}
```

#### Response

```json
{
  "analysis": {
    "issues": [
      {
        "type": "bug",
        "severity": "high",
        "line": 2,
        "column": 11,
        "message": "Potential division by zero error",
        "suggestion": "Add check for zero divisor"
      }
    ],
    "suggestions": [
      {
        "type": "improvement",
        "line": 1,
        "message": "Add type hints and docstring",
        "example": "def divide(a: float, b: float) -> float:\n    \"\"\"Divide a by b.\"\"\"\n    if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b"
      }
    ]
  },
  "metadata": {
    "model_used": "microsoft/codebert-base",
    "processing_time": 0.156,
    "language": "python"
  }
}
```

### 3. Code Documentation

**POST** `/api/v1/documentation`

Generate documentation for code snippets or functions.

#### Request Body

```json
{
  "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
  "language": "python",
  "doc_style": "google",
  "include_examples": true
}
```

#### Response

```json
{
  "documentation": {
    "docstring": "\"\"\"Performs binary search on a sorted array.\n\n    Args:\n        arr (List[int]): A sorted list of integers.\n        target (int): The value to search for.\n\n    Returns:\n        int: The index of the target if found, -1 otherwise.\n\n    Examples:\n        >>> binary_search([1, 3, 5, 7, 9], 5)\n        2\n        >>> binary_search([1, 3, 5, 7, 9], 6)\n        -1\n    \"\"\"",
    "type_hints": "def binary_search(arr: List[int], target: int) -> int:",
    "imports_needed": ["from typing import List"]
  },
  "metadata": {
    "model_used": "microsoft/codebert-base",
    "processing_time": 0.198,
    "language": "python"
  }
}
```

### 4. Health Check

**GET** `/api/v1/health`

Check the health status of the API and loaded models.

#### Response

```json
{
  "status": "healthy",
  "models": {
    "codegpt": {
      "loaded": true,
      "model_name": "microsoft/CodeGPT-small-py",
      "memory_usage": "1.2GB"
    },
    "codebert": {
      "loaded": true,
      "model_name": "microsoft/codebert-base",
      "memory_usage": "0.8GB"
    }
  },
  "system": {
    "cpu_usage": "15%",
    "memory_usage": "2.1GB",
    "uptime": "2h 45m"
  }
}
```

### 5. Model Configuration

**GET** `/api/v1/config`

Get current model configuration.

#### Response

```json
{
  "models": {
    "codegpt": {
      "model_name": "microsoft/CodeGPT-small-py",
      "max_length": 1024,
      "supported_languages": ["python", "javascript", "java", "cpp", "go"],
      "generation_config": {
        "max_new_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50
      }
    },
    "codebert": {
      "model_name": "microsoft/codebert-base",
      "max_length": 512,
      "supported_languages": ["python", "java", "javascript", "php", "ruby"],
      "task_configs": {
        "code_completion": {
          "max_new_tokens": 100,
          "temperature": 0.8
        },
        "bug_detection": {
          "temperature": 0.2
        }
      }
    }
  }
}
```

**PUT** `/api/v1/config`

Update model configuration.

#### Request Body

```json
{
  "model": "codegpt",
  "config": {
    "temperature": 0.8,
    "max_new_tokens": 120,
    "top_p": 0.95
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_LANGUAGE` | Unsupported programming language |
| `INVALID_REQUEST` | Malformed request body |
| `MODEL_NOT_LOADED` | Requested model is not loaded |
| `GENERATION_FAILED` | Model failed to generate completion |
| `RATE_LIMIT_EXCEEDED` | Too many requests in short time |
| `INTERNAL_ERROR` | Internal server error |

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Development**: 100 requests per minute per IP
- **Production**: 500 requests per minute per API key

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640995200
```

## Language Support

### Supported Languages

| Language | CodeGPT | CodeBERT | File Extensions |
|----------|---------|----------|-----------------|
| Python | ✅ | ✅ | .py, .pyx, .pyi |
| JavaScript | ✅ | ✅ | .js, .jsx, .mjs |
| TypeScript | ✅ | ❌ | .ts, .tsx |
| Java | ✅ | ✅ | .java |
| C++ | ✅ | ✅ | .cpp, .cc, .cxx, .c++ |
| C | ✅ | ✅ | .c, .h |
| C# | ✅ | ✅ | .cs |
| Go | ✅ | ✅ | .go |
| Rust | ✅ | ❌ | .rs |
| PHP | ✅ | ✅ | .php, .phtml |
| Ruby | ✅ | ✅ | .rb, .rbw |

## Usage Examples

### Python Client

```python
import requests
import json

# Code completion example
def get_completion(code, language="python"):
    url = "http://localhost:8000/api/v1/completion"
    payload = {
        "code": code,
        "cursor_position": len(code),
        "language": language,
        "max_completions": 3
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()["completions"]
    else:
        print(f"Error: {response.json()}")
        return None

# Usage
code = "def factorial(n):"
completions = get_completion(code)
for i, completion in enumerate(completions):
    print(f"Completion {i+1}: {completion['text']}")
```

### JavaScript Client

```javascript
// Code completion function
async function getCompletion(code, language = 'javascript') {
    const response = await fetch('http://localhost:8000/api/v1/completion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            code: code,
            cursor_position: code.length,
            language: language,
            max_completions: 3
        })
    });
    
    if (response.ok) {
        const data = await response.json();
        return data.completions;
    } else {
        const error = await response.json();
        console.error('Error:', error);
        return null;
    }
}

// Usage
const code = "function fibonacci(n) {";
getCompletion(code).then(completions => {
    completions.forEach((completion, index) => {
        console.log(`Completion ${index + 1}: ${completion.text}`);
    });
});
```

### cURL Examples

```bash
# Code completion
curl -X POST http://localhost:8000/api/v1/completion \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def quicksort(arr):",
    "cursor_position": 19,
    "language": "python",
    "max_completions": 2
  }'

# Code analysis
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def divide(a, b):\n    return a / b",
    "language": "python",
    "analysis_type": "bug_detection"
  }'

# Health check
curl -X GET http://localhost:8000/api/v1/health
```

## WebSocket Support (Optional)

For real-time completions, the API supports WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/completion');

ws.onopen = function(event) {
    console.log('Connected to WebSocket');
};

ws.onmessage = function(event) {
    const completion = JSON.parse(event.data);
    console.log('Received completion:', completion);
};

// Send completion request
ws.send(JSON.stringify({
    code: "def hello_world():",
    cursor_position: 18,
    language: "python"
}));
```

## Performance Considerations

1. **Batch Requests**: For multiple completions, use batch endpoints when available
2. **Caching**: Identical requests are cached for 1 hour by default
3. **Context Size**: Larger context improves accuracy but increases processing time
4. **Model Selection**: Choose appropriate model based on task requirements

## Development Tips

1. **Error Handling**: Always implement proper error handling for API calls
2. **Timeouts**: Set appropriate timeout values for requests (recommended: 5-10 seconds)
3. **Retry Logic**: Implement exponential backoff for failed requests
4. **Logging**: Log API interactions for debugging and monitoring