"""System utilities for Beyond Ralph.

Includes detection of system capabilities like passwordless sudo,
package managers, and available tools.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class PackageManager(Enum):
    """Detected system package managers."""

    APT = "apt"          # Debian/Ubuntu
    DNF = "dnf"          # Fedora/RHEL
    YUM = "yum"          # Older RHEL/CentOS
    PACMAN = "pacman"    # Arch
    BREW = "brew"        # macOS
    CHOCO = "choco"      # Windows
    APK = "apk"          # Alpine
    ZYPPER = "zypper"    # openSUSE
    UNKNOWN = "unknown"


@dataclass
class SystemCapabilities:
    """Detected system capabilities."""

    has_passwordless_sudo: bool
    package_manager: PackageManager
    platform: str
    architecture: str
    available_tools: list[str]


def detect_passwordless_sudo() -> bool:
    """Check if sudo is available and doesn't require a password.

    Returns:
        True if `sudo -n true` succeeds (passwordless sudo available)
    """
    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def detect_package_manager() -> PackageManager:
    """Detect the system's package manager.

    Returns:
        The detected PackageManager enum value
    """
    # Check each package manager in order of commonality
    checks = [
        (PackageManager.APT, ["apt", "--version"]),
        (PackageManager.DNF, ["dnf", "--version"]),
        (PackageManager.PACMAN, ["pacman", "--version"]),
        (PackageManager.BREW, ["brew", "--version"]),
        (PackageManager.APK, ["apk", "--version"]),
        (PackageManager.ZYPPER, ["zypper", "--version"]),
        (PackageManager.YUM, ["yum", "--version"]),
        (PackageManager.CHOCO, ["choco", "--version"]),
    ]

    for pm, cmd in checks:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
                return pm
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

    return PackageManager.UNKNOWN


def get_platform() -> str:
    """Get the current platform."""
    return sys.platform


def get_architecture() -> str:
    """Get the CPU architecture."""
    import platform
    return platform.machine()


def detect_available_tools() -> list[str]:
    """Detect commonly useful tools that are already installed."""
    tools_to_check = [
        "git", "curl", "wget", "docker", "podman",
        "python", "python3", "node", "npm", "yarn", "pnpm",
        "gcc", "clang", "make", "cmake",
        "ruby", "gem", "cargo", "rustc", "go",
        "java", "javac", "mvn", "gradle",
        "psql", "mysql", "sqlite3", "redis-cli",
        "chromium", "chromium-browser", "google-chrome", "firefox",
        "ffmpeg", "convert", "xvfb-run",
    ]

    available = []
    for tool in tools_to_check:
        if shutil.which(tool):
            available.append(tool)

    return available


def get_system_capabilities() -> SystemCapabilities:
    """Detect all system capabilities.

    Returns:
        SystemCapabilities with all detected information
    """
    return SystemCapabilities(
        has_passwordless_sudo=detect_passwordless_sudo(),
        package_manager=detect_package_manager(),
        platform=get_platform(),
        architecture=get_architecture(),
        available_tools=detect_available_tools(),
    )


def install_system_package(package: str, package_manager: PackageManager | None = None) -> bool:
    """Install a system package using sudo.

    Args:
        package: Package name to install
        package_manager: Optional specific package manager to use

    Returns:
        True if installation succeeded
    """
    if package_manager is None:
        package_manager = detect_package_manager()

    commands: dict[PackageManager, list[str]] = {
        PackageManager.APT: ["sudo", "apt", "install", "-y", package],
        PackageManager.DNF: ["sudo", "dnf", "install", "-y", package],
        PackageManager.YUM: ["sudo", "yum", "install", "-y", package],
        PackageManager.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", package],
        PackageManager.BREW: ["brew", "install", package],  # brew doesn't need sudo
        PackageManager.APK: ["sudo", "apk", "add", package],
        PackageManager.ZYPPER: ["sudo", "zypper", "install", "-y", package],
        PackageManager.CHOCO: ["choco", "install", "-y", package],  # choco doesn't need sudo
    }

    cmd = commands.get(package_manager)
    if not cmd:
        return False

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def install_multiple_packages(packages: list[str]) -> dict[str, bool]:
    """Install multiple system packages.

    Args:
        packages: List of package names to install

    Returns:
        Dict mapping package name to success status
    """
    results = {}
    for package in packages:
        results[package] = install_system_package(package)
    return results


# Common package installation helpers
def install_browser_testing_deps() -> dict[str, bool]:
    """Install browser and related dependencies for web testing."""
    packages = ["chromium", "firefox", "xvfb"]
    return install_multiple_packages(packages)


def install_build_tools() -> dict[str, bool]:
    """Install compilers and build tools."""
    packages = ["build-essential", "cmake", "pkg-config"]
    return install_multiple_packages(packages)


def install_database_tools() -> dict[str, bool]:
    """Install database servers and clients for testing."""
    packages = ["postgresql", "redis-server", "sqlite3"]
    return install_multiple_packages(packages)


def is_wsl2() -> bool:
    """Detect if running in WSL2.

    Returns:
        True if running in Windows Subsystem for Linux 2
    """
    try:
        # Check for WSL-specific file
        if Path("/proc/version").exists():
            version = Path("/proc/version").read_text().lower()
            if "microsoft" in version or "wsl" in version:
                return True

        # Check for WSL interop
        if Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
            return True

    except Exception:
        pass

    return False


def is_windows() -> bool:
    """Check if running on Windows (native, not WSL)."""
    return sys.platform == "win32"


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux (including WSL)."""
    return sys.platform.startswith("linux")


