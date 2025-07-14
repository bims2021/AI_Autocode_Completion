# Deployment Guide - Python Code Autocompletion

This guide covers deployment strategies for the Python Code Autocompletion system across different environments, from development to production.

## Overview

The system consists of three main components:
1. **Backend API** - Python FastAPI application
2. **AI Models** - CodeGPT and CodeBERT models
3. **VS Code Extension** - TypeScript-based editor plugin

## Deployment Options

### 1. Local Development

For development and testing purposes.

#### Requirements
- Python 3.8+
- Node.js 16+
- 4GB+ RAM
- 10GB+ free disk space

#### Setup
```bash
# Clone repository
git clone <repository-url>
cd python-code-autocompletion

# Setup backend
cd backend-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup extension
cd ../vscode-extension
npm install
npm run build

# Download models
python ../scripts/download_models.py
```

#### Run
```bash
# Start backend
cd backend-api
python -m app.main

# Install extension in VS Code
cd ../vscode-extension
code --install-extension python-code-autocompletion-*.vsix
```

### 2. Docker Deployment

Containerized deployment for consistency across environments.

#### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: 
      context: ./backend-api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MODEL_CACHE_PATH=/app/models
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379
    volumes:
      - model_cache:/app/models
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  model_cache:
  redis_data:
```

#### Backend Dockerfile

Create `backend-api/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/models /app/logs

# Download models
RUN python scripts/download_models.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["python", "-m", "app.main"]
```

#### Deployment Commands

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API service
docker-compose up -d --scale api=3

# Update deployment
docker-compose pull
docker-compose up -d
```

### 3. Cloud Deployment

#### AWS Deployment

**Using AWS ECS (Recommended)**

1. **Create ECS Cluster**
```bash
# Create cluster
aws ecs create-cluster --cluster-name code-autocompletion

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

2. **Task Definition** (`task-definition.json`):
```json
{
  "family": "code-autocompletion",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-registry/code-autocompletion:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MODEL_CACHE_PATH",
          "value": "/app/models"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/code-autocompletion",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create Service**
```bash
aws ecs create-service \
  --cluster code-autocompletion \
  --service-name api-service \
  --task-definition code-autocompletion:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

**Using AWS Lambda (Serverless)**

For lighter workloads, deploy as Lambda function:

```python
# lambda_handler.py
import json
from mangum import Mangum
from app.main import app

handler = Mangum(app)

def lambda_handler(event, context):
    return handler(event, context)
```

**Deploy with Serverless Framework**:

```yaml
# serverless.yml
service: code-autocompletion

provider:
  name: aws
  runtime: python3.9
  region: us-west-2
  timeout: 30
  memorySize: 3008

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements
```

#### Google Cloud Deployment

**Using Cloud Run**:

```bash
# Build and push container
gcloud builds submit --tag gcr.io/PROJECT-ID/code-autocompletion

# Deploy to Cloud Run
gcloud run deploy code-autocompletion \
  --image gcr.io/PROJECT-ID/code-autocompletion \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10
```

#### Azure Deployment

**Using Azure Container Instances**:

```bash
# Create resource group
az group create --name code-autocompletion --location eastus

# Deploy container
az container create \
  --resource-group code-autocompletion \
  --name api \
  --image your-registry/code-autocompletion:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables MODEL_CACHE_PATH=/app/models
```

### 4. Kubernetes Deployment

For large-scale deployments with orchestration needs.

#### Kubernetes Manifests

**Deployment** (`k8s/deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-autocompletion-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: code-autocompletion-api
  template:
    metadata:
      labels:
        app: code-autocompletion-api
    spec:
      containers:
      - name: api
        image: your-registry/code-autocompletion:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_CACHE_PATH
          value: "/app/models"
        - name: LOG_LEVEL
          value: "INFO"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: model-cache
          mountPath: /app/models
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
```

**Service** (`k8s/service.yaml`):
```yaml
apiVersion: v1
kind: Service
metadata:
  name: code-autocompletion-service
spec:
  selector:
    app: code-autocompletion-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Ingress** (`k8s/ingress.yaml`):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: code-autocompletion-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.codeautocompletion.com
    secretName: code-autocompletion-tls
  rules:
  - host: api.codeautocompletion.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: code-autocompletion-service
            port:
              number: 80
```

**Deploy to Kubernetes**:
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=code-autocompletion-api

# View logs
kubectl logs -f deployment/code-autocompletion-api

# Scale deployment
kubectl scale deployment code-autocompletion-api --replicas=5
```

## VS Code Extension Distribution

### 1. Private Distribution

**Package Extension**:
```bash
cd vscode-extension
npm install -g vsce
vsce package
```

**Install Locally**:
```bash
code --install-extension python-code-autocompletion-*.vsix
```

**Enterprise Distribution**:
```bash
# Create enterprise package
vsce package --baseContentUrl https://your-company.com/extensions/

# Distribute via internal registry
npm publish --registry https://your-npm-registry.com
```

### 2. VS Code Marketplace

**Prepare for Marketplace**:
1. Update `package.json` with marketplace info
2. Add publisher account
3. Create marketplace listing

```json
{
  "publisher": "your-publisher-name",
  "displayName": "Python Code Autocompletion",
  "description": "AI-powered code completion for Python",
  "categories": ["Programming Languages", "Machine Learning"],
  "keywords": ["python", "autocomplete", "ai", "codegpt"],
  "icon": "icon.png",
  "repository": {
    "type": "git",
    "url": "https://github.com/your-org/python-code-autocompletion"
  }
}
```

**Publish to Marketplace**:
```bash
# Login to Azure DevOps
vsce login your-publisher-name

# Publish extension
vsce publish
```

## Production Configuration

### 1. Environment Variables

**Backend Configuration**:
```bash
# .env.production
MODEL_CACHE_PATH=/app/models
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# Database
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://user:pass@db:5432/codeautocompletion

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://your-domain.com

# Model settings
MAX_COMPLETION_LENGTH=150
CACHE_TTL=3600
RATE_LIMIT=500

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_PORT=9090
```

### 2. Nginx Configuration

**Production Nginx Config** (`nginx.conf`):
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name api.codeautocompletion.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.codeautocompletion.com;

        ssl_certificate /etc/ssl/cert.pem;
        ssl_certificate_key /etc/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API proxy
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check
        location /health {
            access_log off;
            proxy_pass http://api/api/v1/health;
        }
    }
}
```

### 3. Monitoring and Logging

**Prometheus Configuration** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'code-autocompletion'
    static_configs:
      - targets: ['api:9090']
    metrics_path: /metrics
    scrape_interval: 5s
```

