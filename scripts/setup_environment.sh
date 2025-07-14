#!/bin/bash

# setup_environment.sh - Setup development environment for Python Code Autocompletion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.9"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_NAME="code-autocompletion-env"

echo -e "${GREEN}Setting up Python Code Autocompletion Environment${NC}"
echo "Project root: $PROJECT_ROOT"
echo "Python version: $PYTHON_VERSION"
echo "Virtual environment: $VENV_NAME"
echo "=================================================="

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi
    
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_status "Found Python $PYTHON_VER"
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    cd "$PROJECT_ROOT"
    
    if [ -d "$VENV_NAME" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf "$VENV_NAME"
    fi
    
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Install global requirements
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
    else
        print_warning "Global requirements.txt not found. Installing common dependencies..."
        pip install fastapi uvicorn torch transformers datasets pydantic python-multipart
    fi
    
    # Install backend API dependencies
    if [ -f "$PROJECT_ROOT/backend-api/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/backend-api/requirements.txt"
    fi
    
    # Install AI model dependencies
    if [ -f "$PROJECT_ROOT/ai-model/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/ai-model/requirements.txt"
    fi
    
    # Install development dependencies
    pip install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit
}

# Create necessary directories
create_directories() {
    print_status "Creating project directories..."
    
    mkdir -p "$PROJECT_ROOT/backend-api/app/routes"
    mkdir -p "$PROJECT_ROOT/backend-api/app/services"
    mkdir -p "$PROJECT_ROOT/backend-api/app/models"
    mkdir -p "$PROJECT_ROOT/backend-api/app/utils"
    mkdir -p "$PROJECT_ROOT/ai-model/model_configs"
    mkdir -p "$PROJECT_ROOT/data-processing"
    mkdir -p "$PROJECT_ROOT/tests/test_api"
    mkdir -p "$PROJECT_ROOT/tests/test_model"
    mkdir -p "$PROJECT_ROOT/tests/test_extension"
    mkdir -p "$PROJECT_ROOT/docs"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/models"
    mkdir -p "$HOME/.cache/ai-model/codegpt"
    mkdir -p "$HOME/.cache/ai-model/codebert"
}

# Setup Node.js environment for VS Code extension
setup_nodejs() {
    print_status "Setting up Node.js environment for VS Code extension..."
    
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Please install Node.js 16+ for VS Code extension development."
        return 1
    fi
    
    if [ -d "$PROJECT_ROOT/vscode-extension" ]; then
        cd "$PROJECT_ROOT/vscode-extension"
        if [ -f "package.json" ]; then
            print_status "Installing Node.js dependencies..."
            npm install
        else
            print_warning "package.json not found in vscode-extension directory"
        fi
    else
        print_warning "vscode-extension directory not found"
    fi
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    if [ -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]; then
        pre-commit install
        print_status "Pre-commit hooks installed"
    else
        print_warning "No .pre-commit-config.yaml found. Creating basic configuration..."
        cat > "$PROJECT_ROOT/.pre-commit-config.yaml" << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF
        pre-commit install
    fi
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        cat > "$PROJECT_ROOT/.env" << EOF
# Development environment configuration
ENVIRONMENT=development
DEBUG=true

# API Configuration
API_HOST=localhost
API_PORT=8000
API_WORKERS=1

# Model Configuration
MODEL_CACHE_DIR=$HOME/.cache/ai-model
CODEGPT_MODEL_NAME=microsoft/CodeGPT-small-py
CODEBERT_MODEL_NAME=microsoft/codebert-base

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Database (if needed)
DATABASE_URL=sqlite:///./code_autocompletion.db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
        print_status "Environment file created at $PROJECT_ROOT/.env"
    else
        print_warning "Environment file already exists"
    fi
}

# Create basic configuration files
create_config_files() {
    print_status "Creating configuration files..."
    
    # Create pytest configuration
    if [ ! -f "$PROJECT_ROOT/pytest.ini" ]; then
        cat > "$PROJECT_ROOT/pytest.ini" << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
EOF
    fi
    
    # Create mypy configuration
    if [ ! -f "$PROJECT_ROOT/mypy.ini" ]; then
        cat > "$PROJECT_ROOT/mypy.ini" << EOF
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
EOF
    fi
}

# Main execution
main() {
    print_status "Starting environment setup..."
    
    check_python
    create_venv
    install_dependencies
    create_directories
    setup_nodejs
    setup_pre_commit
    create_env_file
    create_config_files
    
    echo ""
    echo -e "${GREEN}Environment setup completed successfully!${NC}"
    echo ""
    echo "To activate the virtual environment:"
    echo "  source $VENV_NAME/bin/activate"
    echo ""
    echo "To deactivate:"
    echo "  deactivate"
    echo ""
    echo "Next steps:"
    echo "  1. Activate the virtual environment"
    echo "  2. Run: python scripts/download_models.py"
    echo "  3. Run: python scripts/run_tests.sh"
    echo "  4. Start development server: uvicorn backend-api.app.main:app --reload"
    echo ""
    echo -e "${GREEN}Happy coding!${NC}"
}

# Run main function
main "$@"