"""Tests for CROAK agent system."""

import pytest
from pathlib import Path
import tempfile
import yaml

from croak.agents.loader import AgentLoader, AgentDefinition, AgentCapability, AgentCommand


class TestAgentDefinition:
    """Test AgentDefinition class."""

    def test_create_agent_definition(self):
        """Test creating an agent definition."""
        agent = AgentDefinition(
            id="test-agent",
            name="test_agent",
            title="Test Agent",
            icon="T",
            role="Testing",
            capabilities=[
                AgentCapability(
                    id="test-cap",
                    name="test",
                    description="Run tests",
                )
            ],
            commands=[
                AgentCommand(
                    trigger="run-tests",
                    description="Run all tests",
                    capability="test-cap",
                )
            ],
        )

        assert agent.id == "test-agent"
        assert agent.name == "test_agent"
        assert len(agent.capabilities) == 1
        assert len(agent.commands) == 1

    def test_get_system_prompt(self):
        """Test generating system prompt."""
        agent = AgentDefinition(
            id="data-agent",
            name="data_agent",
            title="Data Agent",
            icon="D",
            role="Data preparation",
            capabilities=[
                AgentCapability(id="validate", name="validate", description="Validate data")
            ],
            commands=[],
        )

        prompt = agent.get_system_prompt()

        assert "Data Agent" in prompt
        assert "Data preparation" in prompt
        assert "validate" in prompt.lower()


class TestAgentLoader:
    """Test AgentLoader class."""

    def _create_agent_dir(self, agents_dir, agent_id, agent_name, title, role,
                          capabilities=None, commands=None):
        """Helper to create a properly structured agent directory."""
        agent_subdir = agents_dir / agent_id
        agent_subdir.mkdir(parents=True, exist_ok=True)

        agent_yaml = {
            "agent": {
                "metadata": {
                    "id": agent_id,
                    "name": agent_name,
                    "title": title,
                    "icon": "T",
                },
                "persona": {
                    "role": role,
                },
                "capabilities": {
                    "items": capabilities or []
                },
                "menu": {
                    "commands": commands or []
                },
            }
        }

        yaml_path = agent_subdir / f"{agent_id}.agent.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(agent_yaml, f)

        return yaml_path

    def test_load_agent_from_yaml(self):
        """Test loading agent from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"

            self._create_agent_dir(
                agents_dir,
                agent_id="test-agent",
                agent_name="test_agent",
                title="Test Agent",
                role="Testing",
                capabilities=[
                    {"id": "test-cap", "name": "test", "description": "Test capability"}
                ],
                commands=[
                    {
                        "trigger": "test-cmd",
                        "description": "Test command",
                        "capability": "test-cap",
                    }
                ],
            )

            loader = AgentLoader(agents_dir)
            agents = loader.load_all()

            assert "test_agent" in agents
            assert agents["test_agent"].title == "Test Agent"

    def test_load_multiple_agents(self):
        """Test loading multiple agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"

            for name in ["data", "training", "eval"]:
                self._create_agent_dir(
                    agents_dir,
                    agent_id=f"{name}-agent",
                    agent_name=f"{name}_agent",
                    title=f"{name.title()} Agent",
                    role=f"{name.title()} operations",
                )

            loader = AgentLoader(agents_dir)
            agents = loader.load_all()

            assert len(agents) == 3
            assert "data_agent" in agents
            assert "training_agent" in agents
            assert "eval_agent" in agents

    def test_route_command(self):
        """Test command routing to correct agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"

            self._create_agent_dir(
                agents_dir,
                agent_id="data-agent",
                agent_name="data_agent",
                title="Data Agent",
                role="Data",
                commands=[
                    {
                        "trigger": "validate",
                        "description": "Validate dataset",
                        "capability": "validate-cap",
                    }
                ],
            )

            loader = AgentLoader(agents_dir)
            loader.load_all()

            result = loader.route_command("validate my dataset")

            assert result is not None
            agent, command = result
            assert agent.id == "data-agent"
            assert command.trigger == "validate"

    def test_route_command_no_match(self):
        """Test command routing with no match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()

            loader = AgentLoader(agents_dir)
            loader.load_all()

            result = loader.route_command("unknown command")
            assert result is None
