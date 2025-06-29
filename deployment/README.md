# Phase 8: Local Deployment Guide

## 🚀 Production Deployment Documentation

This guide covers the complete production deployment of the RAG-A2A-MCP system using Docker, service management, and monitoring.

---

## 📋 Prerequisites

### System Requirements
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **OpenSSL** (for SSL certificate generation)
- **curl** (for health checks)
- **4GB RAM** minimum, **8GB RAM** recommended
- **2 CPU cores** minimum

### Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd rag-agent-project

# Install Python dependencies
pip install -r deployment/requirements.txt
```

---

## 🐳 Docker Deployment

### Quick Start
```bash
# Navigate to project directory
cd rag-agent-project

# Initial setup (Windows)
deployment\deploy.bat setup

# Initial setup (Linux/Mac)
chmod +x deployment/deploy.sh
./deployment/deploy.sh setup

# Start full stack
deployment\deploy.bat start-full    # Windows
./deployment/deploy.sh start-full   # Linux/Mac
```

### Manual Docker Commands
```bash
# Build images
docker-compose -f deployment/docker-compose.yml build

# Start core services
docker-compose -f deployment/docker-compose.yml up -d

# Start with monitoring
docker-compose -f deployment/docker-compose.yml --profile monitoring up -d

# Start with NGINX proxy
docker-compose -f deployment/docker-compose.yml --profile proxy up -d

# Start everything
docker-compose -f deployment/docker-compose.yml --profile monitoring --profile proxy up -d
```

---

## 🎛️ Service Management

### Using Python Service Manager
```bash
# Start all services
python deployment/service_manager.py start

# Stop all services
python deployment/service_manager.py stop

# Check status
python deployment/service_manager.py status

# Health check
python deployment/service_manager.py health

# Start specific service
python deployment/service_manager.py start mcp_server

# Restart service
python deployment/service_manager.py restart main_agent
```

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │   Main Agent    │    │   HR Agent      │
│   Port: 8000    │◄───┤   Port: 8001    │◄───┤   Port: 8002    │
│   Database      │    │   Orchestrator  │    │   HR Specialist │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │ Greeting Agent  │
                       │   Port: 8003    │
                       │ Social Queries  │
                       └─────────────────┘
```

---

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Generate self-signed certificates (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout deployment/ssl/server.key \
    -out deployment/ssl/server.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Environment Variables
```bash
# deployment/.env
A2A_SECRET_KEY=your_secure_secret_key_here
MCP_SERVER_PORT=8000
MAIN_AGENT_PORT=8001
HR_AGENT_PORT=8002
GREETING_AGENT_PORT=8003
```

### Production Security Checklist
- [ ] Change default A2A_SECRET_KEY
- [ ] Use proper SSL certificates
- [ ] Configure firewall rules
- [ ] Enable container security scanning
- [ ] Set up log aggregation
- [ ] Configure backup strategy

---

## 📊 Monitoring & Observability

### Prometheus Metrics
Access metrics at:
- **Prometheus UI**: http://localhost:9090
- **Service Metrics**: http://localhost:8000/metrics

### Grafana Dashboards
- **URL**: http://localhost:3000
- **Default Login**: admin/admin
- **Dashboards**: Pre-configured for agent performance

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Main Agent
curl http://localhost:8002/health  # HR Agent
curl http://localhost:8003/health  # Greeting Agent

# Or use deployment script
deployment/deploy.sh health
```

### Log Management
```bash
# View all logs
docker-compose -f deployment/docker-compose.yml logs -f

# View specific service logs
docker-compose -f deployment/docker-compose.yml logs -f mcp-server

# Using deployment script
deployment/deploy.sh logs main-agent
```

---

## 🔧 Production Configuration

### Uvicorn Production Settings
```python
# deployment/production_mcp_server.py
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,          # Scale based on CPU cores
    log_level="info",
    reload=False,       # Disabled in production
    access_log=True,
    server_header=False # Security hardening
)
```

### Docker Resource Limits
```yaml
# deployment/docker-compose.yml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 🚦 Load Balancing (NGINX)

### NGINX Configuration
```nginx
# deployment/nginx.conf
upstream mcp_backend {
    server mcp-server:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    
    location /mcp/ {
        proxy_pass http://mcp_backend/;
        proxy_set_header Host $host;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

### Access URLs
- **Direct Access**: http://localhost:8001
- **Through Proxy**: https://localhost/agent/main/
- **Load Balanced**: https://rag-a2a-mcp.local

---

## 🎯 Testing Production Deployment

### End-to-End Test
```bash
# Test MCP Server
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_all_employees"}}'

# Test Main Agent
curl -X POST http://localhost:8001/task \
  -H "Content-Type: application/json" \
  -d '{"query": "How many employees do we have?"}'

# Test A2A Communication
python test_phase7_coordination.py
```

### Performance Testing
```bash
# Install testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8001
```

---

## 🔄 Backup & Recovery

### Database Backup
```bash
# Backup SQLite database
docker cp rag-mcp-server:/app/data/employees.db ./backup/employees_$(date +%Y%m%d).db

# Restore database
docker cp ./backup/employees_20241225.db rag-mcp-server:/app/data/employees.db
```

### Configuration Backup
```bash
# Backup deployment configuration
tar -czf deployment_backup_$(date +%Y%m%d).tar.gz deployment/
```

---

## 🛠️ Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check port conflicts
netstat -tulpn | grep :8000

# Check logs
docker-compose logs mcp-server
```

#### Health Check Failures
```bash
# Test connectivity
telnet localhost 8000

# Check container status
docker ps -a

# Restart unhealthy service
docker-compose restart mcp-server
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor logs for errors
docker-compose logs -f --tail=100

# Scale services
docker-compose up -d --scale mcp-server=2
```

### Debug Mode
```bash
# Start with debug logging
LOG_LEVEL=debug docker-compose up

# Open shell in container
docker-compose exec mcp-server /bin/bash

# Run debug commands
python -c "import agents.main_agent_a2a; print('Agent imported successfully')"
```

---

## 🎯 Production Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Security configurations reviewed
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Resource limits configured
- [ ] Monitoring enabled

### Post-Deployment
- [ ] Health checks passing
- [ ] Logs are clean
- [ ] Metrics are being collected
- [ ] Backup strategy implemented
- [ ] Documentation updated
- [ ] Team training completed

### Monitoring
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards configured
- [ ] Alert rules defined
- [ ] Log aggregation working
- [ ] Performance baselines established

---

## 📞 Support & Maintenance

### Daily Operations
```bash
# Morning health check
deployment/deploy.sh health

# Check logs for errors
deployment/deploy.sh logs | grep -i error

# Monitor resource usage
docker stats --no-stream
```

### Weekly Maintenance
```bash
# Update images
docker-compose pull
docker-compose up -d

# Clean up unused resources
docker system prune -f

# Backup database
deployment/backup_database.sh
```

### Emergency Procedures
```bash
# Emergency restart
deployment/deploy.sh stop
deployment/deploy.sh start

# Rollback to previous version
docker-compose down
docker-compose up -d --force-recreate

# Emergency backup
deployment/emergency_backup.sh
```

---

This completes the Phase 8 production deployment setup! 🚀
