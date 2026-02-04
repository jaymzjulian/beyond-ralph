# Beyond Ralph Release Process

This document describes how to create and publish releases of Beyond Ralph.

## Prerequisites

- Python 3.11+ installed
- uv package manager installed
- Git configured with signing (optional)
- PyPI account with token (for publishing)

## Version Numbering

Beyond Ralph follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Pre-release versions: `1.0.0-alpha.1`, `1.0.0-beta.1`, `1.0.0-rc.1`

## Release Checklist

### 1. Prepare the Release

```bash
# Ensure you're on main branch and up to date
git checkout main
git pull origin main

# Run full test suite
uv sync
uv run pytest tests/

# Check linting and types
uv run ruff check src tests
uv run mypy src

# Verify test coverage is >= 90%
uv run pytest tests/unit --cov-fail-under=90
```

### 2. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "X.Y.Z"  # Update this
```

### 3. Update Changelog

If you have a CHANGELOG.md, add release notes:
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature 1
- Feature 2

### Changed
- Change 1

### Fixed
- Bug fix 1
```

### 4. Build the Package

```bash
# Clean previous builds
rm -rf dist/

# Build source distribution and wheel
uv build

# Verify the build
ls -la dist/
# Should show:
# - beyond_ralph-X.Y.Z.tar.gz
# - beyond_ralph-X.Y.Z-py3-none-any.whl
```

### 5. Test the Build

```bash
# Create a fresh test environment
cd /tmp
rm -rf test_release
mkdir test_release && cd test_release
uv venv .venv
source .venv/bin/activate

# Install from wheel
uv pip install /path/to/beyond-ralph/dist/beyond_ralph-X.Y.Z-py3-none-any.whl

# Test CLI
beyond-ralph --help
beyond-ralph info

# Test imports
python -c "from beyond_ralph.core import Orchestrator; print('OK')"

# Cleanup
deactivate
cd /path/to/beyond-ralph
rm -rf /tmp/test_release
```

### 6. Commit and Tag

```bash
# Stage version changes
git add pyproject.toml CHANGELOG.md

# Commit
git commit -m "chore: release v${VERSION}"

# Create annotated tag
git tag -a "v${VERSION}" -m "Release version ${VERSION}"

# Push
git push origin main
git push origin "v${VERSION}"
```

### 7. Publish to PyPI (Optional)

```bash
# Install twine if needed
uv pip install twine

# Upload to PyPI
twine upload dist/*

# Or upload to TestPyPI first
twine upload --repository testpypi dist/*
```

## Post-Release

1. Create GitHub release from the tag
2. Attach wheel and source distribution
3. Write release notes
4. Announce release (if applicable)

## Rollback Process

If a release has critical issues:

```bash
# Delete the tag locally and remotely
git tag -d v${VERSION}
git push origin :refs/tags/v${VERSION}

# Revert the release commit
git revert HEAD

# If published to PyPI, yank the release
# (PyPI doesn't allow deletion, only yanking)
```

## CI/CD Integration

For automated releases, consider:

1. GitHub Actions workflow triggered on tags
2. Automatic version from git tags
3. Automatic PyPI publishing with OIDC

Example workflow trigger:
```yaml
on:
  push:
    tags:
      - 'v*'
```

## Development Builds

For testing without release:

```bash
# Install in development mode
uv pip install -e .

# Or install with dev dependencies
uv sync --all-extras
```

---

*Remember: Beyond Ralph is self-contained. All dependencies must be in pyproject.toml.*
