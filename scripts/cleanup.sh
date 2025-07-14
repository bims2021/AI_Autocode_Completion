#!/bin/bash

# cleanup.sh - Cleanup script for Python Code Autocompletion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_IMAGE_NAME="code-autocompletion"

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

Cleanup script for Python Code Autocompletion

OPTIONS:
    -h, --help              Show this help message
    -a, --all               Clean all artifacts
    -d, --docker            Clean Docker images and containers
    -l, --logs              Clean log files
    -c, --cache             Clean cache directories
    -m, --models            Clean model cache
    -t, --temp              Clean temporary files
    -b, --backups           Clean old backups
    -p, --pyc               Clean Python cache files
    -f, --force             Force cleanup without confirmation
    --dry-run               Show what would be cleaned without actually cleaning

Examples:
    $0 -a                   # Clean everything
    $0 -d -l                # Clean Docker and logs
    $0 --dry-run            # Show what would be cleaned
EOF
}

# Function to clean Docker artifacts
clean_docker() {
    local dry_run=$1
    
    print_section "Cleaning Docker Artifacts"
    
    # Stop running containers
    local containers=$(docker ps -q --filter "name=$DOCKER_IMAGE_NAME" 2>/dev/null || true)
    if [[ -n "$containers" ]]; then
        print_status "Stopping containers: $containers"
        if [[ "$dry_run" != "true" ]]; then
            docker stop $containers
        fi
    fi
    
    # Remove containers
    local all_containers=$(docker ps -aq --filter "name=$DOCKER_IMAGE_NAME" 2>/dev/null || true)
    if [[ -n "$all_containers" ]]; then
        print_status "Removing containers: $all_containers"
        if [[ "$dry_run" != "true" ]]; then
            docker rm $all_containers
        fi
    fi
    
    # Remove images
    local images=$(docker images "$DOCKER_IMAGE_NAME" -q 2>/dev/null || true)
    if [[ -n "$images" ]]; then
        print_status "Removing images: $images"
        if [[ "$dry_run" != "true" ]]; then
            docker rmi $images
        fi
    fi
    
    # Clean unused Docker resources
    if [[ "$dry_run" != "true" ]]; then
        print_status "Cleaning unused Docker resources..."
        docker system prune -f
    else
        print_status "Would clean unused Docker resources"
    fi
}

# Function to clean log files
clean_logs() {
    local dry_run=$1
    
    print_section "Cleaning Log Files"
    
    local log_locations=(
        "/tmp/*.log"
        "/tmp/gunicorn*.log"
        "/tmp/uvicorn*.log"
        "/tmp/monitor.log"
        "$PROJECT_ROOT/logs/*.log"
        "$PROJECT_ROOT/*.log"
    )
    
    for pattern in "${log_locations[@]}"; do
        local files=($(ls $pattern 2>/dev/null || true))
        
        for file in "${files[@]}"; do
            if [[ -f "$file" ]]; then
                local size=$(du -h "$file" | cut -f1)
                print_status "Removing log file: $file ($size)"
                
                if [[ "$dry_run" != "true" ]]; then
                    rm -f "$file"
                fi
            fi
        done
    done
}

# Function to clean cache directories
clean_cache() {
    local dry_run=$1
    
    print_section "Cleaning Cache Directories"
    
    local cache_dirs=(
        "$HOME/.cache/pip"
        "$HOME/.cache/huggingface"
        "$PROJECT_ROOT/.pytest_cache"
        "$PROJECT_ROOT/.coverage"
        "$PROJECT_ROOT/node_modules"
        "$PROJECT_ROOT/vscode-extension/node_modules"
        "$PROJECT_ROOT/vscode-extension/out"
    )
    
    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            local size=$(du -sh "$cache_dir" 2>/dev/null | cut -f1)
            print_status "Removing cache directory: $cache_dir ($size)"
            
            if [[ "$dry_run" != "true" ]]; then
                rm -rf "$cache_dir"
            fi
        fi
    done
}

# Function to clean model cache
clean_models() {
    local dry_run=$1
    
    print_section "Cleaning Model Cache"
    
    local model_cache_dir="$HOME/.cache/ai-model"
    
    if [[ -d "$model_cache_dir" ]]; then
        local size=$(du -sh "$model_cache_dir" 2>/dev/null | cut -f1)
        print_warning "This will remove all cached AI models ($size)"
        print_warning "Models will need to be re-downloaded on next use"
        
        if [[ "$dry_run" != "true" ]]; then
            read -p "Are you sure you want to remove model cache? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "$model_cache_dir"
                print_status "Model cache removed"
            else
                print_status "Model cache cleanup skipped"
            fi
        else
            print_status "Would remove model cache: $model_cache_dir"
        fi
    else
        print_status "No model cache found"
    fi
}

# Function to clean temporary files
clean_temp() {
    local dry_run=$1
    
    print_section "Cleaning Temporary Files"
    
    local temp_patterns=(
        "/tmp/gunicorn.pid"
        "/tmp/uvicorn.pid"
        "/tmp/code-autocompletion-*"
        "$PROJECT_ROOT/tmp/*"
        "$PROJECT_ROOT/*.tmp"
        "$PROJECT_ROOT/*.temp"
    )
    
    for pattern in "${temp_patterns[@]}"; do
        local files=($(ls $pattern 2>/dev/null || true))
        
        for file in "${files[@]}"; do
            if [[ -f "$file" ]]; then
                print_status "Removing temporary file: $file"
                
                if [[ "$dry_run" != "true" ]]; then
                    rm -f "$file"
                fi
            fi
        done
    done
}

