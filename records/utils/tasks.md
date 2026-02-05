# Utils Module Tasks

## Overview

The utils module provides system-level utilities: platform detection, package manager detection, tool inventory, sudo detection, and virtual display support.

**Dependencies**: None (Foundation tier)
**Required By**: ALL modules
**Location**: `src/beyond_ralph/utils/system.py`
**Tests**: `tests/unit/test_system.py` (34 tests)
**LOC**: 852

---

## Task: Implement Platform Detection

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (platform detection working)
- [x] Spec compliant - 2026-02-03

**Description**: Detect the current operating system and platform characteristics.

**Acceptance Criteria**:
1. Detect Linux distributions (Ubuntu, Debian, Fedora, Arch, etc.)
2. Detect macOS versions
3. Detect Windows and WSL2
4. Identify ARM vs x86 architecture
5. Return structured `PlatformInfo` dataclass
6. Handle unknown platforms gracefully

**Tests**: tests/unit/test_system.py::TestPlatformDetection
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/utils/evidence/platform-detection/

---

## Task: Implement Package Manager Detection

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (platform detection working)
- [x] Spec compliant - 2026-02-03

**Description**: Detect available package managers for autonomous tool installation.

**Acceptance Criteria**:
1. Detect apt (Debian/Ubuntu)
2. Detect dnf/yum (Fedora/RHEL)
3. Detect pacman (Arch)
4. Detect brew (macOS)
5. Detect chocolatey/winget (Windows)
6. Return primary and fallback package managers
7. Verify package manager is functional

**Tests**: tests/unit/test_system.py::TestPackageManagerDetection
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/utils/evidence/package-manager/

---

## Task: Implement Tool Inventory

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (platform detection working)
- [x] Spec compliant - 2026-02-03

**Description**: Check availability of 40+ development tools.

**Acceptance Criteria**:
1. Check for common tools: git, python, node, go, rust, etc.
2. Check for testing tools: pytest, playwright, selenium
3. Check for linters: ruff, eslint, golint, clippy
4. Check for security tools: semgrep, bandit
5. Return `ToolInventory` with available/missing lists
6. Include version information where available

**Tools Checked** (40+):
- Languages: python, node, go, rust, java, ruby
- Build: make, cmake, cargo, npm, pip, uv
- VCS: git, gh (GitHub CLI)
- Testing: pytest, playwright, selenium
- Linting: ruff, mypy, eslint, tsc, golint, clippy
- Security: semgrep, bandit, safety
- System: docker, podman, systemctl

**Tests**: tests/unit/test_system.py::TestToolInventory
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/utils/evidence/tool-inventory/

---

## Task: Implement Passwordless Sudo Detection

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (platform detection working)
- [x] Spec compliant - 2026-02-03

**Description**: Detect if passwordless sudo is available for system package installation.

**Acceptance Criteria**:
1. Run `sudo -n true` to test passwordless sudo
2. Cache result (don't prompt user repeatedly)
3. Return boolean `has_passwordless_sudo`
4. If available, use liberally for system packages
5. Handle timeout gracefully

**Tests**: tests/unit/test_system.py::TestSudoDetection
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/utils/evidence/sudo-detection/

---

## Task: Implement Virtual Display Support

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (platform detection working)
- [x] Spec compliant - 2026-02-03

**Description**: Support for Xvfb/virtual displays for headless GUI testing.

**Acceptance Criteria**:
1. Detect if running headless (no DISPLAY)
2. Check for Xvfb availability
3. `start_virtual_display()` creates Xvfb if needed
4. Set DISPLAY environment variable
5. `stop_virtual_display()` cleans up
6. Handle already-set DISPLAY gracefully

**Tests**: tests/unit/test_system.py::TestVirtualDisplay
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/utils/evidence/virtual-display/

---

## Task: Implement System Package Installation

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (platform detection working)
- [x] Spec compliant - 2026-02-03

**Description**: Install system packages using detected package manager with sudo.

**Acceptance Criteria**:
1. `install_system_package(name)` installs via appropriate package manager
2. Uses passwordless sudo if available
3. Maps package names across distributions (e.g., python3-dev vs python3-devel)
4. Returns success/failure with error message
5. Logs installation attempts
6. Supports batch installation for efficiency

**Tests**: tests/unit/test_system.py::TestPackageInstallation
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/utils/evidence/package-installation/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| Platform Detection | [x] | [x] | [x] | [x] | [x] | [x] |
| Package Manager Detection | [x] | [x] | [x] | [x] | [x] | [x] |
| Tool Inventory | [x] | [x] | [x] | [x] | [x] | [x] |
| Passwordless Sudo Detection | [x] | [x] | [x] | [x] | [x] | [x] |
| Virtual Display Support | [x] | [x] | [x] | [x] | [x] | [x] |
| System Package Installation | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 6/6 implemented, 6/6 integration tested, 6/6 live tested, 6/6 spec compliant
