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
            role="Testing",
            expertise=["testing", "validation"],
            capabilities=[
                AgentCapability(
                    name="test",
                    description="Run tests",
                )
            ],
            commands=[
                AgentCommand(
                    name="run-tests",
                    description="Run all tests",
                    usage="croak test",
                    examples=["croak test --verbose"],
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
            role="Data preparation",
            expertise=["data validation", "preprocessing"],
            capabilities=[
                AgentCapability(name="validate", description="Validate data")
            ],
            commands=[],
        )

        prompt = agent.get_system_prompt()

        assert "Data Agent" in prompt
        assert "Data preparation" in prompt
        assert "data validation" in prompt


class TestAgentLoader:
    """Test AgentLoader class."""

    def test_load_agent_from_yaml(self):
        """Test loading agent from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()

            # Create agent YAML
            agent_yaml = {
                "id": "test-agent",
                "name": "test_agent",
                "title": "Test Agent",
                "role": "Testing",
                "expertise": ["testing"],
                "capabilities": [
                    {"name": "test", "description": "Test capability"}
                ],
                "commands": [
                    {
                        "name": "test-cmd",
                        "description": "Test command",
                        "usage": "croak test",
                        "examples": [],
                    }
                ],
            }

            agent_path = agents_dir / "test-agent.yaml"
            with open(agent_path, "w") as f:
                yaml.dump(agent_yaml, f)

            # Load agent
            loader = AgentLoader(agents_dir)
            agents = loader.load_all()

            assert "test-agent" in agents
            assert agents["test-agent"].title == "Test Agent"

    def test_load_multiple_agents(self):
        """Test loading multiple agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()

            # Create multiple agent YAMLs
            for name in ["data", "training", "eval"]:
                agent_yaml = {
                    "id": f"{name}-agent",
                    "name": f"{name}_agent",
                    "title": f"{name.title()} Agent",
                    "role": f"{name.title()} operations",
                    "expertise": [name],
                    "capabilities": [],
                    "commands": [],
                }

                with open(agents_dir / f"{name}-agent.yaml", "w") as f:
                    yaml.dump(agent_yaml, f)

            loader = AgentLoader(agents_dir)
            agents = loader.load_all()

            assert len(agents) == 3
            assert "data-agent" in agents
            assert "training-agent" in agents
            assert "eval-agent" in agents

    def test_route_command(self):
        """Test command routing to correct agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()

            # Create agent with specific command
            agent_yaml = {
                "id": "data-agent",
                "name": "data_agent",
                "title": "Data Agent",
                "role": "Data",
                "expertise": [],
                "capabilities": [],
                "commands": [
                    {
                        "name": "validate",
                        "description": "Validate dataset",
                        "usage": "croak validate",
                        "examples": [],
                    }
                ],
            }

            with open(agents_dir / "data-agent.yaml", "w") as f:
                yaml.dump(agent_yaml, f)

            loader = AgentLoader(agents_dir)
            loader.load_all()

            result = loader.route_command("validate my dataset")

            assert result is not None
            agent, command = result
            assert agent.id == "data-agent"
            assert command.name == "validate"

    def test_route_command_no_match(self):
        """Test command routing with no match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir()

            loader = AgentLoader(agents_dir)
            loader.load_all()

            result = loader.route_command("unknown command")
            assert result is None