# Function to clean old backups
clean_backups() {
    local dry_run=$1
    
    print_section "Cleaning Old Backups"
    
    local backup_dir="$PROJECT_ROOT/backups"
    
    if [[ -d "$backup_dir" ]]; then
        local backup_files=($(ls -1t "$backup_dir"/*.tar.gz 2>/dev/null || true))
        local total_backups=${#backup_files[@]}
        
        if [[ $total_backups -gt 5 ]]; then
            local backups_to_remove=(${backup_files[@]:5})
            
            for backup in "${backups_to_remove[@]}"; do
                local size=$(du -h "$backup" | cut -f1)
                print_status "Removing old backup: $backup ($size)"
                
                if [[ "$dry_run" != "true" ]]; then
                    rm -f "$backup"
                fi
            done
        else
            print_status "No old backups to remove (keeping last 5)"
        fi
    else
        print_status "No backup directory found"
    fi
}

# Function to clean Python cache files
clean_pyc() {
    local dry_run=$1
    
    print_section "Cleaning Python Cache Files"
    
    cd "$PROJECT_ROOT"
    
    # Find and remove __pycache__ directories
    local pycache_dirs=($(find . -type d -name "__pycache__" 2>/dev/null || true))
    
    for cache_dir in "${pycache_dirs[@]}"; do
        print_status "Removing Python cache: $cache_dir"
        
        if [[ "$dry_run" != "true" ]]; then
            rm -rf "$cache_dir"
        fi
    done
    
    # Find and remove .pyc files
    local pyc_files=($(find . -name "*.pyc" 2>/dev/null || true))
    
    for pyc_file in "${pyc_files[@]}"; do
        print_status "Removing .pyc file: $pyc_file"
        
        if [[ "$dry_run" != "true" ]]; then
            rm -f "$pyc_file"
        fi
    done
    
    # Find and remove .pyo files
    local pyo_files=($(find . -name "*.pyo" 2>/dev/null || true))
    
    for pyo_file in "${pyo_files[@]}"; do
        print_status "Removing .pyo file: $pyo_file"
        
        if [[ "$dry_run" != "true" ]]; then
            rm -f "$pyo_file"
        fi
    done
}

# Function to calculate disk space freed
calculate_space_freed() {
    local before_size="$1"
    local after_size="$2"
    
    local freed=$((before_size - after_size))
    
    if [[ $freed -gt 0 ]]; then
        print_status "Disk space freed: $(numfmt --to=iec $freed)"
    else
        print_status "No significant disk space freed"
    fi
}

# Main function
main() {
    local clean_all=false
    local clean_docker=false
    local clean_logs=false
    local clean_cache=false
    local clean_models=false
    local clean_temp=false
    local clean_backups=false
    local clean_pyc=false
    local force=false
    local dry_run=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -a|--all)
                clean_all=true
                shift
                ;;
            -d|--docker)
                clean_docker=true
                shift
                ;;
            -l|--logs)
                clean_logs=true
                shift
                ;;
            -c|--cache)
                clean_cache=true
                shift
                ;;
            -m|--models)
                clean_models=true
                shift
                ;;
            -t|--temp)
                clean_temp=true
                shift
                ;;
            -b|--backups)
                clean_backups=true
                shift
                ;;
            -p|--pyc)
                clean_pyc=true
                shift
                ;;
            -f|--force)
                force=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # If no specific options are provided, show usage
    if [[ "$clean_all" == "false" && "$clean_docker" == "false" && "$clean_logs" == "false" && \
          "$clean_cache" == "false" && "$clean_models" == "false" && "$clean_temp" == "false" && \
          "$clean_backups" == "false" && "$clean_pyc" == "false" ]]; then
        show_usage
        exit 1
    fi
    
    # Set all flags if clean_all is true
    if [[ "$clean_all" == "true" ]]; then
        clean_docker=true
        clean_logs=true
        clean_cache=true
        clean_temp=true
        clean_backups=true
        clean_pyc=true
    fi
    
    # Show dry run notice
    if [[ "$dry_run" == "true" ]]; then
        print_section "DRY RUN MODE - No files will be actually removed"
    fi
    
    # Get initial disk usage
    local initial_size=$(du -sb "$PROJECT_ROOT" 2>/dev/null | cut -f1)
    
    # Confirmation for cleanup
    if [[ "$force" != "true" && "$dry_run" != "true" ]]; then
        print_warning "This will permanently remove files and directories"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleanup cancelled by user"
            exit 0
        fi
    fi
    
    print_section "Starting Cleanup Process"
    
    # Execute cleanup operations
    if [[ "$clean_docker" == "true" ]]; then
        clean_docker "$dry_run"
    fi
    
    if [[ "$clean_logs" == "true" ]]; then
        clean_logs "$dry_run"
    fi
    
    if [[ "$clean_cache" == "true" ]]; then
        clean_cache "$dry_run"
    fi
    
    if [[ "$clean_models" == "true" ]]; then
        clean_models "$dry_run"
    fi
    
    if [[ "$clean_temp" == "true" ]]; then
        clean_temp "$dry_run"
    fi
    
    if [[ "$clean_backups" == "true" ]]; then
        clean_backups "$dry_run"
    fi
    
    if [[ "$clean_pyc" == "true" ]]; then
        clean_pyc "$dry_run"
    fi
    
    # Calculate space freed
    if [[ "$dry_run" != "true" ]]; then
        local final_size=$(du -sb "$PROJECT_ROOT" 2>/dev/null | cut -f1)
        calculate_space_freed "$initial_size" "$final_size"
    fi
    
    print_section "Cleanup Complete"
    print_status "Cleanup process finished successfully"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi