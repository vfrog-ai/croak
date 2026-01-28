"""Agent definition loader and router."""

from pathlib import Path
from typing import Dict, Optional, List, Tuple
import yaml
from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    """Single agent capability."""
    id: str
    name: str
    description: str


class AgentCommand(BaseModel):
    """Agent menu command."""
    trigger: str
    aliases: List[str] = Field(default_factory=list)
    cli: Optional[str] = None
    description: str
    capability: str
    workflow: Optional[str] = None
    type: str = "workflow"
    requires_confirmation: bool = False
    mutates_state: bool = False


class CriticalAction(BaseModel):
    """Critical action rule."""
    id: str
    rule: str
    when: str
    violation: str = "warning"  # warning, error, block


class Guardrail(BaseModel):
    """Guardrail check."""
    id: str
    name: str
    check: str
    trigger: str
    condition: str
    severity: str = "warning"
    error_message: str = ""


class HandoffSpec(BaseModel):
    """Handoff specification."""
    agent: str  # from or to agent
    contract: str
    schema_path: str = Field(alias="schema")
    required_fields: List[str] = Field(default_factory=list)


class KnowledgeFile(BaseModel):
    """Knowledge file reference."""
    id: str
    path: str
    load: str = "on_demand"  # on_demand, always, capability:xxx
    description: str = ""


class AgentDefinition(BaseModel):
    """Loaded agent definition."""
    id: str
    name: str
    title: str
    icon: str
    version: str = "1.0"
    agent_version: str = "0.1.0"
    has_sidecar: bool = False

    # Persona
    role: str = ""
    identity: str = ""
    communication_style: str = ""
    principles: str = ""

    # Capabilities and commands
    capabilities_summary: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    commands: List[AgentCommand] = Field(default_factory=list)

    # Rules and guardrails
    critical_actions: List[CriticalAction] = Field(default_factory=list)
    guardrails: List[Guardrail] = Field(default_factory=list)

    # Handoffs
    receives_from: List[HandoffSpec] = Field(default_factory=list)
    sends_to: List[HandoffSpec] = Field(default_factory=list)

    # Knowledge and templates
    knowledge_files: List[KnowledgeFile] = Field(default_factory=list)
    template_files: List[str] = Field(default_factory=list)

    def get_system_prompt(self) -> str:
        """Generate system prompt for AI assistant.

        Returns:
            Formatted system prompt string.
        """
        caps_list = "\n".join(
            f"- **{c.name}**: {c.description}"
            for c in self.capabilities
        )
        cmds_list = "\n".join(
            f"- `{c.cli}` - {c.description}"
            for c in self.commands
            if c.cli
        )
        rules_list = "\n".join(
            f"- {a.rule}"
            for a in self.critical_actions
        )

        return f"""You are **{self.name}**, the CROAK {self.title}. {self.icon}

## Role
{self.role}

## Identity
{self.identity}

## Communication Style
{self.communication_style}

## Principles
{self.principles}

## Capabilities
{caps_list}

## Available Commands
{cmds_list}

## Critical Rules
{rules_list}
"""

    def get_command(self, trigger: str) -> Optional[AgentCommand]:
        """Get command by trigger or alias.

        Args:
            trigger: Command trigger or alias.

        Returns:
            AgentCommand if found, None otherwise.
        """
        trigger_lower = trigger.lower()
        for cmd in self.commands:
            if cmd.trigger.lower() == trigger_lower:
                return cmd
            if trigger_lower in [a.lower() for a in cmd.aliases]:
                return cmd
        return None

    def get_capability(self, capability_id: str) -> Optional[AgentCapability]:
        """Get capability by ID.

        Args:
            capability_id: Capability ID.

        Returns:
            AgentCapability if found, None otherwise.
        """
        for cap in self.capabilities:
            if cap.id == capability_id:
                return cap
        return None


