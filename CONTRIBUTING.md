# 🤝 Contributing to NBA Prediction Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

---

## 📜 Code of Conduct

This project follows a Code of Conduct to ensure a welcoming environment for all contributors. Please be respectful, inclusive, and constructive in all interactions.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome diverse perspectives and experiences
- **Be constructive**: Provide helpful feedback and suggestions
- **Be professional**: Maintain professional conduct in all communications

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Poetry 1.5+
- Node.js 18+
- Git
- Docker (optional)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/NBA-Prediction.git
cd NBA-Prediction

# Add upstream remote
git remote add upstream https://github.com/ShauryaMallampati/NBA-Prediction.git
```

---

## 💻 Development Setup

### 1. Install Dependencies

```bash
# Python dependencies
poetry install

# Node dependencies
npm install

# Pre-commit hooks (optional but recommended)
poetry run pre-commit install
```

### 2. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys and configurations
```

### 3. Run Development Servers

```bash
# Terminal 1: Backend API
poetry run uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
npm run dev

# Visit http://localhost:3000
```

---

## 🛠️ How to Contribute

### Types of Contributions

We welcome:

1. **Bug fixes** - Fix issues in existing code
2. **New features** - Add new functionality
3. **Documentation** - Improve docs, add examples
4. **Data sources** - Add new data scrapers
5. **Model improvements** - Enhance ML models
6. **Tests** - Add or improve test coverage
7. **Performance** - Optimize code performance

### Contribution Workflow

1. **Find/Create an Issue**
   - Browse [open issues](https://github.com/ShauryaMallampati/NBA-Prediction/issues)
   - Comment on an issue to claim it
   - Or create a new issue to discuss your idea

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

3. **Make Changes**
   - Write code following our [coding standards](#coding-standards)
   - Add tests for new functionality
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Run Python tests
   poetry run pytest
   
   # Run frontend tests
   npm test
   
   # Run linters
   poetry run black src/ scripts/
   poetry run flake8 src/ scripts/
   npm run lint
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```
   
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub

---

## 📏 Coding Standards

### Python

- Follow [PEP 8](https://pep8.org/) style guide
- Use **Black** for formatting (line length: 100)
- Use **isort** for import sorting
- Use type hints where possible
- Write docstrings for all functions/classes

Example:

```python
from typing import List, Dict, Optional
import pandas as pd


def calculate_win_probability(
    team_features: pd.DataFrame,
    opponent_features: pd.DataFrame
) -> float:
    """
    Calculate win probability for a team given features.
    
    Args:
        team_features: DataFrame with team's features
        opponent_features: DataFrame with opponent's features
        
    Returns:
        Win probability (0.0 to 1.0)
        
    Raises:
        ValueError: If features are invalid
    """
    # Implementation here
    return 0.0
```

### JavaScript/TypeScript

- Use **Prettier** for formatting
- Use **ESLint** with recommended rules
- Use TypeScript types
- Use functional components with hooks
- Follow React best practices

Example:

```typescript
interface PredictionProps {
  gameId: string;
  homeTeam: string;
  awayTeam: string;
}

export const PredictionCard: React.FC<PredictionProps> = ({
  gameId,
  homeTeam,
  awayTeam
}) => {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  
  useEffect(() => {
    fetchPrediction(gameId).then(setPrediction);
  }, [gameId]);
  
  return (
    <div className="prediction-card">
      {/* Component JSX */}
    </div>
  );
};
```

### File Naming

- Python: `snake_case.py`
- TypeScript/React: `PascalCase.tsx` for components, `camelCase.ts` for utils
- Tests: `test_feature_name.py` or `FeatureName.test.tsx`

---

## 🧪 Testing Guidelines

### Python Tests

- Use **pytest** for all tests
- Place tests in `tests/` directory
- Mirror source structure: `tests/test_models/test_ensemble.py`
- Aim for 80%+ code coverage

```python
import pytest
from src.models.pregame.ensemble import EnsembleModel


def test_ensemble_prediction():
    """Test ensemble model prediction"""
    model = EnsembleModel()
    features = create_test_features()
    
    prediction = model.predict(features)
    
    assert 0 <= prediction <= 1
    assert isinstance(prediction, float)


@pytest.fixture
def sample_game_data():
    """Fixture for test game data"""
    return {
        'home_team': 'BOS',
        'away_team': 'LAL',
        'date': '2024-11-12'
    }
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_models/test_ensemble.py

# Run tests matching pattern
poetry run pytest -k "test_prediction"
```

---

## 🔄 Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code is formatted (Black, Prettier)
3. ✅ Linters pass (flake8, ESLint)
4. ✅ Documentation updated
5. ✅ CHANGELOG.md updated (if applicable)

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
Describe tests performed

## Screenshots (if UI changes)
Add screenshots

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one maintainer** must approve
3. **All conversations** must be resolved
4. Once approved, maintainer will merge

---

## 🐛 Issue Guidelines

### Creating Issues

Use issue templates:

**Bug Report:**
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., macOS 13]
- Python: [e.g., 3.10.5]
- Browser: [e.g., Chrome 120]

## Screenshots
Add screenshots if applicable
```

**Feature Request:**
```markdown
## Feature Description
Clear description of proposed feature

## Motivation
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

---

## 📚 Additional Resources

### Documentation

- [API Documentation](docs/API.md)
- [Model Card](docs/MODEL_CARD.md)
- [Feature Descriptions](docs/FEATURES.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

### External Resources

- [NBA Stats API](https://github.com/swar/nba_api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)

---

## 🎯 Good First Issues

Look for issues labeled `good-first-issue` - these are great for first-time contributors:

- Documentation improvements
- Adding tests
- Simple bug fixes
- Code formatting improvements

---

## 🏆 Recognition

Contributors will be recognized in:

- Project README
- Release notes
- GitHub contributors page

---

## 💬 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Pull Request Comments**: For code review questions

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make NBA predictions better! 🏀🚀
