# Contributing to CROAK

Thank you for your interest in contributing to CROAK! 🐸

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- A vfrog.ai account (for testing annotation workflows)

### Development Setup

```bash
# Clone the repo
git clone https://github.com/vfrog-ai/croak.git
cd croak

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Use the bug report template
3. Include:
   - Python version
   - CROAK version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

### Suggesting Features

1. Check existing issues/discussions
2. Use the feature request template
3. Describe the use case
4. Explain why existing solutions don't work

### Code Contributions

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Run linting: `ruff check .`
6. Run tests: `pytest`
7. Commit with clear messages
8. Push and create a Pull Request

## Code Style

We use:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Black-compatible** formatting

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Type check
mypy src/croak
```

## Project Structure

```
croak/
├── agents/           # Agent definitions (YAML + prompts)
├── workflows/        # Workflow specifications
├── knowledge/        # Knowledge base documents
├── src/croak/        # Python package
│   ├── core/         # Core functionality
│   ├── data/         # Data handling
│   ├── integrations/ # External integrations
│   └── cli.py        # CLI entry point
├── tests/            # Test suite
└── examples/         # Example projects
```

## Writing Agent Definitions

Agents are defined in YAML with accompanying Markdown prompts:

```yaml
# agents/my-agent/agent.yaml
metadata:
  id: "croak/agents/my-agent"
  name: "MyAgent"
  title: "Agent Title"
  icon: "🎯"

persona:
  role: "Description of role"
  identity: |
    Detailed identity description...
  communication_style: |
    How the agent communicates...
```

## Writing Knowledge Files

Knowledge files should be:
- Concise but comprehensive
- Actionable with specific recommendations
- Up-to-date with current best practices
- Written in clear, technical English

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run with coverage
pytest --cov=croak --cov-report=html
```

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update documentation if needed
- Add tests for new features
- Ensure CI passes
- Request review from maintainers

## Questions?

- Open a GitHub Discussion
- Check existing documentation
- Review closed issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
