#!/bin/bash

# Setup script for AI Code Completion Backend
set -e

echo "Setting up AI Code Completion Backend..."

# Create directories
mkdir -p logs
mkdir -p data
mkdir -p nginx/ssl

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Download model (if not exists)
echo "Checking for model files..."
python -c "
from transformers import GPT2LMHeadModel, GPT2Tokenizer
print('Downloading GPT-2 model...')
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')
print('Model downloaded successfully')
"

# Generate SSL certificates for development
if [ ! -f nginx/ssl/cert.pem ]; then
    echo "Generating SSL certificates for development..."
    openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes -subj '/CN=localhost'
fi

# Set up Redis (if using Docker)
echo "Setting up Redis..."
docker-compose up -d redis

# Run database migrations (if any)
echo "Running database setup..."
# Add any database setup commands here

echo "Setup completed successfully!"
echo "To start the server:"
echo "  Development: uvicorn app.main:app --reload"
echo "  Production: docker-compose up"