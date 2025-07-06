#!/usr/bin/env python3
"""
Phase 8:        print("Starting Production Deployment Tests")
        print("=" * 50)roduction Deployment Test Suite
Comprehensive testing for the deployed RAG-A2A-MCP system
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ProductionTestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration: float
    response_data: Any = None
    error_message: str = ""

class ProductionTestSuite:
    """Production deployment test suite"""
    
    def __init__(self):
        self.base_urls = {
            "mcp_server": "http://localhost:8000",
            "main_agent": "http://localhost:8001", 
            "hr_agent": "http://localhost:8002",
            "greeting_agent": "http://localhost:8003"
        }
        self.results: List[ProductionTestResult] = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🧪 Starting Production Deployment Tests")
        print("=" * 60)
        
        # Health check tests
        await self.test_health_checks()
        
        # MCP server functionality tests
        await self.test_mcp_server_functionality()
        
        # Agent functionality tests
        await self.test_agent_functionality()
        
        # A2A communication tests
        await self.test_a2a_communication()
        
        # Load and performance tests
        await self.test_performance()
        
        # Generate report
        return self.generate_report()
    
    async def test_health_checks(self):
        """Test health endpoints for all services"""
        print("\n🏥 Testing Health Checks")
        print("-" * 30)
        
        for service_name, base_url in self.base_urls.items():
            start_time = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                        duration = time.time() - start_time
                        success = response.status == 200
                        result = ProductionTestResult(
                            test_name=f"Health Check - {service_name}",
                            success=success,
                            duration=duration,
                            response_data=await response.text() if success else None
                        )
                        
                        if success:
                            print(f"SUCCESS: {service_name:<15} - {duration:.2f}s")
                        else:
                            print(f"❌ {service_name:<15} - Status {response.status}")
                            result.error_message = f"HTTP {response.status}"
                        
                        self.results.append(result)
            
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ {service_name:<15} - Connection Error")
                self.results.append(ProductionTestResult(
                    test_name=f"Health Check - {service_name}",
                    success=False,
                    duration=duration,
                    error_message=str(e)
                ))
    
    async def test_mcp_server_functionality(self):
        """Test MCP server core functionality"""
        print("\nTesting MCP Server Functionality")
        print("-" * 40)
        
        mcp_tests = [
            ("get_all_employees", {}),
            ("get_employees_by_department", {"department": "Engineering"}),
            ("get_employee_summary", {}),
            ("search_employees", {"query": "engineer"})
        ]
        
        for tool_name, params in mcp_tests:
            start_time = time.time()
            try:
                request_data = {
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": params
                    }
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_urls['mcp_server']}/mcp",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        duration = time.time() - start_time
                        success = response.status == 200
                        
                        if success:
                            response_data = await response.json()
                            print(f"SUCCESS: {tool_name:<25} - {duration:.2f}s")
                        else:
                            response_data = None
                            print(f"❌ {tool_name:<25} - Status {response.status}")
                        
                        self.results.append(ProductionTestResult(
                            test_name=f"MCP Tool - {tool_name}",
                            success=success,
                            duration=duration,
                            response_data=response_data,
                            error_message="" if success else f"HTTP {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ {tool_name:<25} - Error: {str(e)}")
                self.results.append(ProductionTestResult(
                    test_name=f"MCP Tool - {tool_name}",
                    success=False,
                    duration=duration,
                    error_message=str(e)
                ))
    
    async def test_agent_functionality(self):
        """Test individual agent functionality"""
        print("\nTesting Agent Functionality")
        print("-" * 35)
        
        agent_tests = [
            ("main_agent", "How many employees do we have?"),
            ("hr_agent", "Get all employees in Engineering department"),
            ("greeting_agent", "Hello, how are you today?"),
            ("main_agent", "What's the average salary in the company?")
        ]
        
        for agent_name, query in agent_tests:
            start_time = time.time()
            try:
                request_data = {
                    "input": query
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_urls[agent_name]}/task",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        duration = time.time() - start_time
                        success = response.status == 200
                        
                        if success:
                            response_data = await response.json()
                            print(f"SUCCESS: {agent_name:<12} - {duration:.2f}s")
                        else:
                            response_data = None
                            print(f"❌ {agent_name:<12} - Status {response.status}")
                        
                        self.results.append(ProductionTestResult(
                            test_name=f"Agent Query - {agent_name}",
                            success=success,
                            duration=duration,
                            response_data=response_data,
                            error_message="" if success else f"HTTP {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                print(f"❌ {agent_name:<12} - Error: {str(e)}")
                self.results.append(ProductionTestResult(
                    test_name=f"Agent Query - {agent_name}",
                    success=False,
                    duration=duration,
                    error_message=str(e)
                ))
    
    async def test_a2a_communication(self):
        """Test A2A protocol communication"""
        print("\nTesting A2A Communication")
        print("-" * 30)
        
        # Test main agent delegating to HR agent
        start_time = time.time()
        try:
            request_data = {
                "input": "Please get me information about all employees in the Engineering department"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['main_agent']}/task",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    duration = time.time() - start_time
                    success = response.status == 200
                    
                    if success:
                        response_data = await response.json()
                        print(f"SUCCESS: A2A Delegation - {duration:.2f}s")
                    else:
                        response_data = None
                        print(f"❌ A2A Delegation - Status {response.status}")
                    
                    self.results.append(ProductionTestResult(
                        test_name="A2A Protocol - Delegation",
                        success=success,
                        duration=duration,
                        response_data=response_data,
                        error_message="" if success else f"HTTP {response.status}"
                    ))
        
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ A2A Delegation - Error: {str(e)}")
            self.results.append(ProductionTestResult(
                test_name="A2A Protocol - Delegation",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
    
    async def test_performance(self):
        """Test system performance under load"""
        print("\nTesting Performance")
        print("-" * 25)
        
        # Concurrent requests test
        concurrent_requests = 10
        start_time = time.time()
        
        try:
            tasks = []
            for i in range(concurrent_requests):
                task = self.make_concurrent_request(i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            success_rate = (successful_requests / concurrent_requests) * 100
            
            print(f"SUCCESS: Concurrent Requests - {concurrent_requests} requests in {duration:.2f}s")
            print(f"   Success Rate: {success_rate:.1f}% ({successful_requests}/{concurrent_requests})")
            
            self.results.append(ProductionTestResult(
                test_name="Performance - Concurrent Requests",
                success=success_rate >= 80,  # Consider 80%+ success rate as passing
                duration=duration,
                response_data={
                    "total_requests": concurrent_requests,
                    "successful_requests": successful_requests,
                    "success_rate": success_rate
                }
            ))
        
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Concurrent Requests - Error: {str(e)}")
            self.results.append(ProductionTestResult(
                test_name="Performance - Concurrent Requests",
                success=False,
                duration=duration,
                error_message=str(e)
            ))
    
    async def make_concurrent_request(self, request_id: int):
        """Make a concurrent request for performance testing"""
        try:
            request_data = {
                "input": f"Test request {request_id} - How many employees do we have?"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['main_agent']}/task",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return await response.json() if response.status == 200 else None
        
        except Exception as e:
            return e
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        total_duration = sum(r.duration for r in self.results)
        
        print("\n" + "=" * 60)
        print("PRODUCTION DEPLOYMENT TEST REPORT")
        print("=" * 60)
        print(f"Tests Run: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Average Duration: {total_duration/total_tests:.2f}s per test")
        
        if failed_tests > 0:
            print(f"\nFailed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"   • {result.test_name}: {result.error_message}")
        
        print("\n" + "=" * 60)
        
        if success_rate >= 90:
            print("EXCELLENT - Production system is performing optimally!")
        elif success_rate >= 75:
            print("GOOD - Production system is performing well with minor issues")
        elif success_rate >= 50:
            print("WARNING - Production system has significant issues")
        else:
            print("CRITICAL - Production system requires immediate attention")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "average_duration": total_duration / total_tests if total_tests > 0 else 0,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "error_message": r.error_message
                }
                for r in self.results
            ]
        }

async def main():
    """Run production deployment tests"""
    print("RAG-A2A-MCP Production Deployment Test Suite")
    print("Testing the production deployment of all services...")
    
    test_suite = ProductionTestSuite()
    report = await test_suite.run_all_tests()
    
    # Exit with error code if tests failed
    if report["success_rate"] < 75:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
