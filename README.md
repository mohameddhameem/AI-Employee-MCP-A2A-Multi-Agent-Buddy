# RAG-A2A-MCP: Multi-Agent Retrieval-Augmented Generation System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)

A production-ready multi-agent system demonstrating modern AI agent architecture using **Retrieval-Augmented Generation (RAG)**, **Model Context Protocol (MCP)**, **Agent-to-Agent (A2A) Protocol**, and **Google's Agent Development Kit (ADK)**.

## 🎯 Overview

This project implements a complete multi-agent ecosystem where AI agents collaborate to process natural language queries, retrieve data from databases, and coordinate complex workflows using industry-standard protocols.

### ✨ Key Features

- 🤖 **Multi-Agent Architecture** - Specialized agents for different domains (HR, Greetings, Data)
- 🔗 **A2A Protocol** - Secure agent-to-agent communication with HMAC-SHA256 authentication
- 📊 **MCP Integration** - Database access via Model Context Protocol
- 🐳 **Production Deployment** - Docker containers with load balancing and monitoring
- 🔄 **Workflow Orchestration** - 7 coordination patterns (Sequential, Parallel, Pipeline, etc.)
- 📈 **Monitoring & Observability** - Prometheus metrics and Grafana dashboards
- 🔒 **Enterprise Security** - SSL/TLS, rate limiting, and container isolation

---

## 🏗️ Architecture

```
                    🌐 NGINX Load Balancer (Port 80/443)
                            │ SSL Termination & Rate Limiting
                            ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                 🐳 Docker Container Network                  │
    │                                                             │
    │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
    │  │ Main Agent  │◄──┤ HR Agent    │◄──┤ Greeting    │      │
    │  │ Port: 8001  │   │ Port: 8002  │   │ Agent       │      │
    │  │ A2A Protocol│   │ MCP Tools   │   │ Port: 8003  │      │
    │  └─────────────┘   └─────────────┘   └─────────────┘      │
    │         ▲                   ▲                             │
    │         │ A2A Communication │                             │
    │         ▼                   ▼                             │
    │  ┌─────────────────────────────────────────────────────┐  │
    │  │              MCP Server (Port: 8000)               │  │
    │  │  • Employee Database Tools                         │  │
    │  │  • 20 employees across 4 departments               │  │
    │  │  • SQLite with query optimization                  │  │
    │  └─────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
                            │
    ┌─────────────────────────────────────────────────────────────┐
    │                 📊 Monitoring Stack                         │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
    │  │ Prometheus   │  │ Grafana      │  │ Log          │     │
    │  │ Metrics      │  │ Dashboards   │  │ Aggregation  │     │
    │  │ Port: 9090   │  │ Port: 3000   │  │ ELK Stack    │     │
    │  └──────────────┘  └──────────────┘  └──────────────┘     │
    └─────────────────────────────────────────────────────────────┘
```

### 🔄 Data Flow

```
User Query ──→ Load Balancer ──→ Main Agent ──→ A2A Protocol ──→ Specialist Agent ──→ MCP Server ──→ Database
     ↑                ↓              ↓              ↓                    ↓              ↓            ↓
Natural Language  SSL Security  Query Analysis  Agent Selection    Tool Execution   MCP Tools   Data Retrieval
Response         Rate Limiting   Coordination   Authentication     Result Processing              (20 employees)
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **4GB RAM** minimum, **8GB RAM** recommended
- **2 CPU cores** minimum

### 1. Clone and Setup

```bash
git clone <repository-url>
cd rag-agent-project

# Windows setup
deployment\deploy.bat setup

# Linux/Mac setup
chmod +x deployment/deploy.sh
./deployment/deploy.sh setup
```

### 2. Start the System

```bash
# Start full production stack
deployment\deploy.bat start-full    # Windows
./deployment/deploy.sh start-full   # Linux/Mac

# Or start core services only
deployment\deploy.bat start         # Windows
./deployment/deploy.sh start        # Linux/Mac
```

### 3. Verify Installation

```bash
# Check service health
python deployment/service_manager.py health

