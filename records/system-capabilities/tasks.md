# System Capabilities Module Tasks

## Overview

The system-capabilities module provides system package installation, browser testing dependencies, and build tools setup.

**Dependencies**: utils
**Required By**: testing
**Location**: `src/beyond_ralph/utils/system.py` (integrated)
**Tests**: `tests/unit/test_system.py` (integrated, 20+ tests)
**LOC**: Integrated in utils module

---

## Task: Implement install_system_package Function

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Install system packages using detected package manager.

**Acceptance Criteria**:
1. `install_system_package(name)` installs package
2. Auto-detect package manager (apt, dnf, pacman, brew)
3. Use passwordless sudo if available
4. Handle package name mapping across distros
5. Return installation result
6. Log all installation attempts

**Tests**: tests/unit/test_system.py::TestInstallSystemPackage
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/system-capabilities/evidence/install-package/

---

## Task: Implement install_browser_testing_deps Function

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Install browser testing dependencies (browsers, drivers).

**Acceptance Criteria**:
1. `install_browser_testing_deps()` installs:
   - Chromium/Chrome
   - Firefox
   - Playwright browsers
   - WebDriver executables
2. Handle headless vs headed mode
3. Install Xvfb for headless testing
4. Verify installations work
5. Support multiple platforms

**Tests**: tests/unit/test_system.py::TestInstallBrowserDeps
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/system-capabilities/evidence/browser-deps/

---

## Task: Implement install_build_tools Function

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Install build tools for native extensions.

**Acceptance Criteria**:
1. `install_build_tools()` installs:
   - gcc, g++, make
   - cmake
   - pkg-config
   - Development headers (python3-dev, etc.)
2. Platform-specific package names
3. Verify tools are functional
4. Log installation progress

**Tests**: tests/unit/test_system.py::TestInstallBuildTools
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/system-capabilities/evidence/build-tools/

---

## Task: Implement detect_available_tools Function

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Detect available development tools on the system.

**Acceptance Criteria**:
1. `detect_available_tools()` returns `ToolInventory`
2. Check 40+ common development tools
3. Include version information
4. Categorize by type (language, build, test, etc.)
5. Cache results for performance
6. Refresh on demand

**Tools Categories**:
- Languages: python, node, go, rust, java, ruby
- Build: make, cmake, cargo, npm, pip, uv
- Testing: pytest, playwright, selenium, jest
- Linting: ruff, eslint, golint, clippy
- Security: semgrep, bandit, safety
- System: docker, systemctl, sudo

**Tests**: tests/unit/test_system.py::TestDetectTools
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/system-capabilities/evidence/detect-tools/

---

## Task: Implement install_linter_tools Function

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Install linting and code quality tools.

**Acceptance Criteria**:
1. `install_linter_tools(languages)` installs:
   - Python: ruff, mypy, bandit
   - JavaScript: eslint, prettier
   - Go: golint, staticcheck
   - Rust: clippy
2. Install via appropriate package managers
3. Configure tools with sensible defaults
4. Verify tools are functional

**Tests**: tests/unit/test_system.py::TestInstallLinters
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/system-capabilities/evidence/linter-tools/

---

## Task: Implement install_security_tools Function

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Install security scanning tools.

**Acceptance Criteria**:
1. `install_security_tools()` installs:
   - Semgrep with OWASP rules
   - Bandit (Python security)
   - Safety (dependency vulnerabilities)
   - detect-secrets
   - trivy (container scanning)
2. Download rulesets
3. Verify tools are functional
4. Configure for CI integration

**Tests**: tests/unit/test_system.py::TestInstallSecurityTools
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/system-capabilities/evidence/security-tools/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| install_system_package | [x] | [x] | [x] | [x] | [x] | [x] |
| install_browser_testing_deps | [x] | [x] | [x] | [x] | [x] | [x] |
| install_build_tools | [x] | [x] | [x] | [x] | [x] | [x] |
| detect_available_tools | [x] | [x] | [x] | [x] | [x] | [x] |
| install_linter_tools | [x] | [x] | [x] | [x] | [x] | [x] |
| install_security_tools | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 6/6 implemented, 6/6 mock tested, 6/6 integration tested, 6/6 live tested, 6/6 spec compliant
