# Contributing to Observables

Thank you for your interest in contributing to the Observables library! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Git
- pip

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/observables.git
   cd observables
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e .[dev]
   ```

## Development Workflow

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=observables --cov-report=html

# Run specific test file
pytest tests/test_observables.py

# Run specific test class
pytest tests/test_observables.py::TestObservableSingleValue
```

### Code Quality Checks
```bash
# Format code
black observables tests
isort observables tests

# Lint code
flake8 observables tests

# Type checking
mypy observables
```

### Using Makefile (if available)
```bash
# Run all checks
make check

# Format code
make format

# Run tests with coverage
make test-cov

# Clean build artifacts
make clean
```

## Architecture Overview

The Observables library uses a **component-based architecture** where observables are composed of:

- **Component Values**: The actual data being observed
- **Binding Handlers**: Manage bidirectional connections between observables  
- **Verification Methods**: Validate data changes before applying them
- **Copy Methods**: Control how data is duplicated during binding operations

### Key Design Principles
- **Composition over Inheritance**: Use component composition for flexibility
- **Type Safety**: Full generic support with comprehensive type hints
- **Performance**: Optimized binding and change detection
- **Memory Efficiency**: Automatic cleanup of unused bindings and listeners

## Code Style

### Python Code
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for all function parameters and return values
- Keep functions small and focused
- Write docstrings for all public functions and classes

### Example
```python
from typing import List, Optional, Callable

def process_items(
    items: List[str], 
    callback: Optional[Callable[[str], None]] = None
) -> List[str]:
    """
    Process a list of items with an optional callback.
    
    Args:
        items: List of strings to process
        callback: Optional callback function for each item
        
    Returns:
        Processed list of items
    """
    result = []
    for item in items:
        processed = item.upper()
        if callback:
            callback(processed)
        result.append(processed)
    return result
```

### Testing
- Write tests for all new functionality
- Aim for high test coverage (>90%)
- Use descriptive test names
- Test both positive and negative cases
- Test edge cases and error conditions

### Example Test
```python
def test_process_items_with_callback():
    """Test processing items with a callback function."""
    items = ["hello", "world"]
    processed_items = []
    
    def callback(item: str) -> None:
        processed_items.append(item)
    
    result = process_items(items, callback)
    
    assert result == ["HELLO", "WORLD"]
    assert processed_items == ["HELLO", "WORLD"]
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   make check  # or run individual commands
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Use a descriptive title
   - Describe the changes in detail
   - Reference any related issues
   - Include test results if applicable

## Pull Request Guidelines

### Title Format
- Use present tense ("Add feature" not "Added feature")
- Be descriptive but concise
- Start with a verb

### Description
- Explain what the PR does
- Describe any breaking changes
- Include usage examples if applicable
- Reference related issues

### Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Type hints added
- [ ] Error handling implemented

## Issue Reporting

### Bug Reports
- Use the bug report template
- Include steps to reproduce
- Provide error messages and stack traces
- Specify Python version and OS

### Feature Requests
- Use the feature request template
- Explain the use case
- Suggest implementation approach
- Consider backward compatibility

## Release Process

### Version Numbers
- Follow [Semantic Versioning](https://semver.org/)
- Update version in `pyproject.toml` and `__init__.py`
- Update `CHANGELOG.md`

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version numbers updated
- [ ] Tag created
- [ ] PyPI package built and uploaded

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Ask questions in PR comments

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Provide constructive feedback
- Help others learn and grow

## License

By contributing to this project, you agree that your contributions will be licensed under the Apache License, Version 2.0.

Thank you for contributing to Observables! 🎉