# Run comprehensive tests
python test_production_deployment.py
```

### 4. Access the System

- **Main Agent API**: http://localhost:8001
- **HR Agent API**: http://localhost:8002
- **Greeting Agent API**: http://localhost:8003
- **MCP Server**: http://localhost:8000
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)

---

## 💡 Usage Examples

### Basic Agent Interaction

```bash
# Query the main agent
curl -X POST http://localhost:8001/task \
  -H "Content-Type: application/json" \
  -d '{"input": "How many employees do we have?"}'

# Query HR agent directly
curl -X POST http://localhost:8002/task \
  -H "Content-Type: application/json" \
  -d '{"input": "Get all employees in Engineering department"}'

# Query greeting agent
curl -X POST http://localhost:8003/task \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, how are you today?"}'
```

### MCP Server Tools

```bash
# Get all employees
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_all_employees"
    }
  }'

# Get employees by department
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_employees_by_department",
      "arguments": {"department": "Engineering"}
    }
  }'

# Search employees
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search_employees",
      "arguments": {"query": "engineer"}
    }
  }'
```

### Multi-Agent Coordination

```python
# Python example using the coordination system
import asyncio
from coordination.orchestrator import MultiAgentOrchestrator

async def example_coordination():
    orchestrator = MultiAgentOrchestrator()
    
    # Sequential workflow
    tasks = [
        {"agent": "greeting_agent", "input": "Hello!"},
        {"agent": "hr_agent", "input": "Get Engineering employees"},
        {"agent": "main_agent", "input": "Summarize the results"}
    ]
    
    result = await orchestrator.coordinate_sequential(tasks)
    print(f"Sequential result: {result}")

asyncio.run(example_coordination())
```

---

## 🛠️ Service Management

### Using Service Manager

```bash
# Start all services
python deployment/service_manager.py start

# Stop all services
python deployment/service_manager.py stop

# Restart services
python deployment/service_manager.py restart

# Check status
python deployment/service_manager.py status

# Health check
python deployment/service_manager.py health

# Start specific service
python deployment/service_manager.py start mcp_server

# View logs
python deployment/service_manager.py logs main_agent
```

### Using Docker Commands

```bash
# View running containers
docker-compose -f deployment/docker-compose.yml ps

# View logs
docker-compose -f deployment/docker-compose.yml logs -f

# Scale services
docker-compose -f deployment/docker-compose.yml up -d --scale hr-agent=2

# Stop services
docker-compose -f deployment/docker-compose.yml down

# Cleanup
docker-compose -f deployment/docker-compose.yml down -v --remove-orphans
```

---

## 🔧 Configuration

### Environment Variables

Create `deployment/.env`:

```bash
# Service Configuration
MCP_SERVER_PORT=8000
MAIN_AGENT_PORT=8001
HR_AGENT_PORT=8002
GREETING_AGENT_PORT=8003

# Security
A2A_SECRET_KEY=your_secure_secret_key_here

# AI APIs (Optional)
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOG_LEVEL=INFO
```

### SSL Configuration

```bash
# Generate self-signed certificates (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout deployment/ssl/server.key \
    -out deployment/ssl/server.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Agent Specializations

The system includes specialized agents:

- **Main Agent** (Port 8001): Query coordination and delegation
- **HR Agent** (Port 8002): Employee data and HR operations
- **Greeting Agent** (Port 8003): Social interactions and greetings
- **MCP Server** (Port 8000): Database tools and data access

---

## 📊 Monitoring & Observability

### Prometheus Metrics

Access at http://localhost:9090

Key metrics collected:
- Request counts and response times
- Agent performance metrics
- A2A communication statistics
- System resource usage
- Error rates and availability

### Grafana Dashboards

Access at http://localhost:3000 (admin/admin)

Pre-configured dashboards for:
- Agent Performance Overview
- A2A Communication Metrics
- MCP Server Statistics
- System Health Monitoring
- Response Time Analysis

### Health Checks

```bash
# Individual service health
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Main Agent
curl http://localhost:8002/health  # HR Agent
curl http://localhost:8003/health  # Greeting Agent

# Comprehensive health check
python deployment/service_manager.py health
```

### Log Management

```bash
# View all service logs
docker-compose -f deployment/docker-compose.yml logs -f

# View specific service logs
docker-compose -f deployment/docker-compose.yml logs -f mcp-server

# Follow logs with filtering
docker-compose logs -f | grep ERROR
```

---

## 🧪 Testing

