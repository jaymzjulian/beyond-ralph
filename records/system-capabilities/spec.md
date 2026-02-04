# Module 8: System Capabilities - Specification

> System Detection: Tools, package managers, and permissions.

---

## Overview

The System Capabilities module detects system configuration, available tools, and permissions. It enables autonomous tool installation when needed.

**Key Principle**: Use sudo liberally if available. Install anything that might help.

---

## Location

`src/beyond_ralph/utils/system.py`

---

## Components

### 8.1 System Detector

**Purpose**: Detect system capabilities and available tools.

**Interface**:
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SystemCapabilities:
    """System capabilities and configuration."""
    has_passwordless_sudo: bool
    package_manager: Optional[str]  # apt, dnf, pacman, brew, etc.
    available_tools: dict[str, str]  # tool -> version
    python_version: str
    platform: str  # linux, darwin, windows
    architecture: str  # x86_64, arm64

class SystemDetector:
    """Detects system capabilities and available tools."""

    def detect(self) -> SystemCapabilities:
        """Detect all system capabilities.

        Flow:
            1. Detect platform and architecture
            2. Detect Python version
            3. Detect package manager
            4. Check for passwordless sudo
            5. Detect available tools
        """

    def detect_passwordless_sudo(self) -> bool:
        """Check if passwordless sudo is available.

        Runs: sudo -n true
        Returns True if exits with 0.

        NOTE: If available, USE IT LIBERALLY.
        """

    def detect_package_manager(self) -> Optional[str]:
        """Detect system package manager.

        Checks for (in order):
            - apt (Debian/Ubuntu)
            - dnf (Fedora)
            - yum (RHEL/CentOS)
            - pacman (Arch)
            - brew (macOS)
            - apk (Alpine)
            - zypper (openSUSE)
        """

    def detect_available_tools(self) -> dict[str, str]:
        """Detect available development tools.

        Checks 40+ common tools:

        Build:
            - gcc, g++, clang, clang++
            - make, cmake, ninja
            - pkg-config

        Python:
            - python, python3
            - pip, pip3
            - uv
            - ruff, mypy, black, isort
            - pytest, coverage

        JavaScript:
            - node, npm, npx
            - yarn, pnpm
            - bun, deno

        Go:
            - go

        Rust:
            - cargo, rustc, rustup
            - cargo-clippy

        Java:
            - java, javac
            - maven, gradle

        Ruby:
            - ruby, gem, bundle

        General:
            - git
            - docker, docker-compose
            - curl, wget
            - jq, yq
            - vim, nano

        Returns:
            Dict of {tool_name: version_string}
        """

    def _get_tool_version(self, tool: str) -> Optional[str]:
        """Get version of a tool.

        Tries common version flags:
            --version, -V, version, -v
        """
```

---

### 8.2 System Installer

**Purpose**: Install system packages and tools.

**Interface**:
```python
class SystemInstaller:
    """Installs system packages and tools."""

    def __init__(self, capabilities: SystemCapabilities) -> None:
        """Initialize with detected capabilities."""
        self.capabilities = capabilities
        self.has_sudo = capabilities.has_passwordless_sudo
        self.pkg_manager = capabilities.package_manager

    def install_system_package(self, package: str) -> bool:
        """Install system package using detected package manager.

        Uses sudo if available - be LIBERAL with system installs.

        Commands by package manager:
            apt: sudo apt install -y {package}
            dnf: sudo dnf install -y {package}
            pacman: sudo pacman -S --noconfirm {package}
            brew: brew install {package}
            apk: sudo apk add {package}

        Returns:
            True if installed successfully.
        """

    def install_multiple_packages(self, packages: list[str]) -> dict[str, bool]:
        """Install multiple packages.

        Returns:
            Dict of {package: success} for each package.
        """

    def install_browser_testing_deps(self) -> bool:
        """Install browser testing dependencies.

        Packages:
            - chromium or google-chrome-stable
            - firefox
            - xvfb (for headless)

        Also runs: playwright install
        """

    def install_build_tools(self) -> bool:
        """Install build tools.

        Packages (apt example):
            - build-essential
            - cmake
            - pkg-config
            - libssl-dev
            - libffi-dev
        """

    def install_python_tools(self) -> bool:
        """Install Python development tools.

        Via pip/uv:
            - ruff
            - mypy
            - pytest
            - pytest-cov
            - black
            - isort
        """

    def _run_install_command(self, command: str) -> bool:
        """Run install command with error handling."""
```

---

## Package Manager Detection

| Package Manager | Distro | Detection |
|-----------------|--------|-----------|
| apt | Debian, Ubuntu | `which apt` |
| dnf | Fedora | `which dnf` |
| yum | RHEL, CentOS | `which yum` |
| pacman | Arch | `which pacman` |
| brew | macOS | `which brew` |
| apk | Alpine | `which apk` |
| zypper | openSUSE | `which zypper` |

---

## Tool Categories

| Category | Tools |
|----------|-------|
| Build | gcc, g++, clang, make, cmake |
| Python | python, pip, uv, ruff, mypy, pytest |
| JavaScript | node, npm, yarn, pnpm |
| Go | go |
| Rust | cargo, rustc, clippy |
| Java | java, javac, maven |
| General | git, docker, curl, jq |

---

## Philosophy

**Be LIBERAL with installations.**

If something might help, install it:
- User gave permission during interview
- We're in a contained environment
- More tools = better debugging

**Don't ask, just install** (after interview phase):
```python
# If we need a linter and don't have it:
if "ruff" not in capabilities.available_tools:
    installer.install_system_package("ruff")
    # Or via pip: subprocess.run(["pip", "install", "ruff"])
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 12 (Utils) | Logging, subprocess helpers |

---

## Error Handling

```python
class SystemError(BeyondRalphError):
    """System-related errors."""

class PackageInstallError(SystemError):
    """Package installation failed."""

class SudoRequiredError(SystemError):
    """Operation requires sudo but not available."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Detection logic (mocked) |
| Integration tests | Real system detection |
| Live tests | Package installation |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
