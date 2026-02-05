# Remote Access Module Tasks

## Overview

The remote-access module provides VNC-based remote viewing, Android app testing via Appium, and distributed session support for GUI application testing. **THIS MODULE IS REQUIRED FOR v1.0.**

**Dependencies**: session, utils (system capabilities)
**Required By**: Android testing (REQUIRED), GUI testing
**Location**: `src/beyond_ralph/integrations/remote_access.py`
**Tests**: `tests/unit/test_remote_access.py`
**LOC**: 0 (not started)
**Priority**: HIGH (REQUIRED for v1.0)

**Key Capabilities**:
- VNC/RDP access for GUI application observation
- Android app testing via Appium
- WSL2 integration with Windows host ADB
- Headless display support (Xvfb, Xvnc)
- noVNC for browser-based remote access

---

## Task: Implement WSL2 Environment Detection

- [x] Planned - 2026-02-03
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03 (92 tests total for module)
- [x] Integration tested - 2026-02-04 (28 integration tests)
- [x] Live tested - 2026-02-04 (WSL2 detection verified)
- [x] Spec compliant - 2026-02-04

**Description**: Detect if running on WSL2 vs native Linux/macOS for Android testing strategy.

**Acceptance Criteria**:
1. `detect_environment()` returns `WSL2`, `LINUX`, `MACOS`, or `WINDOWS`
2. Check `/proc/version` for Microsoft kernel indicators
3. Check `WSL_DISTRO_NAME` environment variable
4. Cache detection result for session
5. Return environment info dict with capabilities
6. Determine Android testing strategy based on environment

**Environment Detection Matrix**:
| Environment | Android Testing | ADB Access |
|-------------|-----------------|------------|
| Native Linux | Local emulator | Direct |
| Native macOS | Local emulator | Direct |
| WSL2 | Windows host | Mirrored networking |
| Windows | Local emulator | Direct |

**Tests**: tests/unit/test_remote_access.py::TestEnvironmentDetection
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/environment-detection/

---

## Task: Implement Windows Host ADB Connectivity

- [x] Planned - 2026-02-03
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (ADB connectivity via SSH verified)
- [x] Spec compliant - 2026-02-04

**Description**: Connect to Windows host ADB from WSL2 via mirrored networking.

**Acceptance Criteria**:
1. `WindowsADBClient` class for WSL2→Windows ADB connection
2. `connect(host_ip, adb_port=5037)` method
3. Verify ADB connectivity before proceeding
4. List available devices on Windows host
5. Forward Appium commands to Windows ADB
6. Handle connection failures with clear error messages

**Configuration Required** (from Interview Phase):
```python
@dataclass
class WindowsHostConfig:
    host_ip: str           # Windows host IP (e.g., "172.x.x.1")
    adb_port: int = 5037   # ADB port on Windows
    emulator_name: str = "emulator-5554"
    verified: bool = False  # Set True after connection test
```

**WSL2 Networking**:
```
WSL2 Instance                    Windows Host
┌─────────────┐                  ┌─────────────┐
│ Beyond Ralph│ ──mirrored net── │ ADB Server  │
│   (Appium)  │                  │  (5037)     │
└─────────────┘                  └──────┬──────┘
                                        │
                                 ┌──────┴──────┐
                                 │   Android   │
                                 │  Emulator   │
                                 └─────────────┘
```

**Tests**: tests/unit/test_remote_access.py::TestWindowsADBConnectivity
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/windows-adb/

---

## Task: Implement Appium Server Management

- [x] Planned - 2026-02-03
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (Node.js v24.13.0, Appium 3.2.0, UiAutomator2 driver verified)
- [x] Spec compliant - 2026-02-04

**Description**: Manage Appium server lifecycle for Android testing.

**Windows Host Setup** (verified 2026-02-04):
- Node.js v24.13.0 (LTS) installed via winget
- Appium 3.2.0 installed globally via npm
- UiAutomator2 driver v6.8.0 installed for Android automation

**Acceptance Criteria**:
1. `AppiumManager` class with server lifecycle methods
2. `start_server(port=4723, adb_host=None)` method
3. `stop_server()` method with clean process termination
4. Auto-install Appium via npm if not present
5. Configure ADB host for WSL2 scenarios
6. Health check endpoint verification
7. Return Appium WebDriver URL