### Production Test Suite

```bash
# Run comprehensive tests
python test_production_deployment.py

# Test specific coordination patterns
python test_phase7_coordination.py

# Test A2A protocol
python test_a2a_protocol.py
```

### Manual Testing

```bash
# Test MCP server
python -c "
import requests
response = requests.post('http://localhost:8000/mcp', 
    json={'method': 'tools/call', 'params': {'name': 'get_all_employees'}})
print(response.json())
"

# Test agent communication
python -c "
import requests
response = requests.post('http://localhost:8001/task',
    json={'input': 'How many employees do we have?'})
print(response.json())
"
```

### Load Testing

```bash
# Install testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8001
```

---

## 🔒 Security

### Authentication

- **A2A Protocol**: HMAC-SHA256 message authentication
- **API Keys**: Support for OpenAI and Google AI APIs
- **Container Isolation**: Each service runs in isolated containers
- **Network Security**: Internal Docker network with controlled access

### SSL/TLS

- **NGINX SSL Termination**: HTTPS for external access
- **Certificate Management**: Automated certificate generation
- **Security Headers**: HSTS, XSS protection, and content type validation

### Rate Limiting

```nginx
# NGINX configuration
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

### Security Best Practices

- Change default `A2A_SECRET_KEY`
- Use proper SSL certificates in production
- Configure firewall rules
- Enable container security scanning
- Set up log aggregation and monitoring
- Implement backup and recovery procedures

---

## 🏢 Production Deployment

### Scaling

```yaml
# docker-compose.yml scaling
services:
  hr-agent:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

### High Availability

- **Load Balancing**: NGINX with multiple backend instances
- **Health Checks**: Automated failure detection and recovery
- **Auto Restart**: Container restart policies
- **Graceful Shutdown**: Proper signal handling

### Backup & Recovery

```bash
# Database backup
docker cp rag-mcp-server:/app/data/employees.db ./backup/

# Configuration backup
tar -czf deployment_backup.tar.gz deployment/

# Restore from backup
docker cp ./backup/employees.db rag-mcp-server:/app/data/
```

---

## 🛠️ Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp deployment/.env.example deployment/.env

# Run services locally
python mcp_server/http_server.py &
python agents/main_agent_a2a.py &
python agents/hr_agent_a2a.py &
python agents/greeting_agent_a2a.py &
```

### Adding New Agents

1. **Create Agent File**:
```python
# agents/new_agent.py
from agents.base_agent import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="NewAgent",
            port=8004,
            specialization="new_domain"
        )
    
    def process_query(self, query: str) -> str:
        # Implement agent logic
        return "Response from new agent"
```

2. **Update Service Manager**:
```python
# deployment/service_manager.py
self.services["new_agent"] = ServiceConfig(
    name="New Agent",
    script_path="agents/new_agent.py",
    port=8004,
    health_endpoint="/health",
    environment={"NEW_AGENT_PORT": "8004"},
    dependencies=[]
)
```

3. **Update Docker Configuration**:
```yaml
# deployment/docker-compose.yml
new-agent:
  build:
    context: ..
    dockerfile: deployment/Dockerfile
    target: new-agent
  ports:
    - "8004:8004"
```

### Adding New MCP Tools

```python
# mcp_server/http_server.py
@server.tool()
def new_tool(parameter: str) -> str:
    """New tool description"""
    # Implement tool logic
    return "Tool result"
