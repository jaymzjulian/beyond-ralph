# Module 11: System Capabilities - Specification

**Module**: system-capabilities
**Location**: `src/beyond_ralph/utils/system.py`
**Dependencies**: None (foundational)

## Purpose

Detect system capabilities, manage package installation, set up virtual displays.

## Requirements

### R1: Platform Detection
- Detect: Windows, Linux, macOS
- Detect WSL2 specifically
- Detect architecture: x86_64, ARM64

### R2: Package Manager Detection
- Linux: apt, dnf, pacman, zypper, apk
- macOS: brew
- Windows: chocolatey, winget, scoop
- Try all available, use what works

### R3: Passwordless Sudo
- Detect if `sudo -n true` works
- Use liberally if available
- Install system packages freely

### R4: System Package Installation
- Install browsers (Chrome, Firefox, Chromium)
- Install compilers (gcc, clang, make)
- Install databases (PostgreSQL, Redis)
- Install display servers (Xvfb, xvnc, Wayland)
- Try alternatives if one fails

### R5: Virtual Display Setup
- Prefer: Wayland > xvnc > Xvfb
- Auto-setup VNC with random password
- Fall back to alternatives if one fails

## Interface

```python
@dataclass
class SystemCapabilities:
    has_passwordless_sudo: bool
    package_manager: PackageManager
    platform: str
    architecture: str
    is_wsl: bool
    available_tools: list[str]

async def detect_capabilities() -> SystemCapabilities
async def install_package(package: str) -> bool
async def install_browser() -> bool
async def setup_virtual_display() -> VirtualDisplay
```

## Testing Requirements

- Mock subprocess calls
- Test each platform detection
- Test package manager detection
- Test sudo detection
