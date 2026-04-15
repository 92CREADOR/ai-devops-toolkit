# Contributing to AI DevOps Toolkit

Thank you for your interest in contributing! This document explains how to get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Convention](#commit-convention)

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, inclusive, and constructive. Harassment of any kind will not be tolerated.

---

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Open a new issue using the Bug Report template
3. Include: steps to reproduce, expected vs actual behavior, environment details

### Suggesting Features

1. Open an issue with the Feature Request template
2. Describe the problem your feature solves
3. Be open to discussion before starting implementation

### Good First Issues

Look for issues labeled `good first issue` - these are specifically designed for new contributors.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git
- (Optional) Docker

### Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/ai-devops-toolkit.git
cd ai-devops-toolkit
git remote add upstream https://github.com/92CREADOR/ai-devops-toolkit.git
```

### Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest
pytest --cov=. --cov-report=html
pytest log-analyzer/tests/
```

---

## Pull Request Process

1. Sync your fork: `git fetch upstream && git merge upstream/master`
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes following coding standards
4. Write/update tests - PRs without tests will not be merged
5. Run tests: `pytest`
6. Open a PR referencing the issue: `Closes #1`

---

## Coding Standards

### Python
- Follow PEP 8
- Use type hints everywhere
- Write docstrings (Google style)
- Max line length: 88 chars (Black formatter)
- Use Black for formatting, isort for imports

```bash
black .
isort .
flake8 .
mypy .
```

### TypeScript
- Follow ESLint rules in .eslintrc
- Use Prettier for formatting
- Prefer const over let; avoid var
- Use explicit types, avoid any

---

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

Closes #<issue>
```

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation only |
| test | Adding or fixing tests |
| refactor | Code refactoring |
| ci | CI/CD changes |
| chore | Maintenance |

---

## Recognition

All contributors will be listed in the README. Thank you for making this project better!

Questions? Open a Discussion or reach out via [LinkedIn](https://www.linkedin.com/in/alejandro-benvides-garcia/).
