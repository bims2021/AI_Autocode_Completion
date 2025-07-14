# Python Code Autocompletion System

A comprehensive AI-powered code autocompletion system featuring a VS Code extension, Python backend API, and machine learning models for intelligent code suggestions.

##  Features

- **VS Code Extension**: Seamless integration with VS Code for real-time code completion
- **Multiple AI Models**: Support for CodeGPT, CodeBERT, and custom models
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++, Go, and more
- **Context-aware Suggestions**: Intelligent code completion based on surrounding context
- **Caching System**: Redis-based caching for improved performance
- **Rate Limiting**: Built-in rate limiting and request throttling
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Docker Support**: Full containerization for easy deployment
- **Extensible Architecture**: Modular design for easy customization

##  Project Structure

```
python-code-autocompletion/
├── vscode-extension/          # VS Code Plugin
│   ├── src/
│   │   ├── extension.ts       # Main extension entry point
│   │   ├── completionProvider.ts
│   │   ├── apiClient.ts
│   │   └── config.ts
│   ├── package.json
│   └── tsconfig.json
├── backend-api/               # Python Backend
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # Data models
│   │   └── utils/            # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── ai-model/                  # AI Model Components
│   ├── model_loader.py
│   ├── inference_engine.py
│   ├── preprocessing.py
│   ├── postprocessing.py
│   └── model_configs/
├── data-processing/           # Dataset and Training
│   ├── dataset_loader.py
│   ├── data_cleaner.py
│   ├── tokenizer.py
│   └── fine_tuning.py(optional)
├── tests/                     # Test Suite
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── docker-compose.yml
├── requirements.txt
└── README.md
```

##  Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- Docker and Docker Compose (optional)
- VS Code (for extension development)

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bims2021/AI_Autocode_Completion.git
   cd python-code-autocompletion
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Install the VS Code extension:**
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   # Install in VS Code: Ctrl+Shift+P -> "Install from VSIX"
   ```

### Manual Installation

1. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install AI models:**
   ```bash
   python scripts/download_models.py
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

4. **Run the backend API:**
   ```bash
   cd backend-api
   python -m uvicorn app.main:app --reload --port 8000
   ```

5. **Set up VS Code extension:**
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   # Press F5 to launch extension development host
   ```

## 🔧 Configuration

### Backend API Configuration

Environment variables (`.env`):

```env
# Model Configuration
MODEL_CACHE_DIR=/root/.cache/ai-model
DEFAULT_MODEL=microsoft/CodeGPT-small-py
MAX_CONCURRENT_REQUESTS=100

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_PERIOD=60

# CORS
ENABLE_CORS=true
CORS_ORIGINS=*
```

### Model Configuration

The system supports multiple AI models with language-specific configurations:

```python
# CodeGPT Configuration
codegpt_config = {
    'model_name': 'microsoft/CodeGPT-small-py',
    'max_new_tokens': 150,
    'temperature': 0.7,
    'top_p': 0.9,
    'supported_languages': ['python', 'javascript', 'java', ...]
}

# CodeBERT Configuration
codebert_config = {
    'model_name': 'microsoft/codebert-base',
    'max_length': 512,
    'task_configs': {
        'code_completion': {...},
        'code_search': {...},
        'bug_detection': {...}
    }
}
```

## 🚀 Usage

### VS Code Extension

1. **Install the extension** in VS Code
2. **Open a Python file** (or supported language)
3. **Start typing** - autocompletion suggestions will appear automatically
4. **Configure settings** via VS Code settings:
   - `codeAutocompletion.apiEndpoint`
   - `codeAutocompletion.maxSuggestions`
   - `codeAutocompletion.debounceTime`

### API Usage

Direct API calls for code completion:

```python
import requests

# Code completion request
response = requests.post('http://localhost:8000/api/v1/complete', json={
    'code': 'def fibonacci(n):\n    if n <= 1:\n        return',
    'language': 'python',
    'cursor_position': 45,
    'max_suggestions': 3
})

suggestions = response.json()['suggestions']
```

### API Endpoints

- `POST /api/v1/complete` - Get code completion suggestions
- `POST /api/v1/analyze` - Analyze code quality and bugs
- `GET /api/v1/models` - List available models
- `GET /api/v1/health` - Health check
- `GET /metrics` - Prometheus metrics

## 🧪 Testing

### Run all tests:
```bash
python -m pytest tests/ -v --cov=.
```

### Run specific test suites:
```bash
# API tests
python -m pytest tests/test_api/ -v

# Model tests
python -m pytest tests/test_model/ -v

# Extension tests
cd vscode-extension && npm test
```

### Load testing:
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Monitoring

### Prometheus Metrics

Available at `http://localhost:9090`:

- `api_requests_total` - Total API requests
- `api_request_duration_seconds` - Request duration
- `model_inference_duration_seconds` - Model inference time
- `cache_hits_total` - Cache hit rate
- `active_connections` - Active WebSocket connections

### Grafana Dashboards

Available at `http://localhost:3000` (admin/admin):

- **API Performance Dashboard**
- **Model Performance Dashboard**
- **System Resources Dashboard**
- **Error Rate Dashboard**

##  Development

### Adding New Models

1. **Create model configuration:**
   ```python
   # ai-model/model_configs/your_model_config.py
   class YourModelConfig:
       def __init__(self):
           self.model_name = "your-model-name"
           # ... configuration
   ```

2. **Implement model loader:**
   ```python
   # ai-model/model_loader.py
   def load_your_model(config):
       # Model loading logic
       return model, tokenizer
   ```

3. **Register in inference engine:**
   ```python
   # ai-model/inference_engine.py
   self.model_loaders['your_model'] = load_your_model
   ```

### Adding New Languages

1. **Update model configurations:**
   ```python
   # Add to supported_languages and language_configs
   self.language_configs['your_language'] = {
       'max_new_tokens': 150,
       'temperature': 0.7,
       'file_extensions': ['.ext'],
       'comment_style': '//',
       'indent_style': 'spaces'
   }
   ```

2. **Add language detection:**
   ```python
   # Update detect_language_from_file() method
   ```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

1. **Model loading errors:**
   - Check CUDA availability for GPU models
   - Verify model cache directory permissions
   - Ensure sufficient disk space

2. **API connection errors:**
   - Verify backend is running on correct port
   - Check firewall settings
   - Validate API endpoint in VS Code settings

3. **Performance issues:**
   - Enable Redis caching
   - Adjust model parameters (temperature, max_tokens)
   - Monitor system resources

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

## 📈 Performance Optimization

### Model Optimization

- **Quantization**: Use quantized models for faster inference
- **Batching**: Process multiple requests together
- **Caching**: Cache frequent code patterns
- **GPU Acceleration**: Use CUDA for supported models

### API Optimization

- **Connection Pooling**: Reuse HTTP connections
- **Async Processing**: Use async/await for I/O operations
- **Load Balancing**: Distribute requests across multiple workers
- **Rate Limiting**: Prevent API abuse

##  Security

- **API Key Authentication**: Secure API access
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Sanitize all inputs
- **HTTPS**: Use TLS for production
- **CORS**: Configure appropriate origins

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

##  Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/bims2021/AI_Autocode_Completion/issues)


##  Acknowledgments

- Microsoft for CodeGPT and CodeBERT models
- Hugging Face for the Transformers library
- OpenAI for inspiration from GitHub Copilot
- The open-source community for various tools and libraries

---