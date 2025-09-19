# Contributing to LLM Bank Parser

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/llm-bank-parser
cd llm-bank-parser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black isort flake8

# Run tests
pytest

# Format code
black src/
isort src/
```

### Code Style

- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for public functions

### Adding New Bank Support

If you want to add support for a new bank:

1. Test the existing system with your bank's statements
2. If it works, add the bank name to the README
3. If it doesn't work, create an issue with:
   - Anonymized sample statement (remove personal data)
   - Error messages
   - Bank name and statement format details

### Bug Reports

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

### Feature Requests

Feature requests are welcome! Please:

1. Check if the feature already exists
2. Explain the problem you're trying to solve
3. Describe your proposed solution
4. Consider the scope - start small and iterate

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Areas for Contribution

### High Priority
- [ ] Add comprehensive test suite
- [ ] Support for additional LLM providers (OpenAI, Anthropic)
- [ ] Better error handling and recovery
- [ ] Performance optimizations

### Medium Priority
- [ ] Transaction categorization using LLMs
- [ ] Export to additional formats (Excel, JSON)
- [ ] Docker containerization
- [ ] CI/CD pipeline setup

### Nice to Have
- [ ] Web interface
- [ ] Real-time processing API
- [ ] Integration with accounting software
- [ ] Mobile app support

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## Questions?

Feel free to open an issue with the label "question" or reach out to the maintainers directly.

Thank you for contributing! 🚀