# Contributing to MTDify

Thank you for your interest in contributing to MTDify! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please be kind and constructive in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:

1. **A clear title** describing the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** — what should happen
4. **Actual behavior** — what actually happens
5. **Environment details** — Python version, OS, browser, etc.
6. **Screenshots** if applicable

### Suggesting Features

We welcome feature suggestions! Please create an issue with:

1. **A clear description** of the feature
2. **Use case** — why is this feature needed?
3. **Proposed solution** — how do you envision it working?
4. **Alternatives considered** — other ways to solve the problem

### Submitting Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- A code editor (VS Code, PyCharm, etc.)

### Getting Started

1. **Fork and clone**

   ```bash
   git clone https://github.com/YOUR-USERNAME/mtdify.git
   cd mtdify
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment**

   ```bash
   cp .env.example .env
   ```

5. **Initialize the database**

   ```bash
   python manage.py migrate
   python manage.py create_default_user
   ```

6. **Run the development server**

   ```bash
   python manage.py runserver
   ```

### Creating a Branch

Use descriptive branch names:

- `feature/add-invoice-generation`
- `fix/vat-calculation-rounding`
- `docs/update-installation-guide`

```bash
git checkout -b feature/your-feature-name
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

### Django Conventions

- Follow Django's coding style
- Use class-based views where appropriate
- Keep business logic in models or utility functions
- Use Django's ORM properly — avoid raw SQL unless necessary

### Templates

- Use Django's template inheritance
- Keep templates clean and readable
- Use semantic HTML
- Follow the existing Tailwind CSS patterns

### Example Code Style

```python
def calculate_vat(amount, rate):
    """
    Calculate VAT amount for a given base amount and rate.
    
    Args:
        amount: The base amount (Decimal)
        rate: The VAT rate as a percentage (Decimal, e.g., 20.00 for 20%)
    
    Returns:
        The VAT amount as a Decimal
    """
    from decimal import Decimal
    return (amount * rate / Decimal("100")).quantize(Decimal("0.01"))
```

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test bookkeeping

# Run with pytest (if configured)
pytest
```

### Writing Tests

- Write tests for new features
- Ensure existing tests pass before submitting
- Test edge cases and error conditions
- Use meaningful test names

```python
from django.test import TestCase
from bookkeeping.models import Income

class IncomeModelTest(TestCase):
    def test_income_string_representation(self):
        """Test the string representation of an Income instance."""
        income = Income(description="Test Income", amount=100.00)
        self.assertIn("Test Income", str(income))
```

## Commit Messages

Write clear, concise commit messages:

- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Add a blank line before detailed description if needed

**Good examples:**

```
Add VAT rate selector to expense form

Fix quarterly report date range calculation

Update README with Docker deployment instructions
```

**Bad examples:**

```
fixed stuff
updates
WIP
```

## Pull Request Process

1. **Ensure your code works** — Test locally before submitting
2. **Update documentation** — If you changed functionality, update docs
3. **Fill out the PR template** — Provide context and details
4. **Link related issues** — Use "Fixes #123" to auto-close issues
5. **Respond to feedback** — Be open to suggestions and changes
6. **Keep PRs focused** — One feature or fix per PR

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated (if applicable)
- [ ] Tests added/updated (if applicable)
- [ ] All tests pass locally
- [ ] No new warnings introduced

## Documentation

### Where to Document

- **README.md** — Installation, quick start, overview
- **Code comments** — Complex logic explanation
- **Docstrings** — Function/class documentation
- **Wiki/docs** — Detailed guides and tutorials

### Documentation Style

- Use clear, simple language
- Include code examples where helpful
- Keep documentation up-to-date with code changes
- Use proper Markdown formatting

## Project Structure

Understanding the codebase:

```
mtdify/
├── accounts/          # User authentication
├── bookkeeping/       # Core financial tracking
│   ├── models.py      # Income, Expense, Category
│   ├── views/         # View functions
│   ├── forms.py       # Form definitions
│   └── utils.py       # Tax year utilities
├── business/          # Business profile
├── mtdify/            # Project settings
└── templates/         # HTML templates
```

## Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Create an Issue
- **Security:** Email security concerns privately (see SECURITY.md)

## Recognition

Contributors will be recognized in:

- The project README
- Release notes for significant contributions
- The contributors page on the website

---

Thank you for contributing to MTDify! Your efforts help make bookkeeping easier for UK sole traders everywhere.