def has_display() -> bool:
    """Check if a display is available.

    Returns:
        True if DISPLAY env var is set or on Windows/macOS
    """
    import os

    if is_windows() or is_macos():
        return True

    return bool(os.environ.get("DISPLAY"))


class VirtualDisplay:
    """Manages virtual display for headless testing."""

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.display: str = ":99"
        self.type: str = "none"

    async def start(self) -> str:
        """Start virtual display.

        Tries Wayland compositor first, then xvnc, then Xvfb.

        Returns:
            DISPLAY value to use
        """
        # If already have a display, use it
        if has_display():
            import os
            return os.environ.get("DISPLAY", ":0")

        # Try different virtual display options
        if await self._try_wayland():
            self.type = "wayland"
            return self.display
        elif await self._try_xvnc():
            self.type = "xvnc"
            return self.display
        elif await self._try_xvfb():
            self.type = "xvfb"
            return self.display

        raise RuntimeError("Could not start any virtual display server")

    async def _try_wayland(self) -> bool:
        """Try to start a Wayland compositor."""
        if not shutil.which("weston"):
            return False

        try:
            import os
            # Weston in headless mode
            self.process = subprocess.Popen(
                ["weston", "--backend=headless-backend.so"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "XDG_RUNTIME_DIR": "/tmp"},
            )
            await asyncio.sleep(1)
            if self.process.poll() is None:
                return True
        except Exception:
            pass
        return False

    async def _try_xvnc(self) -> bool:
        """Try to start Xvnc."""
        if not shutil.which("Xvnc"):
            return False

        try:
            self.process = subprocess.Popen(
                ["Xvnc", self.display, "-screen", "0", "1920x1080x24"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            await asyncio.sleep(1)
            if self.process.poll() is None:
                return True
        except Exception:
            pass
        return False

    async def _try_xvfb(self) -> bool:
        """Try to start Xvfb."""
        if not shutil.which("Xvfb"):
            return False

        try:
            self.process = subprocess.Popen(
                ["Xvfb", self.display, "-screen", "0", "1920x1080x24"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            await asyncio.sleep(1)
            if self.process.poll() is None:
                return True
        except Exception:
            pass
        return False

    def stop(self) -> None:
        """Stop virtual display."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None


async def setup_virtual_display() -> VirtualDisplay:
    """Set up virtual display for headless testing.

    Returns:
        VirtualDisplay instance with DISPLAY value
    """
    display = VirtualDisplay()
    await display.start()
    return display


def install_browser(browser: str = "chromium") -> bool:
    """Install a browser for web testing.

    Args:
        browser: Browser to install (chromium, firefox, chrome)

    Returns:
        True if installation succeeded
    """
    pm = detect_package_manager()

    # Map browser names to package names per package manager
    package_map: dict[str, dict[PackageManager, str]] = {
        "chromium": {
            PackageManager.APT: "chromium-browser",
            PackageManager.DNF: "chromium",
            PackageManager.PACMAN: "chromium",
            PackageManager.BREW: "chromium",
            PackageManager.APK: "chromium",
        },
        "firefox": {
            PackageManager.APT: "firefox",
            PackageManager.DNF: "firefox",
            PackageManager.PACMAN: "firefox",
            PackageManager.BREW: "firefox",
            PackageManager.APK: "firefox",
        },
        "chrome": {
            PackageManager.APT: "google-chrome-stable",
            PackageManager.DNF: "google-chrome-stable",
            PackageManager.BREW: "google-chrome",
        },
    }

    package = package_map.get(browser, {}).get(pm)
    if package:
        return install_system_package(package, pm)

    return False


def get_extended_capabilities() -> dict[str, Any]:
    """Get extended system capabilities including platform specifics.

    Returns:
        Dict with all system capability information
    """
    caps = get_system_capabilities()

    return {
        "platform": caps.platform,
        "architecture": caps.architecture,
        "package_manager": caps.package_manager.value,
        "has_passwordless_sudo": caps.has_passwordless_sudo,
        "available_tools": caps.available_tools,
        "is_wsl2": is_wsl2(),
        "is_windows": is_windows(),
        "is_macos": is_macos(),
        "is_linux": is_linux(),
        "has_display": has_display(),
    }


# RDP Support for remote GUI testing
class RDPServer:
    """Manages xrdp server for remote GUI access."""

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.port: int = 3389
        self.started: bool = False

    async def start(self, port: int = 3389) -> bool:
        """Start xrdp server for remote desktop access.

        Args:
            port: Port to listen on (default 3389)

        Returns:
            True if started successfully
        """
        self.port = port

        # Check if xrdp is installed
        if not shutil.which("xrdp"):
            return False

        try:
            # Start xrdp service
            result = subprocess.run(
                ["sudo", "-n", "service", "xrdp", "start"],
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.started = True
                await asyncio.sleep(2)  # Wait for service to start
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try starting xrdp directly
        try:
            self.process = subprocess.Popen(
                ["sudo", "-n", "xrdp", "-n"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            await asyncio.sleep(2)
            if self.process.poll() is None:
                self.started = True
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return False

    def stop(self) -> None:
        """Stop xrdp server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        if self.started:
            subprocess.run(
                ["sudo", "-n", "service", "xrdp", "stop"],
                capture_output=True,
                timeout=10,
            )
            self.started = False

    def get_connection_info(self) -> dict[str, Any]:
        """Get RDP connection information."""
        import socket
        hostname = socket.gethostname()
        return {
            "host": hostname,
            "port": self.port,
            "protocol": "rdp",
            "connection_string": f"xfreerdp /v:{hostname}:{self.port}",
        }


def install_rdp_server() -> bool:
    """Install xrdp server for remote GUI testing.

    Returns:
        True if installation succeeded
    """
    pm = detect_package_manager()

    packages: dict[PackageManager, list[str]] = {
        PackageManager.APT: ["xrdp", "xfce4", "xfce4-goodies"],
        PackageManager.DNF: ["xrdp", "xfce4-session"],
        PackageManager.PACMAN: ["xrdp", "xfce4"],
        PackageManager.APK: ["xrdp"],
    }

    pkgs = packages.get(pm, [])
    if not pkgs:
        return False

    results = install_multiple_packages(pkgs)
    return all(results.values())


# Resource availability checking
@dataclass
class ResourceCheck:
    """Result of a resource availability check."""

    name: str
    available: bool
    details: str
    critical: bool = True


async def check_api_endpoint(
    url: str,
    name: str = "API",
    timeout: float = 10.0,
) -> ResourceCheck:
    """Check if an API endpoint is accessible.

    Args:
        url: URL to check
        name: Human-readable name for the resource
        timeout: Timeout in seconds

    Returns:
        ResourceCheck with availability status
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code < 500:
                return ResourceCheck(
                    name=name,
                    available=True,
                    details=f"HTTP {response.status_code}",
                )
            return ResourceCheck(
                name=name,
                available=False,
                details=f"Server error: HTTP {response.status_code}",
            )
    except Exception as e:
        return ResourceCheck(
            name=name,
            available=False,
            details=f"Connection failed: {e}",
        )


async def check_database(
    db_type: str,
    host: str = "localhost",
    port: int | None = None,
    name: str = "Database",
) -> ResourceCheck:
    """Check if a database is accessible.

    Args:
        db_type: Type of database (postgres, mysql, redis, etc.)
        host: Database host
        port: Database port (uses default if None)
        name: Human-readable name

    Returns:
        ResourceCheck with availability status
    """
    default_ports = {
        "postgres": 5432,
        "postgresql": 5432,
        "mysql": 3306,
        "redis": 6379,
        "mongodb": 27017,
        "sqlite": None,  # No port needed
    }

    if port is None:
        port = default_ports.get(db_type.lower())

    # For SQLite, just check if the file exists
    if db_type.lower() == "sqlite":
        return ResourceCheck(
            name=name,
            available=True,
            details="SQLite is always available",
            critical=False,
        )

    # Check TCP connection
    import socket
    if port:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return ResourceCheck(
                    name=name,
                    available=True,
                    details=f"Connected to {host}:{port}",
                )
        except socket.error as e:
            return ResourceCheck(
                name=name,
                available=False,
                details=f"Connection failed: {e}",
            )

    return ResourceCheck(
        name=name,
        available=False,
        details=f"Cannot connect to {db_type} at {host}:{port}",
    )


def check_file_exists(path: str, name: str = "File") -> ResourceCheck:
    """Check if a file or directory exists.

    Args:
        path: Path to check
        name: Human-readable name

    Returns:
        ResourceCheck with availability status
    """
    p = Path(path)
    if p.exists():
        file_type = "directory" if p.is_dir() else "file"
        return ResourceCheck(
            name=name,
            available=True,
            details=f"Found {file_type}: {path}",
        )
    return ResourceCheck(
        name=name,
        available=False,
        details=f"Not found: {path}",
    )


def check_tool_installed(tool: str, name: str | None = None) -> ResourceCheck:
    """Check if a command-line tool is installed.

    Args:
        tool: Tool name/command
        name: Human-readable name (defaults to tool name)

    Returns:
        ResourceCheck with availability status
    """
    if name is None:
        name = tool

    path = shutil.which(tool)
    if path:
        return ResourceCheck(
            name=name,
            available=True,
            details=f"Found at: {path}",
        )
    return ResourceCheck(
        name=name,
        available=False,
        details=f"Tool '{tool}' not found in PATH",
    )


def check_env_var(var: str, name: str | None = None) -> ResourceCheck:
    """Check if an environment variable is set.

    Args:
        var: Environment variable name
        name: Human-readable name (defaults to var name)

    Returns:
        ResourceCheck with availability status
    """
    import os

    if name is None:
        name = var

    value = os.environ.get(var)
    if value:
        # Don't expose the full value for security
        masked = value[:4] + "..." if len(value) > 4 else "***"
        return ResourceCheck(
            name=name,
            available=True,
            details=f"Set (value: {masked})",
        )
    return ResourceCheck(
        name=name,
        available=False,
        details=f"Environment variable '{var}' not set",
    )


async def check_network_host(host: str, port: int, name: str = "Network") -> ResourceCheck:
    """Check if a network host is reachable.

    Args:
        host: Host to check
        port: Port to check
        name: Human-readable name

    Returns:
        ResourceCheck with availability status
    """
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return ResourceCheck(
                name=name,
                available=True,
                details=f"Can reach {host}:{port}",
            )
    except socket.error as e:
        return ResourceCheck(
            name=name,
            available=False,
            details=f"Network error: {e}",
        )

    return ResourceCheck(
        name=name,
        available=False,
        details=f"Cannot reach {host}:{port}",
    )


async def check_all_resources(
    checks: list[ResourceCheck],
) -> tuple[bool, list[ResourceCheck]]:
    """Check all resources and return summary.

    Args:
        checks: List of ResourceCheck results

    Returns:
        Tuple of (all_critical_available, list of failed checks)
    """
    failed = [c for c in checks if not c.available]
    critical_failed = [c for c in failed if c.critical]

    return len(critical_failed) == 0, failed


@dataclass
class ProjectResourceRequirements:
    """Resource requirements for a project."""

    apis: list[str]  # API URLs to check
    databases: list[tuple[str, str, int | None]]  # (type, host, port)
    files: list[str]  # Required files/directories
    tools: list[str]  # Required CLI tools
    env_vars: list[str]  # Required environment variables
    network_hosts: list[tuple[str, int]]  # (host, port) pairs


async def verify_project_resources(
    requirements: ProjectResourceRequirements,
) -> tuple[bool, list[ResourceCheck]]:
    """Verify all project resource requirements are met.

    Args:
        requirements: ProjectResourceRequirements to check

    Returns:
        Tuple of (all_available, list of all checks)
    """
    checks: list[ResourceCheck] = []

    # Check APIs
    for url in requirements.apis:
        check = await check_api_endpoint(url, f"API: {url}")
        checks.append(check)

    # Check databases
    for db_type, host, port in requirements.databases:
        check = await check_database(db_type, host, port, f"DB: {db_type}")
        checks.append(check)

    # Check files
    for path in requirements.files:
        check = check_file_exists(path, f"File: {path}")
        checks.append(check)

    # Check tools
    for tool in requirements.tools:
        check = check_tool_installed(tool, f"Tool: {tool}")
        checks.append(check)

    # Check env vars
    for var in requirements.env_vars:
        check = check_env_var(var, f"Env: {var}")
        checks.append(check)

    # Check network hosts
    for host, port in requirements.network_hosts:
        check = await check_network_host(host, port, f"Host: {host}:{port}")
        checks.append(check)

    return await check_all_resources(checks)
