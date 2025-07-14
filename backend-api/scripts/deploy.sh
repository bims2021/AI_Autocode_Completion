#!/bin/bash

# Deployment script for AI Code Completion Backend
set -e

echo "Deploying AI Code Completion Backend..."

# Build Docker image
echo "Building Docker image..."
docker build -t ai-completion-backend .

# Tag image with version
VERSION=$(cat version.txt || echo "1.0.0")
docker tag ai-completion-backend:latest ai-completion-backend:$VERSION

# Deploy with Docker Compose
echo "Deploying with Docker Compose..."
docker-compose -f docker-compose.prod.yml up -d

# Health check
echo "Waiting for service to start..."
sleep 10

# Check if service is running
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $HEALTH_CHECK -eq 200 ]; then
    echo "✅ Deployment successful! Service is running."
else
    echo "❌ Deployment failed! Health check returned: $HEALTH_CHECK"
    exit 1
fi

# Run post-deployment tests
echo "Running post-deployment tests..."
python -m pytest tests/test_integration.py -v

echo "Deployment completed successfully!"
