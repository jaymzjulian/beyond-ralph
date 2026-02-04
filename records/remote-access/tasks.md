# Remote Access Module Tasks

## Overview

The remote-access module provides VNC-based remote viewing and distributed session support for GUI application testing. **THIS MODULE IS PLANNED BUT NOT YET STARTED.**

**Dependencies**: session, utils (system capabilities)
**Required By**: GUI testing (optional)
**Location**: `src/beyond_ralph/integrations/remote_access.py`
**Tests**: `tests/unit/test_remote_access.py`
**LOC**: 0 (not started)
**Priority**: LOW (optional for v1.0)

---

## Task: Implement VNCManager Base Class

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

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
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

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

## Task: Implement Display Server Detection

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Detect and select best available display server.

**Acceptance Criteria**:
1. `_detect_display_server()` method
2. Priority order:
   - Wayland (WAYLAND_DISPLAY env)
   - X11 native (DISPLAY env)
   - Xvfb (if installed)
   - Xvnc (if installed)
3. Return server type and display string
4. Raise `DisplayNotAvailableError` if none available
5. Support fallback to starting Xvfb
6. Cache detection result

**Display Server Matrix**:
| Server Type | Env Variable | Binary | Priority |
|-------------|--------------|--------|----------|
| Wayland | WAYLAND_DISPLAY | - | 1 (highest) |
| X11 | DISPLAY | - | 2 |
| Xvfb | - | Xvfb | 3 |
| Xvnc | - | Xvnc | 4 |

**Tests**: tests/unit/test_remote_access.py::TestDisplayDetection
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/display-detection/

---

## Task: Implement VNC Dependencies Installation

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Auto-install VNC dependencies using system package manager.

**Acceptance Criteria**:
1. `_install_vnc_deps()` method
2. Install required packages:
   - xvfb: Virtual framebuffer
   - x11vnc: VNC server
   - websockify: Browser access (optional)
3. Use passwordless sudo if available
4. Support multiple package managers (apt, dnf, brew)
5. Return success/failure status
6. Log installation attempts

**Package Names by Platform**:
| Package | apt | dnf | brew |
|---------|-----|-----|------|
| xvfb | xvfb | xorg-x11-server-Xvfb | - |
| x11vnc | x11vnc | x11vnc | x11vnc |
| websockify | python3-websockify | python3-websockify | websockify |

**Tests**: tests/unit/test_remote_access.py::TestDependencyInstall
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/dependency-install/

---

## Task: Implement noVNC Browser Access

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Enable browser-based VNC access via websockify.

**Acceptance Criteria**:
1. `start_novnc(vnc_port, websocket_port)` method
2. Start websockify proxy
3. Return URL for browser access
4. Default websocket port: 6080
5. Support custom HTML path for noVNC
6. Clean up websockify on session stop

**Browser Access URL Format**:
```
http://localhost:{websocket_port}/vnc.html?autoconnect=true
```

**Tests**: tests/unit/test_remote_access.py::TestNoVNCAccess
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/novnc-access/

---

## Task: Implement Secure Password Generation

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Generate cryptographically secure VNC passwords.

**Acceptance Criteria**:
1. `_generate_password()` method using `secrets` module
2. 12-character URL-safe alphanumeric passwords
3. Unique password per session
4. **CRITICAL**: Passwords logged as `[REDACTED]` in persistent logs
5. Passwords shown in stdout only (ephemeral)
6. Support password file for VNC server

**Security Requirements**:
```python
import secrets

def _generate_password(self) -> str:
    """Generate secure VNC password."""
    return secrets.token_urlsafe(9)  # ~12 characters
```

**Tests**: tests/unit/test_remote_access.py::TestPasswordGeneration
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/password-generation/

---

## Task: Implement GUI Testing Auto-Setup

- [x] Planned - 2024-02-01
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Auto-setup VNC when GUI testing starts.

**Acceptance Criteria**:
1. `setup_gui_testing(test_context)` method
2. Automatically start VNC session
3. Configure resolution based on test requirements
4. Enable websocket for browser access
5. Notify user via notifications module with connection info
6. Return VNCSession for test use

**Integration with Testing Module**:
```python
async def setup_gui_testing(test_context: dict) -> VNCSession:
    """Auto-setup VNC for GUI testing."""
    vnc = VNCManager()
    session = await vnc.start_session(
        display=":99",
        resolution="1920x1080",
        websocket=True
    )
    await notifications.notify(
        type=NotificationType.INFO,
        title="GUI Testing Started",
        message=f"VNC available at localhost:{session.port}",
        context={"vnc_port": session.port, "vnc_password": session.password}
    )
    return session
```

**Tests**: tests/unit/test_remote_access.py::TestGUITestingSetup
**Implementation Agent**: TBD
**Validation Agent**: TBD
**Evidence**: records/remote-access/evidence/gui-testing-setup/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| VNCManager Base Class | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| VNC Session Lifecycle | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Display Server Detection | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| VNC Dependencies Installation | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| noVNC Browser Access | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Secure Password Generation | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| GUI Testing Auto-Setup | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |

**Overall Progress**: 0/7 implemented, 0/7 mock tested, 0/7 integration tested, 0/7 live tested, 0/7 spec compliant

---

## Implementation Priority

This module is **OPTIONAL for v1.0** but essential for:
- GUI application testing (desktop apps, Electron, games)
- Remote debugging and observation
- Screenshot-based test validation

**Recommended Implementation Order**:
1. Secure Password Generation (foundation)
2. Display Server Detection (needed first)
3. VNCManager Base Class (core class)
4. VNC Session Lifecycle (primary functionality)
5. VNC Dependencies Installation (auto-setup)
6. noVNC Browser Access (convenience)
7. GUI Testing Auto-Setup (integration)

**Platform Support**:
| Platform | VNC Server | Display Server | Notes |
|----------|------------|----------------|-------|
| Linux | x11vnc | Xvfb/native | Primary support |
| macOS | builtin | XQuartz | Requires XQuartz install |
| Windows | TightVNC | native | WSL2 via vcxsrv |
| WSL2 | x11vnc | Xvfb | Requires VcXsrv on Windows |

**Dependencies**:
- Requires Xvfb or native display server
- Requires x11vnc for VNC serving
- Optional: websockify for browser access
- Optional: noVNC HTML files for web UI
