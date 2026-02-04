# Module 14: Remote Access - Specification

> VNC Access: Enable remote viewing of GUI applications during testing.

---

## Overview

The Remote Access module provides VNC-based remote viewing capabilities for GUI application testing. Per interview decision, VNC sessions are auto-configured with random passwords for security.

**Key Principle**: Auto-setup VNC for seamless remote viewing during GUI testing.

---

## Location

`src/beyond_ralph/integrations/remote_access.py`

---

## Components

### 14.1 VNC Manager

**Purpose**: Manage VNC sessions for remote access to GUI applications.

**Interface**:
```python
from dataclasses import dataclass
from typing import Optional
import secrets

@dataclass
class VNCSession:
    """Active VNC session."""
    display: str           # X display (e.g., ":99")
    port: int              # VNC port (e.g., 5999)
    password: str          # Auto-generated password
    websocket_port: Optional[int] = None  # For noVNC web access
    resolution: str = "1920x1080"
    pid: Optional[int] = None

class VNCManager:
    """Manages VNC sessions for remote access."""

    def __init__(self) -> None:
        """Initialize VNC manager."""
        self.active_sessions: dict[str, VNCSession] = {}

    async def start_session(
        self,
        display: str = ":99",
        resolution: str = "1920x1080",
        websocket: bool = False
    ) -> VNCSession:
        """Start a VNC session.

        Args:
            display: X display number (e.g., ":99").
            resolution: Screen resolution (e.g., "1920x1080").
            websocket: Enable websockify for browser access.

        Returns:
            VNCSession with connection details.

        Flow:
            1. Generate random password (12 characters)
            2. Start Xvfb on specified display
            3. Start x11vnc on that display
            4. Optionally start websockify for browser access
            5. Return connection info

        Raises:
            VNCError: If VNC setup fails.
        """

    async def stop_session(self, display: str) -> None:
        """Stop a VNC session.

        Args:
            display: Display to stop.

        Cleans up:
            - x11vnc process
            - websockify process (if running)
            - Xvfb process
        """

    def _generate_password(self) -> str:
        """Generate secure random password.

        Returns:
            12-character alphanumeric password.
        """
        return secrets.token_urlsafe(9)  # ~12 characters

    def get_connection_info(self, display: str) -> dict:
        """Get connection information for users.

        Args:
            display: Display to get info for.

        Returns:
            Dict with host, port, password for VNC client.
        """

    def _detect_display_server(self) -> str:
        """Detect available display server.

        Priority:
            1. Wayland (WAYLAND_DISPLAY env)
            2. X11 native (DISPLAY env)
            3. Xvfb (if installed)
            4. xvnc (if installed)

        Returns:
            Best available display server type.
        """

    async def _install_vnc_deps(self) -> bool:
        """Install VNC dependencies if needed.

        Packages:
            - xvfb: Virtual framebuffer
            - x11vnc: VNC server
            - websockify: For browser access (optional)

        Uses sudo if available.
        """
```

---

## Display Server Detection

Per interview decision, detect and try alternatives:

```python
DISPLAY_SERVERS = [
    ("wayland", "WAYLAND_DISPLAY", None),      # Native Wayland
    ("x11", "DISPLAY", None),                   # Native X11
    ("xvfb", None, "Xvfb"),                     # Virtual framebuffer
    ("xvnc", None, "Xvnc"),                     # VNC-based X server
]

def detect_available_display() -> tuple[str, str]:
    """Detect best available display server.

    Returns:
        Tuple of (server_type, display_string).

    Tries each in priority order, falls back to starting Xvfb.
    """
    # Check environment for native display
    for server_type, env_var, binary in DISPLAY_SERVERS:
        if env_var and os.environ.get(env_var):
            return server_type, os.environ[env_var]

    # Check for available binaries
    for server_type, env_var, binary in DISPLAY_SERVERS:
        if binary and shutil.which(binary):
            return server_type, None  # Will need to start

    raise DisplayNotAvailableError("No display server available")
```

---

## Auto-Setup Flow

When GUI testing starts, VNC is automatically configured:

```python
async def setup_gui_testing(test_context: dict) -> VNCSession:
    """Auto-setup VNC for GUI testing.

    Args:
        test_context: Testing context with app info.

    Returns:
        VNCSession for remote viewing.
    """
    vnc = VNCManager()

    # Start VNC session
    session = await vnc.start_session(
        display=":99",
        resolution="1920x1080",
        websocket=True  # Enable browser access
    )

    # Log connection info
    logger.info(
        "VNC available at localhost:%d (password: %s)",
        session.port,
        session.password
    )

    # Notify user via notifications module
    await notifications.notify(
        type=NotificationType.INFO,
        title="GUI Testing Started",
        message=f"VNC available at localhost:{session.port}",
        context={
            "vnc_port": session.port,
            "vnc_password": session.password,
            "websocket_port": session.websocket_port
        }
    )

    return session
```

---

## Security

### Password Generation

All VNC passwords are auto-generated using `secrets` module:

```python
import secrets

def generate_vnc_password() -> str:
    """Generate cryptographically secure VNC password.

    - 12 characters
    - URL-safe alphanumeric
    - Unique per session
    """
    return secrets.token_urlsafe(9)
```

### Password Logging

**CRITICAL**: Passwords are logged as `[REDACTED]` in all persistent logs:

```python
# In-memory only for user display
logger.info("VNC started on :%d", port)
print(f"Password: {password}")  # To stdout only

# Persistent logs show redacted
file_logger.info("VNC started on :%d with password [REDACTED]", port)
```

---

## Platform Support

| Platform | VNC Server | Display Server | Notes |
|----------|------------|----------------|-------|
| Linux | x11vnc | Xvfb/native | Primary support |
| macOS | builtin | native X11 | Via XQuartz |
| Windows | TightVNC | native | WSL2 via vcxsrv |
| WSL2 | x11vnc | Xvfb | Requires VcXsrv on Windows side |

---

## Browser Access (noVNC)

For browser-based VNC access via websockify:

```python
async def start_novnc(
    vnc_port: int,
    websocket_port: int = 6080
) -> str:
    """Start noVNC web interface.

    Args:
        vnc_port: VNC server port.
        websocket_port: Websocket port for browser access.

    Returns:
        URL for browser access.
    """
    # Start websockify
    proc = await asyncio.create_subprocess_exec(
        "websockify",
        "--web=/usr/share/novnc",
        f"{websocket_port}",
        f"localhost:{vnc_port}"
    )

    return f"http://localhost:{websocket_port}/vnc.html"
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 8 (System) | Package installation, capability detection |
| Module 11 (Notifications) | Alerting user about VNC availability |
| Module 12 (Utils) | Logging, subprocess management |
| External: xvfb | Virtual framebuffer |
| External: x11vnc | VNC server |
| External: websockify | Browser access (optional) |

---

## Error Handling

```python
class RemoteAccessError(BeyondRalphError):
    """Remote access errors."""

class VNCError(RemoteAccessError):
    """VNC-specific errors."""

class DisplayNotAvailableError(RemoteAccessError):
    """No display server available."""

class VNCStartError(VNCError):
    """Failed to start VNC server."""

class VNCPasswordError(VNCError):
    """Password configuration failed."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Password generation, display detection |
| Integration tests | VNC session lifecycle (mock) |
| Live tests | Real VNC connections (requires display) |

---

## Checkboxes

- [x] Planned
- [ ] Implemented
- [ ] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