class AgentLoader:
    """Load and manage agent definitions."""

    def __init__(self, agents_dir: Path):
        """Initialize agent loader.

        Args:
            agents_dir: Directory containing agent definitions.
        """
        self.agents_dir = agents_dir
        self._agents: Dict[str, AgentDefinition] = {}
        self._command_map: Dict[str, Tuple[str, AgentCommand]] = {}

    def load_all(self) -> Dict[str, AgentDefinition]:
        """Load all agent definitions.

        Returns:
            Dict mapping agent name to definition.
        """
        if not self.agents_dir.exists():
            return self._agents

        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir():
                # Look for {name}.agent.yaml
                yaml_file = agent_dir / f"{agent_dir.name}.agent.yaml"
                if yaml_file.exists():
                    self.load_agent(yaml_file)
                else:
                    # Fallback to agent.yaml
                    yaml_file = agent_dir / "agent.yaml"
                    if yaml_file.exists():
                        self.load_agent(yaml_file)

        return self._agents

    def load_agent(self, yaml_path: Path) -> AgentDefinition:
        """Load single agent from YAML.

        Args:
            yaml_path: Path to agent YAML file.

        Returns:
            Loaded AgentDefinition.
        """
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Handle nested 'agent' key
        agent_data = data.get('agent', data)
        metadata = agent_data.get('metadata', {})
        persona = agent_data.get('persona', {})
        caps_data = agent_data.get('capabilities', {})
        menu_data = agent_data.get('menu', {})
        critical_data = agent_data.get('critical_actions', {})
        guardrails_data = agent_data.get('guardrails', {})
        handoffs_data = agent_data.get('handoffs', {})
        knowledge_data = agent_data.get('knowledge', {})
        templates_data = agent_data.get('templates', {})

        # Parse capabilities
        capabilities = [
            AgentCapability(**c)
            for c in caps_data.get('items', [])
        ]

        # Parse commands
        commands = [
            AgentCommand(**c)
            for c in menu_data.get('commands', [])
        ]

        # Parse critical actions
        critical_actions = [
            CriticalAction(**a)
            for a in critical_data.get('items', [])
        ]

        # Parse guardrails
        guardrails = [
            Guardrail(**g)
            for g in guardrails_data.get('checks', [])
        ]

        # Parse handoffs
        receives_from = []
        for h in handoffs_data.get('receives', []):
            receives_from.append(HandoffSpec(
                agent=h.get('from', ''),
                contract=h.get('contract', ''),
                schema=h.get('schema', ''),
                required_fields=h.get('required_fields', []),
            ))

        sends_to = []
        for h in handoffs_data.get('sends', []):
            sends_to.append(HandoffSpec(
                agent=h.get('to', ''),
                contract=h.get('contract', ''),
                schema=h.get('schema', ''),
                required_fields=h.get('required_fields', []),
            ))

        # Parse knowledge files
        knowledge_files = [
            KnowledgeFile(**k)
            for k in knowledge_data.get('files', [])
        ]

        # Parse template files
        template_files = [
            t.get('path', '')
            for t in templates_data.get('files', [])
            if t.get('path')
        ]

        agent = AgentDefinition(
            id=metadata.get('id', ''),
            name=metadata.get('name', ''),
            title=metadata.get('title', ''),
            icon=metadata.get('icon', ''),
            version=metadata.get('version', '1.0'),
            agent_version=metadata.get('agent_version', '0.1.0'),
            has_sidecar=metadata.get('has_sidecar', False),
            role=persona.get('role', ''),
            identity=persona.get('identity', ''),
            communication_style=persona.get('communication_style', ''),
            principles=persona.get('principles', ''),
            capabilities_summary=caps_data.get('summary', ''),
            capabilities=capabilities,
            commands=commands,
            critical_actions=critical_actions,
            guardrails=guardrails,
            receives_from=receives_from,
            sends_to=sends_to,
            knowledge_files=knowledge_files,
            template_files=template_files,
        )

        # Register agent
        agent_key = agent.name.lower()
        self._agents[agent_key] = agent

        # Register commands for routing
        for cmd in commands:
            self._command_map[cmd.trigger.lower()] = (agent_key, cmd)
            for alias in cmd.aliases:
                self._command_map[alias.lower()] = (agent_key, cmd)

        return agent

    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """Get agent by name.

        Args:
            name: Agent name (case-insensitive).

        Returns:
            AgentDefinition if found, None otherwise.
        """
        return self._agents.get(name.lower())

    def get_agent_by_role(self, role: str) -> Optional[AgentDefinition]:
        """Get agent by role/title.

        Args:
            role: Role like 'data', 'training', 'evaluation', 'deployment'.

        Returns:
            AgentDefinition if found, None otherwise.
        """
        role_mapping = {
            'data': 'scout',
            'training': 'coach',
            'evaluation': 'judge',
            'deployment': 'shipper',
            'router': 'dispatcher',
        }
        agent_name = role_mapping.get(role.lower(), role.lower())
        return self._agents.get(agent_name)

    def route_command(self, user_input: str) -> Optional[Tuple[AgentDefinition, AgentCommand]]:
        """Route user input to appropriate agent and command.

        Args:
            user_input: User's input text.

        Returns:
            Tuple of (agent, command) if matched, None otherwise.
        """
        input_lower = user_input.lower().strip()

        # Direct command match
        for trigger, (agent_key, cmd) in self._command_map.items():
            if input_lower.startswith(trigger):
                return (self._agents[agent_key], cmd)

        # Fuzzy match on keywords
        for trigger, (agent_key, cmd) in self._command_map.items():
            trigger_words = set(trigger.split())
            input_words = set(input_lower.split())
            if trigger_words & input_words:  # Any common words
                return (self._agents[agent_key], cmd)

        return None

    def get_all_commands(self) -> List[Tuple[str, str, str]]:
        """Get all available commands.

        Returns:
            List of (trigger, agent_name, description) tuples.
        """
        commands = []
        seen = set()
        for trigger, (agent_key, cmd) in self._command_map.items():
            if cmd.trigger not in seen:
                commands.append((
                    cmd.cli or cmd.trigger,
                    self._agents[agent_key].name,
                    cmd.description,
                ))
                seen.add(cmd.trigger)
        return sorted(commands)

    def get_router_context(self) -> str:
        """Get context for router agent to make decisions.

        Returns:
            Formatted string describing all agents and commands.
        """
        agents_info = []
        for agent in self._agents.values():
            commands = [
                f"  - {c.trigger}: {c.description}"
                for c in agent.commands
            ]
            agents_info.append(
                f"**{agent.name}** ({agent.title}):\n" +
                "\n".join(commands)
            )
        return "\n\n".join(agents_info)