**Grafana Dashboard** (JSON config):
```json
{
  "dashboard": {
    "title": "Code Autocompletion Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 4. Security Considerations

**API Security**:
```python
# app/middleware/security.py
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/minute")
async def completion_endpoint(request: Request):
    # Endpoint logic
    pass

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Extension Security**:
```typescript
// vscode-extension/src/security.ts
export class SecurityManager {
    private static validateResponse(response: any): boolean {
        // Validate response structure
        return response && 
               typeof response === 'object' && 
               Array.isArray(response.completions);
    }

    private static sanitizeCode(code: string): string {
        // Remove potentially dangerous code patterns
        return code.replace(/eval\(|exec\(|__import__/g, '');
    }
}
```

## Performance Optimization

### 1. Model Optimization

**Model Quantization**:
```python
# ai-model/optimization.py
import torch
from transformers import AutoModelForCausalLM

def quantize_model(model_path: str, output_path: str):
    model = AutoModelForCausalLM.from_pretrained(model_path)
    quantized_model = torch.quantization.quantize_dynamic(
        model, 
        {torch.nn.Linear}, 
        dtype=torch.qint8
    )
    quantized_model.save_pretrained(output_path)
```

**Model Caching**:
```python
# ai-model/cache.py
import functools
import hashlib

def cache_inference(func):
    @functools.wraps(func)
    def wrapper(self, code: str, language: str, **kwargs):
        # Create cache key
        cache_key = hashlib.sha256(
            f"{code}:{language}:{str(kwargs)}".encode()
        ).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Generate and cache result
        result = func(self, code, language, **kwargs)
        self.cache[cache_key] = result
        return result
    
    return wrapper
```

### 2. Database Optimization

**Redis Configuration**:
```redis
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0
```

**PostgreSQL Configuration** (for analytics):
```sql
-- Create indexes for common queries
CREATE INDEX idx_completions_timestamp ON completions(created_at);
CREATE INDEX idx_completions_language ON completions(language);
CREATE INDEX idx_completions_user ON completions(user_id);
```

### 3. CDN and Caching

**CloudFlare Configuration**:
```javascript
// cloudflare-worker.js
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Cache static assets
  if (request.url.includes('/static/')) {
    const cache = caches.default
    const response = await cache.match(request)
    
    if (response) {
      return response
    }
  }
  
  // Proxy to origin
  return fetch(request)
}
```

## Maintenance and Updates

### 1. Automated Deployment

**GitHub Actions Workflow** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        docker build -t ${{ secrets.REGISTRY }}/code-autocompletion:${{ github.sha }} .
        docker push ${{ secrets.REGISTRY }}/code-autocompletion:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/code-autocompletion-api \
          api=${{ secrets.REGISTRY }}/code-autocompletion:${{ github.sha }}
```

### 2. Model Updates

**Model Update Script**:
```bash
#!/bin/bash
# scripts/update_models.sh

# Download new models
python scripts/download_models.py --version latest

# Test new models
python -m pytest tests/test_models.py

# Deploy with zero downtime
kubectl rollout restart deployment/code-autocompletion-api
kubectl rollout status deployment/code-autocompletion-api
```

### 3. Database Migrations

**Migration Script**:
```python
# scripts/migrate.py
import asyncio
from sqlalchemy import create_engine
from alembic import command
from alembic.config import Config

async def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    asyncio.run(run_migrations())
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Reduce model batch size
   - Enable model quantization
   - Use gradient checkpointing

2. **Slow Response Times**
   - Optimize model inference
   - Add Redis caching
   - Use CDN for static assets

3. **Extension Not Working**
   - Check API endpoint configuration
   - Verify CORS settings
   - Review extension logs

### Monitoring Commands

```bash
# Check service health
curl -f http://localhost:8000/api/v1/health

# Monitor logs
docker-compose logs -f api

# Check resource usage
docker stats

# Kubernetes monitoring
kubectl top pods
kubectl describe pod <pod-name>
```

## Backup and Recovery

### Database Backup

```bash
# Redis backup
redis-cli BGSAVE

# PostgreSQL backup
pg_dump codeautocompletion > backup.sql
```

### Model Backup

```bash
# Backup models to S3
aws s3 sync ~/.cache/ai-model/ s3://your-bucket/models/

# Restore models
aws s3 sync s3://your-bucket/models/ ~/.cache/ai-model/
```

## Cost Optimization

### 1. Resource Scaling

**Auto-scaling Configuration**:
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: code-autocompletion-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: code-autocompletion-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 2. Spot Instances

**AWS Spot Instance Configuration**:
```yaml
# Use spot instances for non-critical workloads
nodeSelector:
  node-type: spot
tolerations:
- key: "spot-instance"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

This deployment guide provides comprehensive coverage of different deployment scenarios, from development to production-scale deployments. Choose the approach that best fits your infrastructure requirements and scale needs.