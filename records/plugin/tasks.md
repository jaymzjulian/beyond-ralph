# Plugin Module Tasks

## Overview

The plugin module provides the complete `.claude/` directory structure for native Claude Code integration.

**Dependencies**: skills, hooks
**Required By**: End users
**Location**: `.claude/`
**Tests**: Integrated with skills and hooks tests
**LOC**: YAML configuration files

---

## Task: Create Plugin Directory Structure

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (plugin installed and working)
- [x] Spec compliant - 2026-02-03

**Description**: Create complete `.claude/` directory structure.

**Acceptance Criteria**:
1. `.claude/` root directory
2. `.claude/skills/` for skill definitions
3. `.claude/hooks/` for hook definitions
4. Proper file permissions
5. Git-tracked (not in .gitignore)

**Structure**:
```
.claude/
├── skills/
│   ├── beyond-ralph.yaml
│   ├── beyond-ralph-start.yaml
│   ├── beyond-ralph-resume.yaml
│   └── beyond-ralph-pause.yaml
└── hooks/
    ├── stop.yaml
    └── quota-check.yaml
```

**Tests**: Integrated
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/plugin/evidence/directory-structure/

---

## Task: Register Entry Points in pyproject.toml

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (plugin installed and working)
- [x] Spec compliant - 2026-02-03

**Description**: Configure CLI entry points in pyproject.toml.

**Acceptance Criteria**:
1. `beyond-ralph` main CLI command
2. `br-quota` quota check command
3. `br-live-tests` live testing command
4. Entry points work after `uv pip install .`
5. Dependencies properly declared

**Entry Points**:
```toml
[project.scripts]
beyond-ralph = "beyond_ralph.cli:main"
br-quota = "beyond_ralph.utils.quota_checker:main"
br-live-tests = "beyond_ralph.testing.claude_driver:main"
```

**Tests**: Integrated
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/plugin/evidence/entry-points/

---

## Task: Ensure Self-Contained Packaging

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (plugin installed and working)
- [x] Spec compliant - 2026-02-03

**Description**: Verify plugin is completely self-contained.

**Acceptance Criteria**:
1. All dependencies in pyproject.toml
2. No references to external tools (SuperClaude, etc.)
3. Works on clean system with `uv pip install .`
4. All skills/hooks bundled in package
5. Documentation doesn't assume external tooling
6. Tests don't require external services

**Verification Commands**:
```bash
# Clean install test
uv pip install . --force-reinstall
beyond-ralph --version
br-quota --help
```

**Tests**: Integrated
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/plugin/evidence/self-contained/

---

## Task: Document Plugin Installation

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (plugin installed and working)
- [x] Spec compliant - 2026-02-03

**Description**: Document how to install and use the plugin.

**Acceptance Criteria**:
1. Installation instructions in README
2. Quick start guide
3. Configuration options documented
4. Troubleshooting section
5. Examples of usage

**Files**:
- `README.md` (updated)
- `docs/user/installation.md`
- `docs/user/quickstart.md`

**Tests**: Manual review
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/plugin/evidence/documentation/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| Plugin Directory Structure | [x] | [x] | [x] | [x] | [x] | [x] |
| Entry Points in pyproject.toml | [x] | [x] | [x] | [x] | [x] | [x] |
| Self-Contained Packaging | [x] | [x] | [x] | [x] | [x] | [x] |
| Plugin Installation Docs | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 4/4 implemented, 4/4 mock tested, 4/4 integration tested, 4/4 live tested, 4/4 spec compliant
