"""
Shared pytest configuration and fixtures for RAG-A2A-MCP test suite
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to Python path (prepend to avoid collision with installed packages like 'a2a-sdk')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from a2a.protocol import A2AProtocol
from agents.greeting_agent_a2a import GreetingAgentA2A
from agents.hr_agent_a2a import HRAgentA2A

# Import commonly used classes for fixtures
from agents.main_agent_a2a import MainAgentA2A
from coordination.orchestrator import MultiAgentOrchestrator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def main_agent():
    """Fixture for MainAgentA2A instance"""
    return MainAgentA2A()


@pytest.fixture
def hr_agent():
    """Fixture for HRAgentA2A instance"""
    return HRAgentA2A()


@pytest.fixture
def greeting_agent():
    """Fixture for GreetingAgentA2A instance"""
    return GreetingAgentA2A()


@pytest.fixture
def orchestrator():
    """Fixture for MultiAgentOrchestrator instance"""
    return MultiAgentOrchestrator()


@pytest.fixture
def test_a2a_protocol():
    """Fixture for A2A protocol instance for testing"""
    return A2AProtocol(
        agent_id="test_agent",
        agent_name="TestAgent",
        endpoint="http://localhost:9999",
        secret_key="rag_a2a_mcp_secret",
    )


@pytest.fixture
def mock_mcp_server():
    """Fixture for mocked MCP server"""
    mock_mcp = Mock()
    mock_mcp.call_tool.return_value = {"content": []}
    return mock_mcp


@pytest.fixture
def sample_employee_data():
    """Fixture for sample employee data used in tests"""
    return [
        {
            "id": 1,
            "name": "Alice Johnson",
            "department": "Engineering",
            "position": "Software Engineer",
            "salary": 95000,
            "hire_date": "2023-01-15",
        },
        {
            "id": 2,
            "name": "Bob Smith",
            "department": "HR",
            "position": "HR Manager",
            "salary": 80000,
            "hire_date": "2022-06-01",
        },
        {
            "id": 3,
            "name": "Carol Davis",
            "department": "Engineering",
            "position": "Senior Developer",
            "salary": 110000,
            "hire_date": "2021-03-10",
        },
    ]


@pytest.fixture
def test_context():
    """Fixture for common test context"""
    return {"test_mode": True, "mock_environment": True, "disable_external_calls": True}


@pytest.fixture(autouse=True)
def patch_external_calls():
    """Auto-fixture to patch external HTTP calls in all tests"""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:

        # Default mock responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "healthy"}

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result": "mocked_response"}

        yield mock_get, mock_post


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add custom markers"""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add unit marker to unit tests
        if "unit" in str(item.fspath) or "integration" not in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "asyncio: mark test as async")


# Test reporting
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test results available to fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture
def test_report(request):
    """Fixture to access test results"""
    return getattr(request.node, "rep_call", None)
