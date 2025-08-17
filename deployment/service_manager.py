#!/usr/bin/env python3
"""
Phase 8: Local Deployment - Service Manager
Production-ready service orchestration for the RAG-A2A-MCP system
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp


class ServiceStatus(Enum):
    """Service status enumeration"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ServiceConfig:
    """Service configuration"""

    name: str
    script_path: str
    port: int
    health_endpoint: str
    environment: Dict[str, str]
    dependencies: List[str]
    auto_restart: bool = True
    start_timeout: int = 30
    stop_timeout: int = 10


class ServiceManager:
    """
    Production service manager for RAG-A2A-MCP system
    Handles service lifecycle, health monitoring, and dependency management
    """

    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.project_root = Path(__file__).parent.parent

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self._initialize_services()

    def _initialize_services(self):
        """Initialize service configurations"""

        # MCP Server - Core data service
        self.services["mcp_server"] = ServiceConfig(
            name="MCP Server",
            script_path="mcp_server/http_server.py",
            port=8000,
            health_endpoint="/health",
            environment={"MCP_SERVER_PORT": "8000", "MCP_SERVER_HOST": "localhost"},
            dependencies=[],
        )

        # Main Agent - Primary coordination agent
        self.services["main_agent"] = ServiceConfig(
            name="Main Agent A2A",
            script_path="agents/main_agent_a2a.py",
            port=8001,
            health_endpoint="/health",
            environment={
                "MAIN_AGENT_PORT": "8001",
                "MAIN_AGENT_HOST": "localhost",
                "MCP_SERVER_PORT": "8000",
                "A2A_SECRET_KEY": "rag_a2a_mcp_secret",
            },
            dependencies=["mcp_server"],
        )

        # HR Agent - Human resources specialist
        self.services["hr_agent"] = ServiceConfig(
            name="HR Agent A2A",
            script_path="agents/hr_agent_a2a.py",
            port=8002,
            health_endpoint="/health",
            environment={
                "HR_AGENT_PORT": "8002",
                "HR_AGENT_HOST": "localhost",
                "MCP_SERVER_PORT": "8000",
                "A2A_SECRET_KEY": "rag_a2a_mcp_secret",
            },
            dependencies=["mcp_server"],
        )

        # Greeting Agent - Social interaction specialist
        self.services["greeting_agent"] = ServiceConfig(
            name="Greeting Agent A2A",
            script_path="agents/greeting_agent_a2a.py",
            port=8003,
            health_endpoint="/health",
            environment={
                "GREETING_AGENT_PORT": "8003",
                "GREETING_AGENT_HOST": "localhost",
                "A2A_SECRET_KEY": "rag_a2a_mcp_secret",
            },
            dependencies=[],
        )

        # Initialize all services as stopped
        for service_name in self.services:
            self.service_status[service_name] = ServiceStatus.STOPPED

    async def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        if service_name not in self.services:
            print(f"ERROR: Unknown service: {service_name}")
            return False

        service = self.services[service_name]

        # Check dependencies
        for dep in service.dependencies:
            if self.service_status.get(dep) != ServiceStatus.RUNNING:
                print(f"WARNING: Dependency '{dep}' not running for '{service_name}'")
                # Auto-start dependency
                if not await self.start_service(dep):
                    return False

        print(f"Starting {service.name}...")
        self.service_status[service_name] = ServiceStatus.STARTING

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(service.environment)

            # Start process
            script_path = self.project_root / service.script_path
            cmd = [sys.executable, str(script_path)]

            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.processes[service_name] = process

            # Wait for service to be ready
            if await self._wait_for_health(service_name, service.start_timeout):
                self.service_status[service_name] = ServiceStatus.RUNNING
                print(f"SUCCESS: {service.name} started successfully on port {service.port}")
                return True
            else:
                self.service_status[service_name] = ServiceStatus.FAILED
                print(f"ERROR: {service.name} failed to start (health check failed)")
                await self.stop_service(service_name)
                return False

        except Exception as e:
            self.service_status[service_name] = ServiceStatus.FAILED
            print(f"ERROR: Failed to start {service.name}: {str(e)}")
            return False

    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        if service_name not in self.services:
            print(f"ERROR: Unknown service: {service_name}")
            return False

        service = self.services[service_name]

        if service_name not in self.processes:
            self.service_status[service_name] = ServiceStatus.STOPPED
            return True

        print(f"Stopping {service.name}...")
        self.service_status[service_name] = ServiceStatus.STOPPING

        try:
            process = self.processes[service_name]

            # Graceful shutdown
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=service.stop_timeout)
            except subprocess.TimeoutExpired:
                print(f"WARNING: Force killing {service.name}")
                process.kill()
                process.wait()

            del self.processes[service_name]
            self.service_status[service_name] = ServiceStatus.STOPPED
            print(f"SUCCESS: {service.name} stopped")
            return True

        except Exception as e:
            print(f"ERROR: Error stopping {service.name}: {str(e)}")
            self.service_status[service_name] = ServiceStatus.FAILED
            return False

    async def start_all(self) -> bool:
        """Start all services in dependency order"""
        print("Starting RAG-A2A-MCP System")
        print("=" * 40)

        # Determine start order based on dependencies
        start_order = self._get_start_order()

        for service_name in start_order:
            if not await self.start_service(service_name):
                print(f"ERROR: Failed to start {service_name}, aborting startup")
                return False
            await asyncio.sleep(2)  # Brief pause between services

        print("\nSUCCESS: All services started successfully!")
        await self.status()
        return True

    async def stop_all(self) -> bool:
        """Stop all services"""
        print("\nStopping RAG-A2A-MCP System")
        print("=" * 40)

        # Stop in reverse dependency order
        start_order = self._get_start_order()
        stop_order = list(reversed(start_order))

        success = True
        for service_name in stop_order:
            if not await self.stop_service(service_name):
                success = False

        print("\nSUCCESS: All services stopped")
        return success

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        print(f"Restarting {self.services[service_name].name}...")
        await self.stop_service(service_name)
        await asyncio.sleep(2)
        return await self.start_service(service_name)

    async def restart_all(self) -> bool:
        """Restart all services"""
        await self.stop_all()
        await asyncio.sleep(3)
        return await self.start_all()

    async def status(self):
        """Display status of all services"""
        print("\nService Status")
        print("=" * 60)

        for service_name, service in self.services.items():
            status = self.service_status[service_name]
            status_icon = {
                ServiceStatus.RUNNING: "[RUNNING]",
                ServiceStatus.STOPPED: "[STOPPED]",
                ServiceStatus.STARTING: "[STARTING]",
                ServiceStatus.STOPPING: "[STOPPING]",
                ServiceStatus.FAILED: "[FAILED]",
                ServiceStatus.UNKNOWN: "[UNKNOWN]",
            }.get(status, "[UNKNOWN]")

            health_status = ""
            if status == ServiceStatus.RUNNING:
                is_healthy = await self._check_health(service_name)
                health_status = " (Healthy)" if is_healthy else " (Unhealthy)"

            print(
                f"{status_icon} {service.name:<20} {status.value:<10} Port {service.port}{health_status}"
            )

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all running services"""
        health_results = {}

        for service_name in self.services:
            if self.service_status[service_name] == ServiceStatus.RUNNING:
                health_results[service_name] = await self._check_health(service_name)
            else:
                health_results[service_name] = False

        return health_results

    async def _check_health(self, service_name: str) -> bool:
        """Check health of a specific service"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{service.port}{service.health_endpoint}",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status == 200
        except:
            return False

    async def _wait_for_health(self, service_name: str, timeout: int) -> bool:
        """Wait for service to become healthy"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await self._check_health(service_name):
                return True
            await asyncio.sleep(1)

        return False

    def _get_start_order(self) -> List[str]:
        """Get service start order based on dependencies"""
        ordered = []
        visited = set()

        def visit(service_name):
            if service_name in visited:
                return
            visited.add(service_name)

            if service_name in self.services:
                for dep in self.services[service_name].dependencies:
                    visit(dep)
                ordered.append(service_name)

        for service_name in self.services:
            visit(service_name)

        return ordered

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        asyncio.create_task(self.stop_all())


async def main():
    """Main service management interface"""
    manager = ServiceManager()

    if len(sys.argv) < 2:
        print("RAG-A2A-MCP Service Manager")
        print("=" * 40)
        print("Usage:")
        print("  python deployment/service_manager.py start")
        print("  python deployment/service_manager.py stop")
        print("  python deployment/service_manager.py restart")
        print("  python deployment/service_manager.py status")
        print("  python deployment/service_manager.py health")
        print("  python deployment/service_manager.py start <service_name>")
        print("  python deployment/service_manager.py stop <service_name>")
        print("  python deployment/service_manager.py restart <service_name>")
        return

    command = sys.argv[1].lower()
    service_name = sys.argv[2] if len(sys.argv) > 2 else None

    if command == "start":
        if service_name:
            await manager.start_service(service_name)
        else:
            await manager.start_all()
    elif command == "stop":
        if service_name:
            await manager.stop_service(service_name)
        else:
            await manager.stop_all()
    elif command == "restart":
        if service_name:
            await manager.restart_service(service_name)
        else:
            await manager.restart_all()
    elif command == "status":
        await manager.status()
    elif command == "health":
        health = await manager.health_check()
        print("\nHealth Check Results")
        print("=" * 30)
        for service_name, is_healthy in health.items():
            status = "HEALTHY" if is_healthy else "UNHEALTHY"
            print(f"{service_name}: {status}")
    else:
        print(f"ERROR: Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
