# Phase 8: Local Deployment - Docker Configuration
# Multi-stage build for optimized containers

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# ===== MCP Server Container =====
FROM base as mcp-server

# Copy MCP server code
COPY mcp_server/ ./mcp_server/
COPY data/ ./data/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run MCP server
CMD ["python", "mcp_server/http_server.py"]

# ===== Main Agent Container =====
FROM base as main-agent

# Copy agent code
COPY agents/ ./agents/
COPY coordination/ ./coordination/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run Main Agent
CMD ["python", "agents/main_agent_a2a.py"]

# ===== HR Agent Container =====
FROM base as hr-agent

# Copy agent code
COPY agents/ ./agents/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run HR Agent
CMD ["python", "agents/hr_agent_a2a.py"]

# ===== Greeting Agent Container =====
FROM base as greeting-agent

# Copy agent code
COPY agents/ ./agents/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run Greeting Agent
CMD ["python", "agents/greeting_agent_a2a.py"]
