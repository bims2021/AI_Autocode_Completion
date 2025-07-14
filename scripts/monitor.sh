#!/bin/bash

# monitor.sh - Monitoring script for Python Code Autocompletion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEALTH_CHECK_URL="http://localhost:8000/health"
METRICS_URL="http://localhost:8000/metrics"
LOG_FILE="/tmp/monitor.log"
ALERT_EMAIL=""
ALERT_THRESHOLD=5

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

# Function to check service health
check_service_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "[$timestamp] Service health: OK" >> "$LOG_FILE"
        return 0
    else
        echo "[$timestamp] Service health: FAILED" >> "$LOG_FILE"
        return 1
    fi
}

# Function to check Docker container status
check_docker_status() {
    local container_name="code-autocompletion"
    
    if docker ps --filter "name=$container_name" --format "table {{.Names}}" | grep -q "$container_name"; then
        print_status "Docker container: Running"
        return 0
    else
        print_error "Docker container: Not running"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    
    print_status "System Resources:"
    echo "  CPU Usage: ${cpu_usage}%"
    echo "  Memory Usage: ${memory_usage}%"
    echo "  Disk Usage: ${disk_usage}%"
    
    # Check for high resource usage
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        print_warning "High CPU usage detected: ${cpu_usage}%"
    fi
    
    if (( $(echo "$memory_usage > 80" | bc -l) )); then
        print_warning "High memory usage detected: ${memory_usage}%"
    fi
    
    if (( disk_usage > 80 )); then
        print_warning "High disk usage detected: ${disk_usage}%"
    fi
}

# Function to check API metrics
check_api_metrics() {
    if curl -f -s "$METRICS_URL" > /dev/null 2>&1; then
        local metrics=$(curl -s "$METRICS_URL")
        
        print_status "API Metrics:"
        echo "$metrics" | jq -r '
            "  Total Requests: \(.total_requests // 0)",
            "  Success Rate: \(.success_rate // 0)%",
            "  Average Response Time: \(.avg_response_time // 0)ms",
            "  Active Connections: \(.active_connections // 0)"
        ' 2>/dev/null || echo "  Metrics parsing failed"
    else
        print_warning "Unable to fetch API metrics"
    fi
}

# Function to check log files
check_logs() {
    local log_dirs=("/tmp" "/var/log" "$PROJECT_ROOT/logs")
    local log_patterns=("*.log" "gunicorn*.log" "uvicorn*.log")
    
    print_status "Recent log entries:"
    
    for log_dir in "${log_dirs[@]}"; do
        if [[ -d "$log_dir" ]]; then
            for pattern in "${log_patterns[@]}"; do
                local log_files=($(find "$log_dir" -name "$pattern" -type f 2>/dev/null))
                
                for log_file in "${log_files[@]}"; do
                    if [[ -f "$log_file" ]]; then
                        local error_count=$(grep -c "ERROR\|CRITICAL\|Exception" "$log_file" 2>/dev/null || echo 0)
                        
                        if [[ $error_count -gt 0 ]]; then
                            print_warning "Found $error_count errors in $log_file"
                            echo "  Last 3 errors:"
                            grep "ERROR\|CRITICAL\|Exception" "$log_file" | tail -3 | sed 's/^/    /'
                        fi
                    fi
                done
            done
        fi
    done
}

# Function to send alert
send_alert() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [[ -n "$ALERT_EMAIL" ]]; then
        echo "[$timestamp] ALERT: $message" | mail -s "Code Autocompletion Alert" "$ALERT_EMAIL"
    fi
    
    # Log alert
    echo "[$timestamp] ALERT: $message" >> "$LOG_FILE"
}

# Function to monitor continuously
monitor_continuous() {
    local interval=${1:-60}  # Default 60 seconds
    local failure_count=0
    
    print_status "Starting continuous monitoring (interval: ${interval}s)"
    print_status "Press Ctrl+C to stop"
    
    while true; do
        clear
        print_section "System Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
        
        # Check service health
        if check_service_health; then
            print_status "Service: Healthy"
            failure_count=0
        else
            print_error "Service: Unhealthy"
            failure_count=$((failure_count + 1))
            
            if [[ $failure_count -ge $ALERT_THRESHOLD ]]; then
                send_alert "Service has been unhealthy for $failure_count checks"
                failure_count=0  # Reset after sending alert
            fi
        fi
        
        # Check Docker status
        check_docker_status
        
        # Check system resources
        check_system_resources
        
        # Check API metrics
        check_api_metrics
        
        # Wait for next check
        sleep "$interval"
    done
}

# Function to run single check
run_single_check() {
    print_section "System Status Check - $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Service health
    if check_service_health; then
        print_status "Service: Healthy"
    else
        print_error "Service: Unhealthy"
    fi
    
    # Docker status
    check_docker_status
    
    # System resources
    check_system_resources
    
    # API metrics
    check_api_metrics
    
    # Log files
    check_logs
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Monitoring script for Python Code Autocompletion

OPTIONS:
    -h, --help              Show this help message
    -c, --continuous        Run continuous monitoring
    -i, --interval N        Monitoring interval in seconds (default: 60)
    -e, --email EMAIL       Alert email address
    -t, --threshold N       Alert threshold (default: 5)
    -l, --logs              Show recent log entries
    --health-only           Check only service health
    --metrics-only          Check only API metrics

Examples:
    $0                      # Run single status check
    $0 -c                   # Run continuous monitoring
    $0 -c -i 30             # Monitor every 30 seconds
    $0 -e admin@example.com # Set alert email
    $0 --logs               # Show recent log entries
EOF
}

# Main function
main() {
    local continuous=false
    local interval=60
    local logs_only=false
    local health_only=false
    local metrics_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -c|--continuous)
                continuous=true
                shift
                ;;
            -i|--interval)
                interval="$2"
                shift 2
                ;;
            -e|--email)
                ALERT_EMAIL="$2"
                shift 2
                ;;
            -t|--threshold)
                ALERT_THRESHOLD="$2"
                shift 2
                ;;
            -l|--logs)
                logs_only=true
                shift
                ;;
            --health-only)
                health_only=true
                shift
                ;;
            --metrics-only)
                metrics_only=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Create log file if it doesn't exist
    touch "$LOG_FILE"
    
    # Run appropriate monitoring mode
    if [[ "$logs_only" == "true" ]]; then
        check_logs
    elif [[ "$health_only" == "true" ]]; then
        check_service_health
        if [[ $? -eq 0 ]]; then
            print_status "Service is healthy"
        else
            print_error "Service is unhealthy"
        fi
    elif [[ "$metrics_only" == "true" ]]; then
        check_api_metrics
    elif [[ "$continuous" == "true" ]]; then
        monitor_continuous "$interval"
    else
        run_single_check
    fi
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi