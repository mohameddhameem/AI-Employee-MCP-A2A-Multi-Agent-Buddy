# Codebase Overview

This document provides a concise, high-level walkthrough of the RAG-A2A-MCP project to help new contributors quickly understand the architecture, core modules, data flow, and how components interact in development and production.

## Purpose
A production-oriented multi-agent system demonstrating:
- Retrieval-Augmented Generation (RAG) with a simple Employee DB via an HTTP-based MCP server.
- Agent-to-Agent (A2A) protocol with message signing and discovery for inter-agent coordination.
- Multiple agent roles (Main, HR, Greeting) exposed over FastAPI.
- Production orchestration via a Service Manager and Docker stack.

## Top-Level Components
- a2a/ — Agent-to-Agent protocol (message types, signing, discovery, delegation). Note: JSON-RPC routing is served by the official A2A SDK under POST /a2a.
- agents/ — Agent HTTP servers (FastAPI) implementing roles and A2A behaviors
- coordination/ — Orchestrator supporting multiple coordination patterns
- mcp_server/ — HTTP-based MCP server exposing DB tools
- data/ — SQLite database and query utilities (EmployeeDB)
- deployment/ — Production scripts, service manager, Docker/Nginx/Prometheus configs
- cli/ — Simple CLI to interact with the Main Agent
- tests/ — Unit and integration tests for functionality and deployment flows

## Runtime Architecture
- Main Agent (port 8001) is the entrypoint for user queries.
- Specialist agents (HR on 8002, Greeting on 8003) handle domain-specific tasks.
- Agents communicate via the A2A protocol and JSON-RPC served by the official A2A SDK at POST /a2a. HMAC signing is used for A2A; JSON-RPC requests follow the SDK contract.
- MCP Server (port 8000) exposes DB tools used primarily by HR Agent for data retrieval.
- Optional: NGINX for load balancing and Prometheus/Grafana for monitoring in production.

Data Flow (simplified):
User → Main Agent → (A2A) → Specialist Agent → MCP Server → Employee DB → Specialist Agent → Main Agent → User

## Key Modules and Responsibilities

### a2a/protocol.py
- MessageType, A2AMessage: Data structures for messages.
- AgentCapability, AgentProfile: Metadata for discovery and capability queries.
- A2AProtocol:
  - Signing/verification (HMAC-SHA256 via secret key).
  - create_message, send_message: Build and POST messages to endpoints.
  - discover_agents: Broadcast discovery requests to known endpoints.
  - delegate_task, query_capabilities, health_check_agent.
  - handle_incoming_message and internal handlers for each MessageType.
  - cleanup_expired_requests, get_protocol_status.

Endpoints (SDK + A2A):
- POST /a2a — JSON-RPC 2.0 (A2A SDK)
- GET /.well-known/agent-card.json — Agent discovery card (A2A SDK)

### agents/main_agent_a2a.py
- MainAgentA2A FastAPI server (default port: 8001).
- Discovers other agents, selects appropriate agent based on simple heuristics, and delegates via A2A.
- Endpoints:
  - POST /task — primary API to submit a user query.
  - POST /a2a — JSON-RPC (SDK)
  - GET /.well-known/agent-card.json — Agent Card (SDK)
  - GET /health — health checks.
  - GET /a2a/status — protocol status.
  - GET /discover — run agent discovery and return known agents.
  - GET / — root info.
- Fallback behavior: If A2A delegation fails, can attempt direct HTTP.

### agents/hr_agent_a2a.py
- HRAgentA2A FastAPI server (default port: 8002).
- Integrates with MCP server to retrieve employee/department data via HTTP tools.
- Implements overrides for capability queries and delegation requests.
- High-level capabilities:
  - get employee lists, department overviews, analytics summaries, org hierarchy, smart search, etc.
- Endpoints similar in pattern to MainAgent:
  - POST /task, POST /a2a (SDK), GET /health, GET /capabilities, GET /.

### agents/greeting_agent_a2a.py
- GreetingAgentA2A FastAPI server (default port: 8003).
- Handles social/greeting-type user queries with several intent handlers and capability exposure.
- Endpoints align with the shared A2A/SDK pattern.

### coordination/orchestrator.py
- MultiAgentOrchestrator supports multiple coordination patterns:
  - Sequential, Parallel, Pipeline, Hierarchical, Consensus, Competitive, Collaborative
- TaskNode represents executable steps; WorkflowResult aggregates outcomes.
- Utilities for delegation, scoring, consensus formation, metrics, and summaries.
- Intended for composing multi-step workflows across agents.

### mcp_server/http_server.py
- FastAPI HTTP server exposing MCP-like tools under POST /mcp and health under GET /health.
- Backed by data/database_utils.py (EmployeeDB) with rich queries:
  - get_all_employees, get_employees_by_department, get_employee_by_id, search_employees,
    get_department_summary, get_managers_and_reports, get_employee_summary, get_active_projects.

### data/database_utils.py
- EmployeeDB wraps SQLite queries and returns results as lists/dicts.
- Exposes convenience methods used by MCP server and HR Agent.

### deployment/
- service_manager.py starts/stops/monitors services (MCP server and agents), manages health checks, and orchestrates start order based on dependencies.
- docker-compose.yml, Dockerfile, nginx.conf, prometheus.yml provide production deployment topology.
- deploy.bat / deploy.sh provide platform-specific orchestration scripts.

### cli/main.py
- Simple REPL to send user inputs to Main Agent POST /task.
- Uses ADK_AGENT_HOST/ADK_AGENT_PORT env vars (defaults to localhost:8001).

## Common Endpoints
- Main Agent (8001):
  - POST /task, POST /a2a (SDK), GET /health, GET /discover, GET /, GET /.well-known/agent-card.json
- HR Agent (8002):
  - POST /task, POST /a2a (SDK), GET /health, GET /capabilities, GET /, GET /.well-known/agent-card.json
- Greeting Agent (8003):
  - POST /task, POST /a2a (SDK), GET /health, GET /capabilities, GET /, GET /.well-known/agent-card.json
- MCP Server (8000):
  - GET /health, POST /mcp, GET /

## How To Run (Development)
1) Launch MCP server:
   python -m mcp_server.http_server  # serves on localhost:8000

2) Launch Agents (in separate terminals):
   python -m agents.main_agent_a2a    # localhost:8001
   python -m agents.hr_agent_a2a      # localhost:8002
   python -m agents.greeting_agent_a2a# localhost:8003

3) Use CLI to interact:
   python -m cli.main

## How To Run (Production)
- Use deployment/deploy.bat or deployment/deploy.sh with start-full to start the full stack via Docker Compose, including NGINX and monitoring.
- Alternatively, use deployment/service_manager.py to run services locally with health checks and explicit ordering.

## Tests
- Integration: tests/integration/test_production_deployment.py verifies health, MCP functionality, agent task handling, A2A communication, and concurrency performance.
- Additional tests cover A2A protocol and coordination patterns.

## Notes
- Several files (agents/main_agent.py, mcp_server/server.py, deployment/production_agent_server.py) are placeholders guiding you to the A2A-enabled implementations.
- Secret keys for A2A signing are expected via environment variables; see README and deployment configs.

This overview complements the detailed README by mapping source files to runtime behavior and endpoints, accelerating onboarding and maintenance.