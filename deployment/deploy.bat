@echo off
REM Phase 8: Windows Local Deployment Scripts
REM Production deployment automation for Windows

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=rag-a2a-mcp
set COMPOSE_FILE=deployment\docker-compose.yml
set ENV_FILE=deployment\.env

REM Colors (Windows doesn't support ANSI colors in basic cmd, but we'll structure for output)
set "INFO_PREFIX=[INFO]"
set "SUCCESS_PREFIX=[SUCCESS]"
set "WARNING_PREFIX=[WARNING]"
set "ERROR_PREFIX=[ERROR]"

REM Functions
:log_info
echo %INFO_PREFIX% %~1
goto :eof

:log_success
echo %SUCCESS_PREFIX% %~1
goto :eof

:log_warning
echo %WARNING_PREFIX% %~1
goto :eof

:log_error
echo %ERROR_PREFIX% %~1
goto :eof

:check_dependencies
call :log_info "Checking dependencies..."

REM Check Docker
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    call :log_error "Docker is not installed or not in PATH"
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if !errorlevel! neq 0 (
    call :log_error "Docker Compose is not installed or not in PATH"
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if !errorlevel! neq 0 (
    call :log_error "Docker daemon is not running"
    exit /b 1
)

call :log_success "All dependencies are available"
goto :eof

:create_ssl_certificates
call :log_info "Creating SSL certificates..."

set SSL_DIR=deployment\ssl
if not exist "%SSL_DIR%" mkdir "%SSL_DIR%"

if not exist "%SSL_DIR%\server.key" (
    REM Try to create SSL certificates using OpenSSL if available
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "%SSL_DIR%\server.key" -out "%SSL_DIR%\server.crt" -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" >nul 2>&1
    if !errorlevel! equ 0 (
        call :log_success "SSL certificates created"
    ) else (
        call :log_warning "OpenSSL not available, skipping SSL certificate generation"
    )
) else (
    call :log_info "SSL certificates already exist"
)
goto :eof

:create_env_file
call :log_info "Creating environment file..."

if not exist "%ENV_FILE%" (
    (
        echo # RAG-A2A-MCP Environment Configuration
        echo # Generated on %date% %time%
        echo.
        echo # Service Configuration
        echo MCP_SERVER_PORT=8000
        echo MAIN_AGENT_PORT=8001
        echo HR_AGENT_PORT=8002
        echo GREETING_AGENT_PORT=8003
        echo.
        echo # Security
        echo A2A_SECRET_KEY=rag_a2a_mcp_secret_windows
        echo.
        echo # Monitoring
        echo PROMETHEUS_PORT=9090
        echo GRAFANA_PORT=3000
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo.
        echo # OpenAI Configuration ^(Optional^)
        echo # OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # Google AI Configuration ^(Optional^)
        echo # GOOGLE_API_KEY=your_google_api_key_here
    ) > "%ENV_FILE%"
    call :log_success "Environment file created at %ENV_FILE%"
) else (
    call :log_info "Environment file already exists"
)
goto :eof

:build_images
call :log_info "Building Docker images..."
docker-compose -f "%COMPOSE_FILE%" build --parallel
if !errorlevel! equ 0 (
    call :log_success "Docker images built successfully"
) else (
    call :log_error "Failed to build Docker images"
    exit /b 1
)
goto :eof

:start_services
call :log_info "Starting services..."
docker-compose -f "%COMPOSE_FILE%" up -d
if !errorlevel! equ 0 (
    call :log_success "Services started"
) else (
    call :log_error "Failed to start services"
    exit /b 1
)
goto :eof

:stop_services
call :log_info "Stopping services..."
docker-compose -f "%COMPOSE_FILE%" down
if !errorlevel! equ 0 (
    call :log_success "Services stopped"
) else (
    call :log_error "Failed to stop services"
)
goto :eof

:start_with_monitoring
call :log_info "Starting services with monitoring..."
docker-compose -f "%COMPOSE_FILE%" --profile monitoring up -d
if !errorlevel! equ 0 (
    call :log_success "Services with monitoring started"
) else (
    call :log_error "Failed to start services with monitoring"
    exit /b 1
)
goto :eof

:start_with_proxy
call :log_info "Starting services with NGINX proxy..."
docker-compose -f "%COMPOSE_FILE%" --profile proxy up -d
if !errorlevel! equ 0 (
    call :log_success "Services with proxy started"
) else (
    call :log_error "Failed to start services with proxy"
    exit /b 1
)
goto :eof

:start_full_stack
call :log_info "Starting full stack (all services + monitoring + proxy)..."
docker-compose -f "%COMPOSE_FILE%" --profile monitoring --profile proxy up -d
if !errorlevel! equ 0 (
    call :log_success "Full stack started"
) else (
    call :log_error "Failed to start full stack"
    exit /b 1
)
goto :eof

:show_status
call :log_info "Service status:"
docker-compose -f "%COMPOSE_FILE%" ps
echo.
call :log_info "Service logs (last 10 lines):"
docker-compose -f "%COMPOSE_FILE%" logs --tail=10
goto :eof

:show_health
call :log_info "Health check status:"

set services=mcp-server:8000 main-agent:8001 hr-agent:8002 greeting-agent:8003

for %%s in (%services%) do (
    for /f "tokens=1,2 delims=:" %%a in ("%%s") do (
        curl -f -s "http://localhost:%%b/health" >nul 2>&1
        if !errorlevel! equ 0 (
            call :log_success "%%a (port %%b) - Healthy"
        ) else (
            call :log_error "%%a (port %%b) - Unhealthy"
        )
    )
)
goto :eof

:cleanup
call :log_info "Cleaning up..."
docker-compose -f "%COMPOSE_FILE%" down -v --remove-orphans
docker system prune -f
call :log_success "Cleanup completed"
goto :eof

:show_logs
set service_name=%~1
if "%service_name%"=="" (
    call :log_info "Showing logs for all services:"
    docker-compose -f "%COMPOSE_FILE%" logs -f
) else (
    call :log_info "Showing logs for %service_name%:"
    docker-compose -f "%COMPOSE_FILE%" logs -f "%service_name%"
)
goto :eof

:show_usage
echo 🐳 RAG-A2A-MCP Docker Deployment Manager (Windows)
echo ==========================================
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   setup          - Initial setup (dependencies, SSL, env)
echo   build          - Build Docker images
echo   start          - Start core services
echo   start-monitor  - Start services with monitoring
echo   start-proxy    - Start services with NGINX proxy
echo   start-full     - Start full stack (all components)
echo   stop           - Stop all services
echo   restart        - Restart all services
echo   status         - Show service status
echo   health         - Check service health
echo   logs [service] - Show logs (optionally for specific service)
echo   cleanup        - Stop services and clean up
echo   shell [service]- Open shell in service container
echo.
echo Examples:
echo   %~nx0 setup         # Initial setup
echo   %~nx0 start-full    # Start everything
echo   %~nx0 logs main-agent  # Show main-agent logs
echo   %~nx0 shell mcp-server # Open shell in MCP server
goto :eof

REM Main execution
set command=%~1
if "%command%"=="" set command=help

if "%command%"=="setup" (
    call :check_dependencies
    call :create_ssl_certificates
    call :create_env_file
    call :log_success "Setup completed successfully!"
) else if "%command%"=="build" (
    call :check_dependencies
    call :build_images
) else if "%command%"=="start" (
    call :check_dependencies
    call :start_services
    echo.
    call :show_health
) else if "%command%"=="start-monitor" (
    call :check_dependencies
    call :start_with_monitoring
    echo.
    call :show_health
) else if "%command%"=="start-proxy" (
    call :check_dependencies
    call :start_with_proxy
    echo.
    call :show_health
) else if "%command%"=="start-full" (
    call :check_dependencies
    call :start_full_stack
    echo.
    call :show_health
) else if "%command%"=="stop" (
    call :stop_services
) else if "%command%"=="restart" (
    call :stop_services
    timeout /t 2 /nobreak >nul
    call :start_services
) else if "%command%"=="status" (
    call :show_status
) else if "%command%"=="health" (
    call :show_health
) else if "%command%"=="logs" (
    call :show_logs "%~2"
) else if "%command%"=="cleanup" (
    call :cleanup
) else if "%command%"=="shell" (
    set service_name=%~2
    if "!service_name!"=="" set service_name=mcp-server
    call :log_info "Opening shell in !service_name! container..."
    docker-compose -f "%COMPOSE_FILE%" exec "!service_name!" /bin/bash
) else if "%command%"=="help" (
    call :show_usage
) else if "%command%"=="--help" (
    call :show_usage
) else if "%command%"=="-h" (
    call :show_usage
) else (
    call :log_error "Unknown command: %command%"
    echo.
    call :show_usage
    exit /b 1
)