```

---

## 📚 Technical Reference

### A2A Protocol Implementation

The system implements the Agent-to-Agent protocol with:

- **Agent Cards**: JSON descriptors with capabilities and endpoints
- **Message Authentication**: HMAC-SHA256 with shared secrets
- **Task Delegation**: Secure inter-agent communication
- **Error Handling**: Retry logic and failure recovery

### MCP Protocol Integration

Model Context Protocol features:

- **Tool Execution**: Database query tools
- **Resource Access**: Employee data resources
- **HTTP Transport**: RESTful API interface
- **Error Handling**: Proper status codes and error messages

### Coordination Patterns

Seven implemented patterns:

1. **Sequential**: Tasks executed in order
2. **Parallel**: Concurrent task execution
3. **Pipeline**: Output chaining between tasks
4. **Consensus**: Agreement-based decision making
5. **Hierarchical**: Tree-based task distribution
6. **Competitive**: Best response selection
7. **Collaborative**: Shared resource coordination

---

## 📦 Project Structure

```
rag-agent-project/
├── agents/                     # Agent implementations
│   ├── main_agent_a2a.py      # Main coordination agent
│   ├── hr_agent_a2a.py        # HR specialist agent
│   ├── greeting_agent_a2a.py  # Greeting specialist agent
│   └── base_agent.py          # Base agent class
├── coordination/               # Multi-agent coordination
│   ├── orchestrator.py        # Workflow orchestrator
│   ├── patterns.py            # Coordination patterns
│   └── task_manager.py        # Task management
├── data/                       # Database and utilities
│   ├── employees.db           # SQLite database
│   └── database_utils.py      # Database utilities
├── deployment/                 # Production deployment
│   ├── docker-compose.yml     # Container orchestration
│   ├── Dockerfile             # Multi-stage container build
│   ├── nginx.conf             # Load balancer configuration
│   ├── service_manager.py     # Service lifecycle management
│   ├── deploy.sh              # Linux deployment script
│   ├── deploy.bat             # Windows deployment script
│   └── requirements.txt       # Production dependencies
├── mcp_server/                 # MCP server implementation
│   ├── http_server.py         # HTTP-based MCP server
│   └── tools.py               # MCP tool definitions
├── tests/                      # Test suites
│   ├── test_production_deployment.py
│   ├── test_phase7_coordination.py
│   └── test_a2a_protocol.py
├── cli/                        # Command-line interface
│   └── main.py                # Interactive CLI
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :8000

# Kill processes using ports
lsof -ti:8000 | xargs kill -9
```

#### Container Issues
```bash
# Check container status
docker ps -a

# View container logs
docker logs rag-mcp-server

# Restart containers
docker-compose restart
```

#### Health Check Failures
```bash
# Test connectivity
telnet localhost 8000

# Check service logs
python deployment/service_manager.py logs mcp_server

# Manual health check
curl -v http://localhost:8000/health
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check system load
top -p $(pgrep -f python)

# Scale services
docker-compose up -d --scale hr-agent=2
```

### Debug Mode

```bash
# Start with debug logging
LOG_LEVEL=debug python deployment/service_manager.py start

# Enable verbose Docker output
docker-compose -f deployment/docker-compose.yml up --verbose

# Interactive container debugging
docker-compose exec mcp-server /bin/bash
```

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run test suite: `python test_production_deployment.py`
5. Commit changes: `git commit -m "Add new feature"`
6. Push to branch: `git push origin feature/new-feature`
7. Create a Pull Request

### Code Style

```bash
# Format code
black . --line-length 100

# Sort imports
isort . --profile black

# Type checking
mypy agents/ mcp_server/ coordination/
```

### Testing Requirements

- All new features must include tests
- Maintain >90% test coverage
- Performance tests for critical paths
- Integration tests for A2A communication

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Anthropic** for the Model Context Protocol
- **Google** for the Agent Development Kit and A2A Protocol
- **OpenAI** for GPT integration capabilities
- **FastAPI** for the web framework
- **Docker** for containerization platform

---

## 📞 Support

For support and questions:

- **Issues**: GitHub Issues tab
- **Discussions**: GitHub Discussions
- **Documentation**: See `deployment/README.md` for detailed deployment guide
- **Examples**: Check `tests/` directory for usage examples

---

## 🗺️ Roadmap

### Upcoming Features

- [ ] **Vector Database Integration** - ChromaDB for semantic search
- [ ] **LLM Model Switching** - Support for local models (Ollama, LiteLLM)
- [ ] **Advanced Monitoring** - Custom metrics and alerting
- [ ] **Multi-tenancy** - Support for multiple organizations
- [ ] **API Gateway** - Advanced routing and authentication
- [ ] **Workflow Designer** - Visual workflow creation interface
- [ ] **Agent Marketplace** - Plugin system for custom agents
- [ ] **Real-time Communication** - WebSocket support for live updates

### Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Production deployment and monitoring
- **v1.2.0** - Multi-agent coordination patterns
- **v1.3.0** - A2A protocol implementation
- **v2.0.0** - Full production system (current)

---

*Built with ❤️ for the AI agent community*
