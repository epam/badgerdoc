# BadgerDoc Test Automation Framework

This project is a Python-based **test automation framework** built with [pytest](https://docs.pytest.org/).

## Getting Started

### 1. Install PDM
Make sure you have [PDM](https://pdm-project.org/latest/#installation) installed:

```bash
brew install pdm    # macOS
# or
pip install pdm
```

Verify installation:

```bash
pdm --version
```

### 2. Clone the repository

```bash
git clone https://github.com/epam/badgerdoc.git
cd badgerdoc
```

### 3. Install dependencies

```bash
pdm install
```

### 4. Pre-commit hooks

Enable pre-commit to enforce style and linting:
```bash
pre-commit install
``` 
Now hooks will run automatically before each commit.

### 5. Run tests

```bash
pdm run pytest
```