**Appium Configuration**:
```python
@dataclass
class AppiumConfig:
    port: int = 4723
    adb_host: Optional[str] = None  # Windows host IP for WSL2
    log_level: str = "info"
    relaxed_security: bool = True   # For screenshot access
```

**Tests**: tests/unit/test_remote_access.py::TestAppiumManager
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/appium-manager/

---

## Task: Implement Android Emulator Control

- [x] Planned - 2026-02-03
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (emulator info, version, screenshot verified)
- [x] Spec compliant - 2026-02-04

**Description**: Control Android emulator for testing (local or via Windows host).

**Acceptance Criteria**:
1. `AndroidEmulatorManager` class
2. `list_devices()` returns available emulators/devices
3. `start_emulator(name)` for local environments
4. `wait_for_boot(timeout=120)` with boot completion detection
5. `install_apk(path)` for APK installation
6. `take_screenshot()` returns PIL Image
7. Support both local and remote (Windows host) emulators

**Emulator Detection**:
| Method | Environment | Command |
|--------|-------------|---------|
| Local | Linux/macOS | `adb devices` |
| Remote | WSL2 | `adb -H {host_ip} devices` |

**Tests**: tests/unit/test_remote_access.py::TestAndroidEmulatorControl
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/emulator-control/

---

## Task: Implement Interview Phase Android Questions

- [x] Planned - 2026-02-03
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03 (143 tests total for module)
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (WSL2 detection, host IP discovery verified)
- [x] Spec compliant - 2026-02-04

**Description**: Add Android testing questions to interview phase.

**Acceptance Criteria**:
1. Ask "Does this project require Android app testing?"
2. If yes on WSL2: "Please provide Windows host ADB configuration"
3. Required fields: Host IP, ADB port, emulator name
4. Verify connection before proceeding
5. **BLOCK if Android needed but no config** (do not skip silently)
6. Store configuration in knowledge base

**Interview Flow**:
```
Q1: Does this project require Android app testing?
    - Yes
    - No

[If Yes and WSL2 detected]
Q2: Please provide your Windows host configuration:
    - Windows Host IP: ___________
    - ADB Port (default 5037): ___________
    - Emulator Device Name: ___________

[Verify Connection]
Connecting to Windows ADB at {host_ip}:{port}...
✓ Connection successful
✓ Found device: {emulator_name}
```

**Tests**: tests/unit/test_remote_access.py::TestInterviewAndroidQuestions
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/interview-questions/

---

## Task: Implement VNCManager Base Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (Xvfb + x11vnc verified)
- [x] Spec compliant - 2026-02-04

**Description**: VNC session manager for remote GUI access.

**Acceptance Criteria**:
1. `VNCManager` class with session tracking
2. `active_sessions: dict[str, VNCSession]` for tracking
3. Support multiple concurrent VNC sessions
4. Auto-detect available display servers
5. Handle display server priority (Wayland > X11 > Xvfb)
6. Generate secure random passwords (12 chars, alphanumeric)

**Data Classes Required**:
```python
@dataclass
class VNCSession:
    display: str           # X display (e.g., ":99")
    port: int              # VNC port (e.g., 5999)
    password: str          # Auto-generated password
    websocket_port: Optional[int] = None
    resolution: str = "1920x1080"
    pid: Optional[int] = None
```

**Tests**: tests/unit/test_remote_access.py::TestVNCManager
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/base-class/

---

## Task: Implement VNC Session Lifecycle

- [x] Planned - 2024-02-01
- [x] Implemented - 2026-02-03
- [x] Mock tested - 2026-02-03
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (session lifecycle verified)
- [x] Spec compliant - 2026-02-04

**Description**: Start, stop, and manage VNC sessions.

**Acceptance Criteria**:
1. `start_session(display, resolution, websocket)` method
2. Session startup flow:
   - Generate random password
   - Start Xvfb on specified display
   - Start x11vnc on that display
   - Optionally start websockify for browser access
3. `stop_session(display)` method
4. Clean up all processes on session end
5. Return VNCSession with connection details
6. Handle session already exists errors

**Tests**: tests/unit/test_remote_access.py::TestSessionLifecycle
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/session-lifecycle/

---

## Task: Implement SSH-based ADB Connectivity

- [x] Planned - 2026-02-04
- [x] Implemented - 2026-02-04
- [x] Mock tested - 2026-02-04
- [x] Integration tested - 2026-02-04
- [x] Live tested - 2026-02-04 (SSH ADB commands verified against Windows host)
- [x] Spec compliant - 2026-02-04

