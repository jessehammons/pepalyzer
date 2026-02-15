# pepalyzer

A CLI tool for analyzing text files.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate  # On macOS/Linux (use venv\Scripts\activate on Windows)
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --verbose --cov=pepalyzer --cov-report=term-missing
```

## Installation

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the virtual environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Install the package in development mode

```bash
pip install -e ".[dev]"
```

This installs:
- The `pepalyzer` package in editable mode
- All development dependencies (pytest, black, mypy, flake8, etc.)

### 4. Set up pre-commit hooks

```bash
pre-commit install
```

This enables automatic code quality checks before each commit.

## Usage

```bash
pepalyzer --help
pepalyzer file1.txt file2.txt
```

## Development

### Running tests

```bash
pytest
```

### Running tests with coverage

```bash
pytest --verbose --cov=pepalyzer --cov-report=term-missing
```

### Running pre-commit hooks manually

```bash
pre-commit run --all-files
```

### Code formatting and linting

```bash
# Format code with black
black .

# Check with flake8
flake8 .

# Type check with mypy
mypy pepalyzer

# Security check with bandit
bandit -r pepalyzer -c pyproject.toml
```

## CI/CD

GitHub Actions automatically run tests on Python 3.9, 3.10, 3.11, and 3.12 for:
- All pushes to `main` and `develop` branches
- All pull requests to `main` and `develop` branches

The workflow runs:
1. Pre-commit hooks
2. Test suite with coverage
3. Coverage upload to Codecov
