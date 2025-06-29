#!/bin/bash
# Phase 8: Local Deployment Scripts
# Production deployment automation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="rag-a2a-mcp"
COMPOSE_FILE="deployment/docker-compose.yml"
ENV_FILE="deployment/.env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

create_ssl_certificates() {
    log_info "Creating SSL certificates..."
    
    SSL_DIR="deployment/ssl"
    mkdir -p "$SSL_DIR"
    
    if [ ! -f "$SSL_DIR/server.key" ] || [ ! -f "$SSL_DIR/server.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/server.key" \
            -out "$SSL_DIR/server.crt" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
            2>/dev/null || {
                log_warning "OpenSSL not available, skipping SSL certificate generation"
                return 0
            }
        log_success "SSL certificates created"
    else
        log_info "SSL certificates already exist"
    fi
}

create_env_file() {
    log_info "Creating environment file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# RAG-A2A-MCP Environment Configuration
# Generated on $(date)

# Service Configuration
MCP_SERVER_PORT=8000
MAIN_AGENT_PORT=8001
HR_AGENT_PORT=8002
GREETING_AGENT_PORT=8003

# Security
A2A_SECRET_KEY=rag_a2a_mcp_secret_$(openssl rand -hex 16 2>/dev/null || echo "fallback_secret")

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Logging
LOG_LEVEL=INFO

# OpenAI Configuration (Optional)
# OPENAI_API_KEY=your_openai_api_key_here

# Google AI Configuration (Optional) 
# GOOGLE_API_KEY=your_google_api_key_here
EOF
        log_success "Environment file created at $ENV_FILE"
    else
        log_info "Environment file already exists"
    fi
}

build_images() {
    log_info "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build --parallel
    log_success "Docker images built successfully"
}

start_services() {
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    log_success "Services started"
}

stop_services() {
    log_info "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" down
    log_success "Services stopped"
}

start_with_monitoring() {
    log_info "Starting services with monitoring..."
    docker-compose -f "$COMPOSE_FILE" --profile monitoring up -d
    log_success "Services with monitoring started"
}

start_with_proxy() {
    log_info "Starting services with NGINX proxy..."
    docker-compose -f "$COMPOSE_FILE" --profile proxy up -d
    log_success "Services with proxy started"
}

start_full_stack() {
    log_info "Starting full stack (all services + monitoring + proxy)..."
    docker-compose -f "$COMPOSE_FILE" --profile monitoring --profile proxy up -d
    log_success "Full stack started"
}

show_status() {
    log_info "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log_info "Service logs (last 10 lines):"
    docker-compose -f "$COMPOSE_FILE" logs --tail=10
}

show_health() {
    log_info "Health check status:"
    
    services=("mcp-server:8000" "main-agent:8001" "hr-agent:8002" "greeting-agent:8003")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -f -s "http://localhost:$port/health" >/dev/null 2>&1; then
            log_success "$name (port $port) - Healthy"
        else
            log_error "$name (port $port) - Unhealthy"
        fi
    done
}

cleanup() {
    log_info "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    docker system prune -f
    log_success "Cleanup completed"
}

show_logs() {
    service_name=${1:-""}
    if [ -n "$service_name" ]; then
        log_info "Showing logs for $service_name:"
        docker-compose -f "$COMPOSE_FILE" logs -f "$service_name"
    else
        log_info "Showing logs for all services:"
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

show_usage() {
    echo "🐳 RAG-A2A-MCP Docker Deployment Manager"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup          - Initial setup (dependencies, SSL, env)"
    echo "  build          - Build Docker images"
    echo "  start          - Start core services"
    echo "  start-monitor  - Start services with monitoring"
    echo "  start-proxy    - Start services with NGINX proxy"
    echo "  start-full     - Start full stack (all components)"
    echo "  stop           - Stop all services"
    echo "  restart        - Restart all services"
    echo "  status         - Show service status"
    echo "  health         - Check service health"
    echo "  logs [service] - Show logs (optionally for specific service)"
    echo "  cleanup        - Stop services and clean up"
    echo "  shell [service]- Open shell in service container"
    echo ""
    echo "Examples:"
    echo "  $0 setup         # Initial setup"
    echo "  $0 start-full    # Start everything"
    echo "  $0 logs main-agent  # Show main-agent logs"
    echo "  $0 shell mcp-server # Open shell in MCP server"
}

# Main execution
case "${1:-help}" in
    setup)
        check_dependencies
        create_ssl_certificates
        create_env_file
        log_success "Setup completed successfully!"
        ;;
    build)
        check_dependencies
        build_images
        ;;
    start)
        check_dependencies
        start_services
        echo ""
        show_health
        ;;
    start-monitor)
        check_dependencies
        start_with_monitoring
        echo ""
        show_health
        ;;
    start-proxy)
        check_dependencies
        start_with_proxy
        echo ""
        show_health
        ;;
    start-full)
        check_dependencies
        start_full_stack
        echo ""
        show_health
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    health)
        show_health
        ;;
    logs)
        show_logs "$2"
        ;;
    cleanup)
        cleanup
        ;;
    shell)
        service_name=${2:-"mcp-server"}
        log_info "Opening shell in $service_name container..."
        docker-compose -f "$COMPOSE_FILE" exec "$service_name" /bin/bash
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
