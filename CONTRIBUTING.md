# Contributing to MeritScore

## Development Setup

```bash
git clone https://github.com/warvis/warvis-hackerton.git
cd warvis-hackerton
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Locally

```bash
# Start Docker container
docker-compose up -d

# Run tests
pytest python/ -q

# Check linting
ruff check python/
forge fmt --check
```

## Code Style

- **Python**: PEP8 (enforced by ruff)
- **Solidity**: EIP-8 (enforced by forge fmt)
- **Git commits**: Semantic versioning (feat:, fix:, docs:, refactor:)

## PR Workflow

1. Create feature branch from `main`
2. Make changes + test locally
3. Push branch + open PR
4. Wait for CI/CD (lint + test + security)
5. Merge after approval

## Testing Requirements

- All pytest tests must pass (`23/23 PASS`)
- No ruff linting violations
- No hardcoded secrets or API keys
- Comments for complex logic

## Deployment Checklist

Before merging to main:
- [ ] All tests passing
- [ ] Linting clean
- [ ] Documentation updated
- [ ] No security issues detected
- [ ] Compatible with both MOCK_MODE=true and false

## Known Issues

- KeeperHub integration pending OG_PRIVATE_KEY setup
- 0G Compute tests require valid wallet + testnet faucet

## Questions?

Open an issue or contact the warvis team.
