#!/bin/bash

# deploy.sh - Deployment script for Python Code Autocompletion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_ENV="production"
DOCKER_IMAGE_NAME="code-autocompletion"
DOCKER_TAG="latest"
HEALTH_CHECK_URL="http://localhost:8000/health"
HEALTH_CHECK_TIMEOUT=60

# Default deployment settings
BUILD_DOCKER=true
RUN_TESTS=true
CREATE_BACKUP=true
DEPLOY_API=true
DEPLOY_MODELS=true
FORCE_DEPLOYMENT=false
VERBOSE=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deployment script for Python Code Autocompletion

OPTIONS:
    -h, --help              Show this help message
    -e, --env ENV           Deployment environment (dev, staging, production)
    -t, --tag TAG           Docker image tag (default: latest)
    -v, --verbose           Enable verbose output
    -f, --force             Force deployment without confirmation
    
    --no-docker             Skip Docker build
    --no-tests              Skip running tests before deployment
    --no-backup             Skip creating backup
    --api-only              Deploy only API components
    --models-only           Deploy only AI models
    --health-timeout N      Health check timeout in seconds (default: 60)

Examples:
    $0                      # Deploy to production with default settings
    $0 -e staging           # Deploy to staging environment
    $0 --no-tests --force   # Deploy without tests and confirmation
    $0 --api-only -t v1.2.3 # Deploy only API with specific tag
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -e|--env)
                DEPLOYMENT_ENV="$2"
                shift 2
                ;;
            -t|--tag)
                DOCKER_TAG="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force)
                FORCE_DEPLOYMENT=true
                shift
                ;;
            --no-docker)
                BUILD_DOCKER=false
                shift
                ;;
            --no-tests)
                RUN_TESTS=false
                shift
                ;;
            --no-backup)
                CREATE_BACKUP=false
                shift
                ;;
            --api-only)
                DEPLOY_API=true
                DEPLOY_MODELS=false
                shift
                ;;
            --models-only)
                DEPLOY_API=false
                DEPLOY_MODELS=true
                shift
                ;;
            --health-timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking deployment prerequisites..."
    
    # Check Docker
    if [[ "$BUILD_DOCKER" == "true" ]]; then
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed or not in PATH"
            exit 1
        fi
        
        if ! docker info &> /dev/null; then
            print_error "Docker daemon is not running"
            exit 1
        fi
    fi
    
    # Check git repository status
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        cd "$PROJECT_ROOT"
        
        if [[ -n "$(git status --porcelain)" ]]; then
            print_warning "Repository has uncommitted changes"
            if [[ "$FORCE_DEPLOYMENT" != "true" ]]; then
                read -p "Continue deployment? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        fi
        
        # Get current branch and commit
        local current_branch=$(git rev-parse --abbrev-ref HEAD)
        local current_commit=$(git rev-parse --short HEAD)
        
        print_status "Current branch: $current_branch"
        print_status "Current commit: $current_commit"
        
        # Set Docker tag to commit if not specified
        if [[ "$DOCKER_TAG" == "latest" ]]; then
            DOCKER_TAG="$current_commit"
        fi
    fi
    
    # Check environment file
    if [[ ! -f "$PROJECT_ROOT/.env.$DEPLOYMENT_ENV" ]]; then
        print_warning "Environment file .env.$DEPLOYMENT_ENV not found"
        if [[ -f "$PROJECT_ROOT/.env" ]]; then
            print_status "Using default .env file"
        else
            print_error "No environment configuration found"
            exit 1
        fi
    fi
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    if [[ "$RUN_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_section "Running Pre-Deployment Tests"
    
    if [[ -f "$PROJECT_ROOT/scripts/run_tests.sh" ]]; then
        print_status "Running test suite..."
        if ! bash "$PROJECT_ROOT/scripts/run_tests.sh" --no-lint --no-type-check; then
            print_error "Tests failed. Deployment aborted."
            exit 1
        fi
    else
        print_warning "Test script not found. Skipping tests."
    fi
}

# Function to create backup
create_backup() {
    if [[ "$CREATE_BACKUP" != "true" ]]; then
        return 0
    fi
    
    print_section "Creating Backup"
    
    local backup_dir="$PROJECT_ROOT/backups"
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$backup_dir/$backup_name"
    
    mkdir -p "$backup_dir"
    
    # Create backup archive
    print_status "Creating backup archive..."
    tar -czf "$backup_path.tar.gz" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='*.log' \
        --exclude='backups' \
        -C "$PROJECT_ROOT" .
    
    print_status "Backup created: $backup_path.tar.gz"
    
    # Keep only last 10 backups
    local backup_count=$(ls -1 "$backup_dir"/*.tar.gz 2>/dev/null | wc -l)
    if [[ $backup_count -gt 10 ]]; then
        print_status "Cleaning old backups..."
        ls -1t "$backup_dir"/*.tar.gz | tail -n +11 | xargs rm -f
    fi
}

# Function to build Docker image
build_docker_image() {
    if [[ "$BUILD_DOCKER" != "true" ]]; then
        return 0
    fi
    
    print_section "Building Docker Image"
    
    cd "$PROJECT_ROOT"
    
    # Check if Dockerfile exists
    if [[ ! -f "Dockerfile" ]]; then
        print_error "Dockerfile not found in project root"
        exit 1
    fi
    
    local full_image_name="$DOCKER_IMAGE_NAME:$DOCKER_TAG"
    
    print_status "Building Docker image: $full_image_name"
    
    # Build Docker image
    if [[ "$VERBOSE" == "true" ]]; then
        docker build -t "$full_image_name" .
    else
        docker build -t "$full_image_name" . --quiet
    fi
    
    # Tag as latest if not already
    if [[ "$DOCKER_TAG" != "latest" ]]; then
        docker tag "$full_image_name" "$DOCKER_IMAGE_NAME:latest"
    fi
    
    print_status "Docker image built successfully"
}

# Function to stop existing services
stop_existing_services() {
    print_section "Stopping Existing Services"
    
    # Stop Docker containers
    if command -v docker &> /dev/null; then
        local containers=$(docker ps -q --filter "name=$DOCKER_IMAGE_NAME")
        if [[ -n "$containers" ]]; then
            print_status "Stopping existing containers..."
            docker stop $containers
            docker rm $containers
        fi
    fi
    
    # Kill processes using port 8000
    local pid=$(lsof -ti:8000 2>/dev/null || true)
    if [[ -n "$pid" ]]; then
        print_status "Killing process using port 8000..."
        kill -9 "$pid" 2>/dev/null || true
    fi
}

# Function to deploy AI models
deploy_models() {
    if [[ "$DEPLOY_MODELS" != "true" ]]; then
        return 0
    fi
    
    print_section "Deploying AI Models"
    
    # Download/update models
    if [[ -f "$PROJECT_ROOT/scripts/download_models.py" ]]; then
        print_status "Downloading/updating AI models..."
        python "$PROJECT_ROOT/scripts/download_models.py" --verify
    else
        print_warning "Model download script not found"
    fi
    
    # Set appropriate permissions
    local model_cache_dir="$HOME/.cache/ai-model"
    if [[ -d "$model_cache_dir" ]]; then
        chmod -R 755 "$model_cache_dir"
    fi
}

# Function to deploy API
deploy_api() {
    if [[ "$DEPLOY_API" != "true" ]]; then
        return 0
    fi
    
    print_section "Deploying API"
    
    cd "$PROJECT_ROOT"
    
    # Load environment variables
    local env_file=".env.$DEPLOYMENT_ENV"
    if [[ -f "$env_file" ]]; then
        source "$env_file"
    elif [[ -f ".env" ]]; then
        source ".env"
    fi
    
    # Start the API service
    if [[ "$BUILD_DOCKER" == "true" ]]; then
        # Deploy using Docker
        local full_image_name="$DOCKER_IMAGE_NAME:$DOCKER_TAG"
        
        print_status "Starting API service with Docker..."
        docker run -d \
            --name "$DOCKER_IMAGE_NAME" \
            -p 8000:8000 \
            -v "$HOME/.cache/ai-model:/root/.cache/ai-model" \
            --env-file "$env_file" \
            "$full_image_name"
    else
        # Deploy using virtual environment
        print_status "Starting API service..."
        
        # Activate virtual environment if exists
        if [[ -d "venv" ]]; then
            source venv/bin/activate
        elif [[ -d "code-autocompletion-env" ]]; then
            source code-autocompletion-env/bin/activate
        fi
        
        # Start with gunicorn for production
        if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
            gunicorn backend-api.app.main:app \
                --workers 4 \
                --worker-class uvicorn.workers.UvicornWorker \
                --bind 0.0.0.0:8000 \
                --daemon \
                --pid /tmp/gunicorn.pid \
                --log-file /tmp/gunicorn.log \
                --access-logfile /tmp/gunicorn-access.log
        else
            # Development deployment
            uvicorn backend-api.app.main:app \
                --host 0.0.0.0 \
                --port 8000 \
                --reload &
            
            echo $! > /tmp/uvicorn.pid
        fi
    fi
}

# Function to perform health check
perform_health_check() {
    print_section "Performing Health Check"
    
    local start_time=$(date +%s)
    local timeout_time=$((start_time + HEALTH_CHECK_TIMEOUT))
    
    print_status "Waiting for service to start..."
    
    while [[ $(date +%s) -lt $timeout_time ]]; do
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            print_status "Health check passed"
            return 0
        fi
        
        sleep 5
        echo -n "."
    done
    
    echo ""
    print_error "Health check failed after ${HEALTH_CHECK_TIMEOUT}s"
    return 1
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    print_section "Running Post-Deployment Tests"
    
    # Test API endpoints
    print_status "Testing API endpoints..."
    
    # Test health endpoint
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
        print_status "Health endpoint: OK"
    else
        print_error "Health endpoint: FAILED"
        return 1
    fi
    
    # Test completion endpoint
    local completion_url="http://localhost:8000/complete"
    local test_payload='{"code": "def hello():", "language": "python"}'
    
    if curl -f -s -X POST "$completion_url" \
        -H "Content-Type: application/json" \
        -d "$test_payload" > /dev/null; then
        print_status "Completion endpoint: OK"
    else
        print_error "Completion endpoint: FAILED"
        return 1
    fi
    
    print_status "Post-deployment tests passed"
}

# Function to create deployment summary
create_deployment_summary() {
    print_section "Deployment Summary"
    
    local deployment_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat << EOF
Deployment completed successfully!

Environment: $DEPLOYMENT_ENV
Docker Image: $DOCKER_IMAGE_NAME:$DOCKER_TAG
Deployment Time: $deployment_time

Services deployed:
$(if [[ "$DEPLOY_API" == "true" ]]; then echo "  ✓ API Service"; fi)
$(if [[ "$DEPLOY_MODELS" == "true" ]]; then echo "  ✓ AI Models"; fi)

Health Check URL: $HEALTH_CHECK_URL
API Documentation: http://localhost:8000/docs

Next steps:
1. Monitor logs: docker logs $DOCKER_IMAGE_NAME
2. Check metrics: curl $HEALTH_CHECK_URL
3. Test functionality: curl -X POST http://localhost:8000/complete

EOF
}

# Function to rollback deployment
rollback_deployment() {
    print_section "Rolling Back Deployment"
    
    print_status "Stopping current services..."
    stop_existing_services
    
    # Restore from backup if available
    local backup_dir="$PROJECT_ROOT/backups"
    if [[ -d "$backup_dir" ]]; then
        local latest_backup=$(ls -1t "$backup_dir"/*.tar.gz 2>/dev/null | head -n1)
        if [[ -n "$latest_backup" ]]; then
            print_status "Restoring from backup: $latest_backup"
            # Note: This is a simplified rollback - in production, you'd want more sophisticated rollback logic
            print_warning "Manual rollback required. Latest backup: $latest_backup"
        fi
    fi
    
    print_status "Rollback completed"
}

# Function to cleanup deployment artifacts
cleanup() {
    print_status "Cleaning up deployment artifacts..."
    
    # Remove temporary files
    rm -f /tmp/gunicorn.pid
    rm -f /tmp/uvicorn.pid
    
    # Clean up old Docker images
    if command -v docker &> /dev/null; then
        local old_images=$(docker images "$DOCKER_IMAGE_NAME" --format "table {{.Repository}}:{{.Tag}}" | tail -n +2 | head -n -3)
        if [[ -n "$old_images" ]]; then
            print_status "Removing old Docker images..."
            echo "$old_images" | xargs -r docker rmi
        fi
    fi
}

# Main deployment function
main() {
    print_section "Python Code Autocompletion Deployment"
    
    # Parse arguments
    parse_args "$@"
    
        # Show deployment configuration
    print_status "Deployment Configuration:"
    echo "  Environment: $DEPLOYMENT_ENV"
    echo "  Docker Image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
    echo "  Deploy API: $DEPLOY_API"
    echo "  Deploy Models: $DEPLOY_MODELS"
    echo "  Build Docker: $BUILD_DOCKER"
    echo "  Run Tests: $RUN_TESTS"
    echo "  Create Backup: $CREATE_BACKUP"
    echo
    
    # Confirmation for production deployment
    if [[ "$DEPLOYMENT_ENV" == "production" && "$FORCE_DEPLOYMENT" != "true" ]]; then
        print_warning "You are about to deploy to PRODUCTION environment"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    # Trap for cleanup on exit
    trap cleanup EXIT
    
    # Execute deployment steps
    check_prerequisites
    
    if [[ "$RUN_TESTS" == "true" ]]; then
        run_pre_deployment_tests
    fi
    
    if [[ "$CREATE_BACKUP" == "true" ]]; then
        create_backup
    fi
    
    if [[ "$BUILD_DOCKER" == "true" ]]; then
        build_docker_image
    fi
    
    stop_existing_services
    
    if [[ "$DEPLOY_MODELS" == "true" ]]; then
        deploy_models
    fi
    
    if [[ "$DEPLOY_API" == "true" ]]; then
        deploy_api
    fi
    
    # Wait for services to start
    sleep 10
    
    # Perform health check
    if ! perform_health_check; then
        print_error "Health check failed. Rolling back deployment..."
        rollback_deployment
        exit 1
    fi
    
    # Run post-deployment tests
    if ! run_post_deployment_tests; then
        print_error "Post-deployment tests failed. Rolling back deployment..."
        rollback_deployment
        exit 1
    fi
    
    # Create deployment summary
    create_deployment_summary
    
    print_status "Deployment completed successfully!"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi