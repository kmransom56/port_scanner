"""
Test agent functionality
"""

import pytest
from datetime import datetime


@pytest.mark.unit
def test_agent_structure(client):
    """Test that agents have correct structure"""
    response = client.get("/registry")
    agents = response.json()["agents"]

    for agent in agents:
        assert "id" in agent
        assert "name" in agent
        assert "type" in agent
        assert "status" in agent
        assert "tasks_completed" in agent
        assert "description" in agent
        assert agent["status"] in ["active", "idle", "error"]


@pytest.mark.unit
def test_agent_types(client):
    """Test that all expected agent types exist"""
    response = client.get("/registry")
    agents = response.json()["agents"]

    agent_types = [agent["type"] for agent in agents]
    expected_types = ["data_analysis", "reporting", "automation", "support", "development"]

    for expected_type in expected_types:
        assert expected_type in agent_types, f"Missing agent type: {expected_type}"


@pytest.mark.unit
def test_agent_execution_updates_status(client):
    """Test that executing an agent updates its status"""
    agent_id = "agent-001"

    # Get initial state
    response = client.get(f"/registry/{agent_id}")
    initial_data = response.json()

    # Execute agent
    response = client.post(f"/registry/{agent_id}/execute")
    assert response.status_code == 200

    # Get updated state
    response = client.get(f"/registry/{agent_id}")
    updated_data = response.json()

    # Verify updates
    assert updated_data["tasks_completed"] == initial_data["tasks_completed"] + 1
    assert "last_execution" in updated_data
    assert updated_data["last_execution"] is not None


@pytest.mark.unit
def test_multiple_agent_executions(client):
    """Test executing multiple agents"""
    agent_ids = ["agent-001", "agent-002", "agent-003"]

    for agent_id in agent_ids:
        response = client.post(f"/registry/{agent_id}/execute")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.unit
def test_agent_task_counter(client):
    """Test that task counter increments correctly"""
    agent_id = "agent-001"

    # Get initial count
    response = client.get(f"/registry/{agent_id}")
    initial_count = response.json()["tasks_completed"]

    # Execute multiple times
    executions = 3
    for _ in range(executions):
        client.post(f"/registry/{agent_id}/execute")

    # Verify count
    response = client.get(f"/registry/{agent_id}")
    final_count = response.json()["tasks_completed"]

    assert final_count == initial_count + executions
