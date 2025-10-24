"""
Test API endpoints
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "integrations" in data


@pytest.mark.unit
def test_root_endpoint(client):
    """Test root endpoint returns HTML"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.unit
def test_agent_registry_list(client):
    """Test listing all agents"""
    response = client.get("/registry")
    assert response.status_code == 200

    data = response.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) > 0


@pytest.mark.unit
def test_get_specific_agent(client):
    """Test getting a specific agent"""
    response = client.get("/registry/agent-001")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "agent-001"
    assert "name" in data
    assert "type" in data
    assert "status" in data


@pytest.mark.unit
def test_get_nonexistent_agent(client):
    """Test getting a non-existent agent"""
    response = client.get("/registry/nonexistent-agent")
    assert response.status_code == 404


@pytest.mark.unit
def test_execute_agent(client):
    """Test executing an agent"""
    response = client.post("/registry/agent-001/execute")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "result" in data
    assert "agent_id" in data["result"]


@pytest.mark.unit
def test_execute_nonexistent_agent(client):
    """Test executing a non-existent agent"""
    response = client.post("/registry/nonexistent-agent/execute")
    assert response.status_code == 404


@pytest.mark.unit
def test_stats_endpoint(client):
    """Test statistics endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200

    data = response.json()
    assert "stats" in data
    stats = data["stats"]
    assert "total_agents" in stats
    assert "active" in stats
    assert "idle" in stats
    assert "total_tasks_completed" in stats


@pytest.mark.unit
def test_integrations_endpoint(client):
    """Test integrations status endpoint"""
    response = client.get("/api/integrations")
    assert response.status_code == 200

    data = response.json()
    assert "integrations" in data
    integrations = data["integrations"]
    assert "ai_gateway" in integrations
    assert "autogen_studio" in integrations
    assert "prometheus" in integrations
    assert "mcp_server" in integrations


@pytest.mark.unit
def test_recommend_agent_no_params(client):
    """Test agent recommendation without parameters"""
    response = client.get("/api/agents/recommend")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "recommended_agent" in data
    assert "confidence" in data
    assert "reasoning" in data


@pytest.mark.unit
def test_recommend_agent_with_task_type(client):
    """Test agent recommendation with task type"""
    response = client.get("/api/agents/recommend?task_type=analysis")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["task_type"] == "analysis"
    assert data["recommended_agent"]["id"] == "agent-001"  # Data Analyzer


@pytest.mark.unit
def test_ai_analyze_agent(client):
    """Test AI agent analysis endpoint"""
    response = client.post("/api/agents/agent-001/ai-analyze")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "analysis" in data
    assert "agent_name" in data


@pytest.mark.unit
def test_ai_analyze_nonexistent_agent(client):
    """Test AI analysis of non-existent agent"""
    response = client.post("/api/agents/nonexistent-agent/ai-analyze")
    assert response.status_code == 404


@pytest.mark.unit
def test_prometheus_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Check for expected metrics
    metrics = response.text
    assert "aiautodash_agent_total" in metrics
    assert "aiautodash_tasks_completed_total" in metrics
    assert "aiautodash_api_requests_total" in metrics


@pytest.mark.unit
def test_autogen_status(client):
    """Test AutoGen Studio status endpoint"""
    response = client.get("/api/autogen/status")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "enabled" in data


@pytest.mark.integration
def test_full_workflow(client):
    """Test complete workflow: list, get, execute, stats"""
    # List agents
    response = client.get("/registry")
    assert response.status_code == 200
    agents = response.json()["agents"]
    agent_id = agents[0]["id"]

    # Get specific agent
    response = client.get(f"/registry/{agent_id}")
    assert response.status_code == 200
    initial_tasks = response.json()["tasks_completed"]

    # Execute agent
    response = client.post(f"/registry/{agent_id}/execute")
    assert response.status_code == 200

    # Verify task count increased
    response = client.get(f"/registry/{agent_id}")
    assert response.status_code == 200
    new_tasks = response.json()["tasks_completed"]
    assert new_tasks == initial_tasks + 1

    # Check stats updated
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()["stats"]
    assert stats["total_tasks_completed"] > 0


@pytest.mark.smoke
def test_all_critical_endpoints(client):
    """Smoke test for all critical endpoints"""
    critical_endpoints = [
        ("/", 200),
        ("/health", 200),
        ("/registry", 200),
        ("/api/stats", 200),
        ("/api/integrations", 200),
        ("/metrics", 200),
    ]

    for endpoint, expected_status in critical_endpoints:
        response = client.get(endpoint)
        assert response.status_code == expected_status, f"Endpoint {endpoint} failed"
