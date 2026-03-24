# Contributing to ContextRefactor

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment support (`venv`)

### Setting Up Your Development Environment

1. **Fork and clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/context-refactor.git
cd context-refactor
```

2. **Create a virtual environment:**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install in editable mode with dev dependencies:**

```bash
pip install -e ".[dev,mcp]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=context_refactor --cov=mcp_server --cov=cli

# Run tests matching a pattern
pytest tests/ -k "analyzer" -v
```

### Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Lint
ruff check context_refactor tests cli mcp_server

# Format (check only)
ruff format --check context_refactor tests cli mcp_server

# Type checking
mypy context_refactor mcp_server cli --ignore-missing-imports
```

### Making Changes

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** and write tests for new functionality.

3. **Run tests and quality checks** locally before pushing.

4. **Commit with clear messages:**

```bash
git commit -m "feat: add new refactor rule for function parameters"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/).

## Types of Contributions

### Bug Fixes

- File a GitHub issue describing the bug
- Create a PR with a fix and test case(s)
- Reference the issue in your PR

### New Features

- Discuss the feature in an issue first
- Implement with comprehensive tests
- Update documentation as needed

### Documentation

- Fix typos, clarify instructions
- Add examples of common use cases
- Document known limitations

### New Rules for Heuristics Engine

To add a new refactor rule:

1. Create a new class in `context_refactor/refactor_rules/` inheriting from `RefactorRule`
2. Implement `applies_to()` and `evaluate()` methods
3. Add tests in `tests/test_refactor_rules.py`
4. Update `HeuristicsEngine` if the rule should be automatically loaded
5. Document the rule's purpose and threshold

Example:

```python
from context_refactor.refactor_rules.base import RefactorRule
from context_refactor.models import FileTokenInfo, RefactorRecommendation

class MyNewRule(RefactorRule):
    def applies_to(self, file_info: FileTokenInfo) -> bool:
        """Return True if this rule should analyze the file."""
        return file_info.ext in {".py", ".ts"}
    
    def evaluate(self, file_info: FileTokenInfo, project_path: str) -> list[RefactorRecommendation]:
        """Analyze file and return recommendations."""
        # Implement your logic here
        return []
```

## Pull Request Process

1. **Create a PR** from your feature branch
2. **Provide a clear title and description** explaining your changes
3. **Link related issues** (e.g., "Closes #123")
4. **Ensure all CI checks pass:**
   - Tests pass on Python 3.11, 3.12, 3.13
   - Code quality checks pass
   - No new warnings
5. **Request review** from maintainers
6. **Address feedback** and update the PR

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Dependency updates, configuration changes
- `perf:` Performance improvements

Examples:

```
feat: add DuplicateCodeRule to heuristics engine
fix: resolve timeout issue with large projects
docs: clarify .context-refactor.json configuration
test: add tests for LargeFileRule threshold calculation
```

## Testing Guidelines

- **Write tests for new functionality** — aim for >80% code coverage
- **Test both happy path and edge cases** — empty files, missing files, invalid config
- **Use descriptive test names** — `test_large_file_triggers_recommendation` instead of `test_case_1`
- **Keep tests isolated** — no cross-test dependencies, use fixtures/temp directories

Example test:

```python
def test_my_new_feature(tmp_path):
    """Describe what the test validates."""
    # Setup
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1\n")
    
    # Execute
    result = my_function(str(tmp_path))
    
    # Assert
    assert result is not None
    assert len(result) > 0
```

## Documentation

When adding features or changing behavior:

- **Update README.md** if it affects user-facing functionality
- **Update docstrings** in the code
- **Add inline comments** for complex logic
- **Update TUNING_GUIDE.md** or **TOKEN_REPORT.md** if relevant

## Asking for Help

- **Open an issue** for bug reports or questions
- **Start a discussion** for feature ideas
- **Comment on PRs** with questions or suggestions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT).

---

Thank you for helping make ContextRefactor better! 🎉
