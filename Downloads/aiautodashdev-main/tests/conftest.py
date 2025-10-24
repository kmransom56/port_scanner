"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, AGENT_REGISTRY


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_agent():
    """Sample agent data for testing"""
    return {
        "id": "test-agent-001",
        "name": "Test Agent",
        "type": "test",
        "status": "active",
        "tasks_completed": 0,
        "last_execution": None,
        "description": "Test agent for unit tests",
    }


@pytest.fixture
def reset_agent_registry():
    """Reset agent registry to default state after test"""
    original_registry = AGENT_REGISTRY.copy()
    yield
    AGENT_REGISTRY.clear()
    AGENT_REGISTRY.extend(original_registry)
