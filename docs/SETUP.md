# Setup Guide - Python Code Autocompletion

This guide will help you set up the Python Code Autocompletion system with VS Code extension, backend API, and AI models.

## Prerequisites

- Python 3.8+ installed
- Node.js 16+ and npm
- VS Code (for extension development)
- Docker (optional, for containerized deployment)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd python-code-autocompletion
```

### 2. Environment Setup

Run the setup script to configure your environment:

```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

Or manually follow these steps:

#### Backend Setup

```bash
# Navigate to backend directory
cd backend-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### VS Code Extension Setup

```bash
# Navigate to extension directory
cd vscode-extension

# Install dependencies
npm install

# Build extension
npm run build
```

### 3. Download AI Models

```bash
# Run the model download script
python scripts/download_models.py
```

This will download and cache the following models:
- Microsoft CodeGPT-small-py
- Microsoft CodeBERT-base

Models will be stored in `~/.cache/ai-model/` directory.

## Detailed Setup Instructions

### Backend API Setup

1. **Virtual Environment**
   ```bash
   cd backend-api
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` file in the `backend-api` directory:
   ```env
   MODEL_CACHE_PATH=~/.cache/ai-model
   LOG_LEVEL=INFO
   API_HOST=localhost
   API_PORT=8000
   CACHE_TTL=3600
   MAX_COMPLETION_LENGTH=150
   ```

4. **Start the Backend**
   ```bash
   python -m app.main
   ```

   The API will be available at `http://localhost:8000`

### AI Model Configuration

The system supports two main models with different configurations:

#### CodeGPT Configuration
- **Model**: microsoft/CodeGPT-small-py
- **Context Window**: 1024-2048 tokens (language-specific)
- **Use Cases**: Code completion, generation
- **Supported Languages**: Python, JavaScript, Java, C++, Go, Rust, and more

#### CodeBERT Configuration
- **Model**: microsoft/codebert-base
- **Context Window**: 512 tokens
- **Use Cases**: Code analysis, bug detection, documentation
- **Supported Languages**: Python, Java, JavaScript, PHP, Ruby, Go, C, C++, C#

### VS Code Extension Setup

1. **Install Dependencies**
   ```bash
   cd vscode-extension
   npm install
   ```

2. **Development Mode**
   ```bash
   # Build in watch mode
   npm run watch
   
   # In VS Code, press F5 to launch Extension Development Host
   ```

3. **Package Extension**
   ```bash
   npm install -g vsce
   vsce package
   ```

4. **Install Extension**
   ```bash
   code --install-extension python-code-autocompletion-*.vsix
   ```

### Data Processing Setup (Optional)

For custom model training or fine-tuning:

```bash
cd data-processing
pip install -r requirements.txt

# Download and prepare datasets
python dataset_loader.py

# Clean and process data
python data_cleaner.py

# Tokenize code samples
python tokenizer.py
```

## Configuration

### Backend Configuration

Edit `backend-api/app/utils/config.py`:

```python
# Model settings
MODEL_NAME = "microsoft/CodeGPT-small-py"
MAX_COMPLETION_LENGTH = 150
TEMPERATURE = 0.7
TOP_P = 0.9

# API settings
API_HOST = "localhost"
API_PORT = 8000
WORKERS = 4

# Cache settings
CACHE_TTL = 3600
CACHE_SIZE = 1000
```

### VS Code Extension Configuration

Edit `vscode-extension/src/config.ts`:

```typescript
export const CONFIG = {
  apiEndpoint: 'http://localhost:8000',
  completionDelay: 300,
  maxCompletions: 5,
  enableCache: true,
  supportedLanguages: ['python', 'javascript', 'java', 'cpp']
};
```

## Testing

### Run All Tests

```bash
# Make script executable
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

### Individual Test Suites

```bash
# Backend API tests
cd backend-api
python -m pytest tests/

# Model tests
cd ai-model
python -m pytest tests/

# Extension tests
cd vscode-extension
npm test
```

## Troubleshooting

### Common Issues

1. **Model Download Fails**
   - Check internet connection
   - Verify model names in configuration
   - Ensure sufficient disk space (~2GB)

2. **API Connection Issues**
   - Verify backend is running on correct port
   - Check firewall settings
   - Ensure no port conflicts

3. **Extension Not Loading**
   - Rebuild extension: `npm run build`
   - Check VS Code developer console for errors
   - Verify extension is enabled in VS Code

4. **Slow Completions**
   - Reduce `max_new_tokens` in model config
   - Enable caching in backend
   - Consider using smaller model variants

### Performance Optimization

1. **Model Optimization**
   ```python
   # In model configs, adjust for performance
   "max_new_tokens": 50,  # Reduce for faster inference
   "temperature": 0.5,    # Lower for more focused output
   "top_p": 0.8          # Reduce for faster sampling
   ```

2. **Caching**
   - Enable Redis for production caching
   - Adjust cache TTL based on usage patterns

3. **Resource Management**
   - Monitor GPU memory usage
   - Adjust batch sizes for inference
   - Consider model quantization for deployment

## Next Steps

1. **Development**: Start with the backend API and test basic completion
2. **Extension**: Build and test the VS Code extension
3. **Customization**: Modify model configurations for your specific use case
4. **Deployment**: Follow the deployment guide for production setup

For more detailed information, see:
- [API Documentation](api_docs.md)
- [Deployment Guide](deployment.md)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs in `logs/` directory
3. Verify all dependencies are installed correctly
4. Ensure models are properly downloaded and cached