**Description**: SSH-based ADB as the RECOMMENDED approach for WSL2→Windows Android testing.

**Priority**: HIGH - This is the preferred method over direct network ADB

**Rationale**: Direct network ADB (port 5037) is often blocked by Windows Firewall, even with firewall rules added. SSH-based ADB bypasses this entirely by running ADB commands on the Windows host via SSH.

**Acceptance Criteria**:
1. `SSHADBClient` class for running ADB commands via SSH
2. `run_adb_command(command)` executes ADB on Windows via SSH
3. Pattern: `ssh <host> "C:\Android\platform-tools\adb.exe <command>"`
4. Detect SSH availability during interview phase
5. Fall back to direct network if SSH unavailable
6. Handle SSH connection errors gracefully
7. Support all standard ADB operations (devices, shell, pull, push, install)

**Configuration**:
```python
@dataclass
class SSHADBConfig:
    host_ip: str           # Windows host IP
    ssh_user: str          # SSH username (optional, uses current user)
    adb_path: str = "C:\\Android\\platform-tools\\adb.exe"
    ssh_key: str | None = None  # Path to SSH key (optional)
```

**Usage Pattern**:
```python
# Interview phase detects SSH is available
ssh_client = SSHADBClient(config)

# Run ADB commands via SSH
devices = await ssh_client.list_devices()
# Internally runs: ssh 192.168.68.138 "C:\Android\...\adb.exe devices"

screenshot = await ssh_client.take_screenshot()
# Runs screencap on device, pulls to Windows, then fetches via SSH/SCP
```

**Connectivity Test Order**:
1. Test SSH connectivity to Windows host
2. If SSH works → use SSH-based ADB (preferred)
3. If SSH fails → try direct network ADB (fallback)
4. If both fail → report error with troubleshooting steps

**Tests**: tests/live/test_remote_access_live.py::TestWindowsADBClientLive
**Implementation Agent**: Claude Opus 4.5
**Validation Agent**: Live test verification
**Evidence**: records/remote-access/evidence/ssh-adb/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| WSL2 Environment Detection | [x] | [x] | [x] | [x] | [x] | [x] |
| Windows Host ADB Connectivity | [x] | [x] | [x] | [x] | [x] | [x] |
| **SSH-based ADB Connectivity** | [x] | [x] | [x] | [x] | [x] | [x] |
| Appium Server Management | [x] | [x] | [x] | [x] | [x] | [x] |
| Android Emulator Control | [x] | [x] | [x] | [x] | [x] | [x] |
| Interview Phase Android Questions | [x] | [x] | [x] | [x] | [x] | [x] |
| VNCManager Base Class | [x] | [x] | [x] | [x] | [x] | [x] |
| VNC Session Lifecycle | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 8/8 implemented, 8/8 mock tested, 8/8 integration tested, 8/8 live tested, 8/8 spec compliant

---

## Implementation Priority

This module is **REQUIRED for v1.0** to support:
- Android application testing via Appium
- GUI application testing (desktop apps, Electron, games)
- Remote debugging and observation
- Screenshot-based test validation

**Recommended Implementation Order**:
1. WSL2 Environment Detection (foundation for strategy selection)
2. SSH-based ADB Connectivity (PREFERRED for WSL2 - bypasses firewall)
3. Windows Host ADB Connectivity (fallback if SSH unavailable)
4. Appium Server Management (core Android testing)
5. Android Emulator Control (device management)
6. Interview Phase Android Questions (user configuration)
7. VNCManager Base Class (GUI testing)
8. VNC Session Lifecycle (GUI testing)

**Platform Support**:
| Platform | Android Testing | ADB Method | VNC Server |
|----------|-----------------|------------|------------|
| Linux | Local emulator | Direct | x11vnc |
| macOS | Local emulator | Direct | builtin |
| WSL2 | Windows host | SSH (preferred) or Network | x11vnc |
| Windows | Local emulator | Direct | TightVNC |

**Dependencies**:
- Android SDK (for local testing)
- Node.js + Appium (for mobile testing)
- Xvfb or native display server (for VNC)
- x11vnc for VNC serving
- Optional: websockify for browser access
- **For WSL2 Android testing**:
  - SSH client in WSL2 (usually pre-installed)
  - OpenSSH Server on Windows host (preferred)
  - SSH key authentication configured (recommended)
  - Windows Android SDK at known path (C:\Android recommended)
