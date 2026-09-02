# Contributing to BRAINK

Thank you for your interest in contributing to the BRAINK project. This document provides guidelines and standards for all contributions.

## Code of Conduct

- Be respectful and professional
- Assume good intentions
- Focus on constructive feedback
- Respect intellectual property

## Development Standards

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/Keddeh1/BRAINK-BETA-TEST.git
cd BRAINK-BETA-TEST

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,test]"
```

### Code Style

- **Python**: PEP 8 (enforced via Black, isort, flake8)
- **Line Length**: 100 characters max
- **Imports**: Alphabetically sorted and grouped (isort)
- **Naming**:
  - `classes`: PascalCase
  - `functions/variables`: snake_case
  - `constants`: UPPER_SNAKE_CASE
  - `private`: prefix with underscore `_`

### Type Hints

All public APIs must include type hints:

```python
def process_ring_state(
    ring_id: int,
    state: RingState,
) -> RingExecutionResult:
    """Process ring state transition."""
    pass
```

### Testing Requirements

- **Coverage**: Minimum 80% for all new code
- **Test Types**:
  - Unit tests (fast, isolated)
  - Integration tests (component interactions)
  - E2E tests (full workflows)
- **Naming**: `test_<function>_<scenario>.py`

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=braink

# Run specific marker
pytest -m unit
pytest -m integration

# Run in parallel
pytest -n auto
```

### File Organization

```
braink/
├── __init__.py
├── core/                    # Core architecture
│   ├── __init__.py
│   ├── rings.py            # Ring definitions
│   └── state.py            # State management
├── domain/                  # Domain engine
│   ├── __init__.py
│   ├── engine.py
│   └── validators.py
├── runtime/                 # Runtime engine
│   ├── __init__.py
│   ├── executor.py
│   └── scheduler.py
└── utils/                   # Utilities
    ├── __init__.py
    └── common.py

tests/
├── __init__.py
├── unit/
│   ├── test_rings.py
│   └── test_state.py
├── integration/
│   └── test_engine_integration.py
└── fixtures/
    └── conftest.py
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

**Scopes**: `core`, `domain`, `runtime`, `utils`, `ci`, `docs`

**Examples**:
```
feat(core): implement Ring 1 access validation
fix(domain): resolve state transition deadlock
docs(architecture): add Ring 2 specification
chore(ci): upgrade pytest to 7.4.0
```

### Commit Best Practices

- Small, focused commits
- One logical change per commit
- Imperative mood ("add" not "added")
- Reference issues: `Fixes #123`

## Pull Request Process

### Before Creating a PR

1. Create a feature branch: `git checkout -b feat/ring-1-validation`
2. Make your changes
3. Format code: `black braink/` and `isort braink/`
4. Run linters: `flake8 braink/` and `pylint braink/`
5. Run tests: `pytest --cov=braink`
6. Type check: `mypy braink/`
7. Security scan: `bandit -r braink/`
8. Update documentation
9. Add tests (aim for 80%+ coverage)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Documentation
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Code comments added

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No new warnings generated
- [ ] Tests cover new functionality
```

## Review Expectations

### For Reviewers

- Test the changes locally
- Check code style compliance
- Verify test coverage
- Review architecture impact
- Provide constructive feedback

### For Authors

- Respond to comments promptly
- Request re-review after changes
- Explain design decisions
- Be open to suggestions

## Documentation Standards

### Code Documentation

```python
def calculate_ring_access_cost(
    ring_level: int,
    operation_type: str,
) -> int:
    """
    Calculate execution cost for ring-level operation.

    Args:
        ring_level: Target ring level (0-3)
        operation_type: Type of operation (read/write/execute)

    Returns:
        Cost in cycles

    Raises:
        ValueError: If ring_level out of range
        KeyError: If operation_type unknown

    Example:
        >>> calculate_ring_access_cost(1, "write")
        150
    """
    pass
```

### Architecture Decision Records (ADRs)

For significant decisions, add an ADR to `docs/adr/`:

```markdown
# ADR-001: Ring 0 Memory Isolation Strategy

## Context
...

## Decision
...

## Consequences
...
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create annotated tag: `git tag -a v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions publishes release

## Getting Help

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: Check `docs/` and ARCHITECTURE.md

## Recognition

Contributors will be recognized in CHANGELOG.md and the project README.

---

Thank you for contributing to BRAINK!
