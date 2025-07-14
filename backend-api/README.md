# AI Code Completion Backend API

A high-performance FastAPI backend service for AI-powered code completion, featuring intelligent context analysis, caching, and rate limiting.

## Features

- **AI-Powered Suggestions**: GPT-2 based code completion with context awareness
- **Language Support**: Python, JavaScript, TypeScript, Java, and more
- **Smart Context Analysis**: Function signatures, class information, imports, and variables
- **Redis Caching**: Efficient caching of suggestions with TTL
- **Rate Limiting**: Configurable rate limiting per user/tier
- **Production Ready**: Docker support, monitoring, and logging
- **Extensible**: Plugin architecture for additional language parsers

## Quick Start

### Development Setup

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd backend-api
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run Setup Script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

4. **Start Development Server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## API Usage

### Request Completion

```bash
curl -X POST "http://localhost:8000/api/v1/completion" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "language": "python",
      "position": {"line": 10, "column": 4},
      "previousLines": [
        "def fibonacci(n):",
        "    if n <= 1:",
        "        return n",
        "    return "
      ],
      "currentLine": ""
    },
    "max_suggestions": 3,
    "temperature": 0.7,
    "user_id": "user123"
  }'
```

### Response Format

```json
{
  "suggestions": [
    {
      "text": "fibonacci(n-1) + fibonacci(n-2)",
      "confidence": 0.9,
      "type": "single-line",
      "description": "Recursive fibonacci calculation",
      "cursorOffset": 29
    }
  ],
  "metadata": {
    "processingTimeMs": 150,
    "modelVersion": "gpt2-medium",
    "cacheHit": false,
    "contextHash": "abc123"
  },
  "status": "success"
}
```

## Architecture

### Core Components

- **FastAPI App**: Main application with middleware and routing
- **Model Service**: AI model management and inference
- **Context Processor**: Language-specific context analysis
- **Cache Service**: Redis-based caching layer
- **Rate Limiter**: Request throttling and quota management

### Language Parsers

- **Python Parser**: Function signatures, classes, imports, variables
- **JavaScript Parser**: Functions, arrow functions, modules
- **Extensible**: Add new parsers for additional languages

## Configuration

### Environment Variables

```env
# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
DEBUG=false

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Model
MODEL_PATH=gpt2
MAX_TOKENS=1024
```

### Rate Limit Tiers

- **Default**: 100 requests/hour
- **Premium**: 1000 requests/hour
- **Enterprise**: 10000 requests/hour

## Testing

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_completion.py -v

# Run with coverage
pytest --cov=app tests/
```

## Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8000/api/v1/metrics
```

### Prometheus + Grafana

1. **Start monitoring stack**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d prometheus grafana
   ```

2. **Access Grafana**
   - URL: http://localhost:3000
   - Login: admin/admin123

### Health Check

```bash
curl http://localhost:8000/health
```

## Performance Optimization

### Caching Strategy

- **Context-based caching**: Hash-based cache keys
- **TTL**: 1 hour default, configurable
- **Cache warming**: Pre-populate common patterns

### Model Optimization

- **Batch processing**: Multiple requests in single inference
- **Model quantization**: Reduce memory footprint
- **GPU acceleration**: CUDA support for inference

## Security

### Authentication

- User ID-based rate limiting
- Session management support
- API key validation (optional)

### Input Validation

- Pydantic models for request validation
- Context sanitization
- Length limits and timeouts

## Deployment

### Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Redis persistence enabled
- [ ] Log aggregation setup
- [ ] Monitoring dashboards configured
- [ ] Backup strategy implemented

### Scaling

- **Horizontal scaling**: Multiple API instances
- **Load balancing**: Nginx reverse proxy
- **Redis clustering**: High availability caching
- **CDN integration**: Static asset caching

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Run test suite
5. Submit pull request

## License

MIT License - see LICENSE file for details