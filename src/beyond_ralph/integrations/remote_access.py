"""Remote access module for Android testing and VNC support.

This module provides:
- WSL2 environment detection for Android testing strategy
- Windows host ADB connectivity for WSL2 environments
- Appium server management for mobile testing
- Android emulator control
- VNC session management for headless display access
- Interview phase Android requirements gathering
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import secrets
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Environment Detection
# =============================================================================


@dataclass
class EnvironmentInfo:
    """Runtime environment information for Android testing strategy.

    Attributes:
        platform: Detected platform ("WSL2", "LINUX", "MACOS", "WINDOWS")
        android_testing_mode: Testing strategy ("local" or "remote")
        adb_access: ADB access method ("direct" or "mirrored")
        capabilities: Dictionary of detected capabilities
    """

    platform: str
    android_testing_mode: str
    adb_access: str
    capabilities: dict[str, object] = field(default_factory=dict)


def detect_environment() -> EnvironmentInfo:
    """Detect runtime environment for Android testing strategy.

    Returns:
        EnvironmentInfo with detected platform and testing strategy.
    """
    platform = _detect_platform()
    android_testing_mode = "local"
    adb_access = "direct"
    capabilities: dict[str, object] = {}

    # Check for common tools
    capabilities["adb"] = shutil.which("adb") is not None
    capabilities["appium"] = shutil.which("appium") is not None
    capabilities["node"] = shutil.which("node") is not None
    capabilities["npm"] = shutil.which("npm") is not None

    if platform == "WSL2":
        # In WSL2, Android testing typically requires connecting to Windows host
        android_testing_mode = "remote"
        adb_access = "mirrored"

        # Check if we can reach Windows host
        host_ip = get_wsl2_host_ip()
        capabilities["wsl2_host_ip"] = host_ip
        capabilities["windows_adb_reachable"] = host_ip is not None

    elif platform == "LINUX":
        # Native Linux can use local ADB
        android_testing_mode = "local"
        adb_access = "direct"

    elif platform == "MACOS":
        # macOS can use local ADB
        android_testing_mode = "local"
        adb_access = "direct"

    elif platform == "WINDOWS":
        # Windows uses local ADB
        android_testing_mode = "local"
        adb_access = "direct"

    return EnvironmentInfo(
        platform=platform,
        android_testing_mode=android_testing_mode,
        adb_access=adb_access,
        capabilities=capabilities,
    )


def _detect_platform() -> str:
    """Detect the current platform.

    Returns:
        One of "WSL2", "LINUX", "MACOS", "WINDOWS"
    """
    # Check for WSL2 first
    if _is_wsl2():
        return "WSL2"

    # Check standard platforms
    import sys

    if sys.platform == "linux":
        return "LINUX"
    elif sys.platform == "darwin":
        return "MACOS"
    elif sys.platform == "win32":
        return "WINDOWS"

    return "LINUX"  # Default fallback


def _is_wsl2() -> bool:
    """Check if running in WSL2 environment.

    Returns:
        True if running in WSL2
    """
    # Check WSL_DISTRO_NAME environment variable
    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    # Check /proc/version for Microsoft kernel
    try:
        version_path = Path("/proc/version")
        if version_path.exists():
            version_text = version_path.read_text().lower()
            if "microsoft" in version_text:
                return True
    except OSError:
        pass

    return False


def get_wsl2_host_ip() -> str | None:
    """Get the Windows host IP address from WSL2.

    In WSL2, the Windows host IP is typically in /etc/resolv.conf as the nameserver,
    or can be obtained from the default gateway.

    Returns:
        Host IP address string, or None if not found.
    """
    # Try /etc/resolv.conf first (most reliable)
    try:
        resolv_path = Path("/etc/resolv.conf")
        if resolv_path.exists():
            content = resolv_path.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("nameserver"):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[1]
                        # Validate it looks like an IP
                        if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                            return ip
    except OSError:
        pass

    # Try getting default gateway
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Output like: "default via 172.x.x.1 dev eth0"
            match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


# =============================================================================
# Windows Host ADB Connectivity
# =============================================================================


@dataclass
class WindowsHostConfig:
    """Configuration for connecting to Windows host ADB server.

    Attributes:
        host_ip: IP address of Windows host
        adb_port: ADB server port (default 5037)
        emulator_name: Default emulator device name
        verified: Whether connection has been verified
    """

    host_ip: str
    adb_port: int = 5037
    emulator_name: str = "emulator-5554"
    verified: bool = False


@dataclass
class ADBConnectionResult:
    """Result of an ADB connection attempt.

    Attributes:
        connected: Whether connection was successful
        devices: List of connected device identifiers
        error_message: Error message if connection failed
    """

    connected: bool
    devices: list[str] = field(default_factory=list)
    error_message: str | None = None


class WindowsADBClient:
    """Client for connecting to ADB server on Windows host from WSL2.

    This client allows WSL2 to connect to an ADB server running on the
    Windows host machine, enabling Android testing from within WSL2.
    """

    def __init__(self, config: WindowsHostConfig) -> None:
        """Initialize the Windows ADB client.

        Args:
            config: Configuration for connecting to Windows host
        """
        self.config = config
        self._connected = False

    @property
    def host_string(self) -> str:
        """Get the host:port string for ADB commands."""
        return f"{self.config.host_ip}:{self.config.adb_port}"

    async def connect(self) -> ADBConnectionResult:
        """Connect to the Windows host ADB server.

        Returns:
            ADBConnectionResult with connection status and device list.
        """
        try:
            # First, try to connect to the remote ADB server
            result = await self.execute_command("connect", self.host_string)

            if "connected" in result.lower() or "already connected" in result.lower():
                self._connected = True
                devices = await self.list_devices()
                self.config.verified = True
                return ADBConnectionResult(
                    connected=True,
                    devices=devices,
                    error_message=None,
                )
            else:
                return ADBConnectionResult(
                    connected=False,
                    devices=[],
                    error_message=f"Failed to connect: {result}",
                )

        except Exception as e:
            logger.error("ADB connection failed: %s", e)
            return ADBConnectionResult(
                connected=False,
                devices=[],
                error_message=str(e),
            )

    async def list_devices(self) -> list[str]:
        """List connected Android devices.

        Returns:
            List of device identifiers.
        """
        try:
            output = await self.execute_command("devices")

            devices = []
            for line in output.strip().split("\n"):
                line = line.strip()
                # Skip header and empty lines
                if not line or line.startswith("List of"):
                    continue
                # Parse device line: "emulator-5554	device"
                parts = line.split("\t")
                if len(parts) >= 2 and parts[1] in ("device", "emulator"):
                    devices.append(parts[0])

            return devices

        except Exception as e:
            logger.error("Failed to list devices: %s", e)
            return []

    async def execute_command(self, *args: str) -> str:
        """Execute an ADB command.

        Args:
            *args: ADB command arguments

        Returns:
            Command output string.

        Raises:
            RuntimeError: If adb is not found or command fails.
        """
        adb_path = shutil.which("adb")
        if not adb_path:
            raise RuntimeError("adb not found in PATH")

        # Build command with host flag for remote connection
        cmd = [adb_path, "-H", self.config.host_ip, "-P", str(self.config.adb_port)]
        cmd.extend(args)

        logger.debug("Executing ADB command: %s", " ".join(cmd))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

            if process.returncode != 0:
                error_msg = stderr.decode().strip() or "Unknown error"
                raise RuntimeError(f"ADB command failed: {error_msg}")

            return stdout.decode().strip()

        except TimeoutError as e:
            raise RuntimeError("ADB command timed out") from e

    async def disconnect(self) -> bool:
        """Disconnect from the Windows host ADB server.

        Returns:
            True if disconnection was successful.
        """
        try:
            await self.execute_command("disconnect", self.host_string)
            self._connected = False
            self.config.verified = False
            return True
        except Exception as e:
            logger.error("Failed to disconnect: %s", e)
            return False


def create_adb_client_for_wsl2() -> WindowsADBClient | None:
    """Create an ADB client configured for WSL2 environment.

    Returns:
        Configured WindowsADBClient, or None if not in WSL2 or host IP not found.
    """
    if not _is_wsl2():
        return None

    host_ip = get_wsl2_host_ip()
    if not host_ip:
        return None

    config = WindowsHostConfig(host_ip=host_ip)
    return WindowsADBClient(config)


# =============================================================================
# Appium Server Management
# =============================================================================


@dataclass
class AppiumConfig:
    """Configuration for Appium server.

    Attributes:
        port: Port to run Appium server on
        adb_host: ADB host address (for WSL2 scenarios)
        log_level: Appium log level
        relaxed_security: Whether to enable relaxed security (allows some insecure operations)
    """

    port: int = 4723
    adb_host: str | None = None
    log_level: str = "info"
    relaxed_security: bool = True


@dataclass
class AppiumServerStatus:
    """Status of an Appium server instance.

    Attributes:
        running: Whether the server is running
        port: Port the server is running on
        url: Base URL for the server
        pid: Process ID of the server
    """

    running: bool
    port: int
    url: str
    pid: int | None = None


class AppiumManager:
    """Manager for Appium server lifecycle.

    Handles starting, stopping, and health checking Appium servers
    for mobile testing automation.
    """

    def __init__(self) -> None:
        """Initialize the Appium manager."""
        self._process: asyncio.subprocess.Process | None = None
        self._config: AppiumConfig | None = None
        self._suggested_config: AppiumConfig | None = None

    async def start_server(self, config: AppiumConfig) -> AppiumServerStatus:
        """Start an Appium server with the given configuration.

        Args:
            config: Appium server configuration

        Returns:
            AppiumServerStatus with server details

        Raises:
            RuntimeError: If Appium is not installed or server fails to start
        """
        # Check if appium is installed
        appium_path = shutil.which("appium")
        if not appium_path:
            raise RuntimeError("Appium not found. Install with: npm install -g appium")

        # Stop any existing server
        if self._process:
            await self.stop_server()

        # Build command
        cmd = [appium_path, "--port", str(config.port), "--log-level", config.log_level]

        if config.relaxed_security:
            cmd.append("--relaxed-security")

        if config.adb_host:
            cmd.extend(["--default-capabilities", f'{{"adb:remoteAdbHost":"{config.adb_host}"}}'])

        logger.info("Starting Appium server: %s", " ".join(cmd))

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._config = config

            # Wait briefly for server to start
            await asyncio.sleep(2)

            # Check if server is healthy
            if await self.health_check():
                return AppiumServerStatus(
                    running=True,
                    port=config.port,
                    url=f"http://localhost:{config.port}",
                    pid=self._process.pid,
                )
            else:
                raise RuntimeError("Appium server failed health check")

        except Exception as e:
            logger.error("Failed to start Appium server: %s", e)
            if self._process:
                self._process.terminate()
                self._process = None
            raise

    async def stop_server(self) -> bool:
        """Stop the running Appium server.

        Returns:
            True if server was stopped successfully.
        """
        if not self._process:
            return True

        try:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()

            self._process = None
            self._config = None
            logger.info("Appium server stopped")
            return True

        except Exception as e:
            logger.error("Failed to stop Appium server: %s", e)
            return False

    async def health_check(self) -> bool:
        """Check if the Appium server is healthy.

        Returns:
            True if server is responding to health checks.
        """
        if not self._config:
            return False

        url = f"http://localhost:{self._config.port}/status"

        try:
            # Use curl as a simple HTTP client (widely available)
            process = await asyncio.create_subprocess_exec(
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5)
            status_code = stdout.decode().strip()
            return status_code == "200"

        except (TimeoutError, FileNotFoundError):
            return False
        except Exception as e:
            logger.debug("Health check failed: %s", e)
            return False

    async def install_appium(self) -> bool:
        """Install Appium using npm.

        Returns:
            True if installation was successful.

        Raises:
            RuntimeError: If npm is not found.
        """
        npm_path = shutil.which("npm")
        if not npm_path:
            raise RuntimeError("npm not found. Install Node.js first.")

        logger.info("Installing Appium globally...")

        try:
            process = await asyncio.create_subprocess_exec(
                npm_path,
                "install",
                "-g",
                "appium",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

            if process.returncode == 0:
                logger.info("Appium installed successfully")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error("Appium installation failed: %s", error_msg)
                return False

        except TimeoutError:
            logger.error("Appium installation timed out")
            return False

    def get_status(self) -> AppiumServerStatus:
        """Get the current server status.

        Returns:
            AppiumServerStatus with current state.
        """
        if self._process and self._config and self._process.returncode is None:
            # Process is still running
            return AppiumServerStatus(
                running=True,
                port=self._config.port,
                url=f"http://localhost:{self._config.port}",
                pid=self._process.pid,
            )

        return AppiumServerStatus(
            running=False,
            port=self._config.port if self._config else 4723,
            url="",
            pid=None,
        )


# =============================================================================
# Android Emulator Control
# =============================================================================


class AndroidEmulatorManager:
    """Manager for Android emulator operations.

    Provides methods for listing, starting, and interacting with
    Android emulators and devices.
    """

    def __init__(self, adb_client: WindowsADBClient | None = None) -> None:
        """Initialize the emulator manager.

        Args:
            adb_client: Optional ADB client for remote connections (WSL2).
                       If None, uses local ADB.
        """
        self.adb_client = adb_client
        self._use_remote = adb_client is not None

    async def _execute_adb(self, *args: str) -> str:
        """Execute an ADB command using appropriate client.

        Args:
            *args: ADB command arguments

        Returns:
            Command output string.
        """
        if self._use_remote and self.adb_client:
            return await self.adb_client.execute_command(*args)

        # Local ADB execution
        adb_path = shutil.which("adb")
        if not adb_path:
            raise RuntimeError("adb not found in PATH")

        cmd = [adb_path] + list(args)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

        if process.returncode != 0:
            error_msg = stderr.decode().strip() or "Unknown error"
            raise RuntimeError(f"ADB command failed: {error_msg}")

        return stdout.decode().strip()

    async def list_devices(self) -> list[str]:
        """List connected Android devices/emulators.

        Returns:
            List of device identifiers.
        """
        if self._use_remote and self.adb_client:
            return await self.adb_client.list_devices()

        output = await self._execute_adb("devices")
        devices = []

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("List of"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] in ("device", "emulator"):
                devices.append(parts[0])

        return devices

    async def start_emulator(self, name: str) -> bool:
        """Start an Android emulator by name.

        Args:
            name: AVD (Android Virtual Device) name

        Returns:
            True if emulator start was initiated.

        Note:
            This method starts the emulator in the background.
            Use wait_for_boot() to wait until it's ready.
        """
        emulator_path = shutil.which("emulator")
        if not emulator_path:
            # Try common locations
            android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
            if android_home:
                possible_path = Path(android_home) / "emulator" / "emulator"
                if possible_path.exists():
                    emulator_path = str(possible_path)

        if not emulator_path:
            raise RuntimeError("Android emulator not found. Ensure ANDROID_HOME is set.")

        cmd = [emulator_path, "-avd", name, "-no-snapshot-load"]

        logger.info("Starting emulator: %s", name)

        try:
            # Start emulator in background (don't wait for it)
            await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent
            )
            return True

        except Exception as e:
            logger.error("Failed to start emulator: %s", e)
            return False

    async def wait_for_boot(self, timeout: int = 120) -> bool:
        """Wait for the emulator to fully boot.

        Args:
            timeout: Maximum seconds to wait for boot

        Returns:
            True if emulator booted successfully within timeout.
        """
        start_time = time.monotonic()

        while (time.monotonic() - start_time) < timeout:
            try:
                # Check if device is online
                devices = await self.list_devices()
                if not devices:
                    await asyncio.sleep(2)
                    continue

                # Check boot_completed property
                output = await self._execute_adb(
                    "-s", devices[0], "shell", "getprop", "sys.boot_completed"
                )

                if output.strip() == "1":
                    logger.info("Emulator boot completed")
                    return True

            except Exception as e:
                logger.debug("Waiting for boot: %s", e)

            await asyncio.sleep(2)

        logger.warning("Emulator boot timed out after %d seconds", timeout)
        return False

    async def install_apk(self, path: str) -> bool:
        """Install an APK on the connected device/emulator.

        Args:
            path: Path to the APK file

        Returns:
            True if installation was successful.

        Raises:
            FileNotFoundError: If APK file doesn't exist.
        """
        apk_path = Path(path)
        if not apk_path.exists():
            raise FileNotFoundError(f"APK not found: {path}")

        try:
            output = await self._execute_adb("install", "-r", str(apk_path))
            success = "Success" in output
            if success:
                logger.info("APK installed successfully: %s", path)
            else:
                logger.error("APK installation failed: %s", output)
            return success

        except Exception as e:
            logger.error("Failed to install APK: %s", e)
            return False

    async def take_screenshot(self) -> bytes:
        """Take a screenshot from the connected device/emulator.

        Returns:
            PNG image data as bytes.

        Raises:
            RuntimeError: If screenshot capture fails.
        """
        # Capture screenshot to device
        remote_path = "/sdcard/screenshot.png"

        try:
            await self._execute_adb("shell", "screencap", "-p", remote_path)

            # Pull screenshot to local temp file
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                local_path = tmp.name

            await self._execute_adb("pull", remote_path, local_path)

            # Read the image data
            with open(local_path, "rb") as f:
                data = f.read()

            # Clean up
            Path(local_path).unlink(missing_ok=True)
            await self._execute_adb("shell", "rm", remote_path)

            return data

        except Exception as e:
            raise RuntimeError(f"Screenshot capture failed: {e}") from e

    async def uninstall_app(self, package_name: str) -> bool:
        """Uninstall an app from the device.

        Args:
            package_name: Android package name (e.g., com.example.app)

        Returns:
            True if uninstallation was successful.
        """
        try:
            output = await self._execute_adb("uninstall", package_name)
            return "Success" in output
        except Exception as e:
            logger.error("Failed to uninstall %s: %s", package_name, e)
            return False

    async def get_device_info(self) -> dict[str, str]:
        """Get information about the connected device.

        Returns:
            Dictionary with device information.
        """
        info: dict[str, str] = {}

        try:
            # Get device model
            model = await self._execute_adb("shell", "getprop", "ro.product.model")
            info["model"] = model.strip()

            # Get Android version
            version = await self._execute_adb("shell", "getprop", "ro.build.version.release")
            info["android_version"] = version.strip()

            # Get SDK version
            sdk = await self._execute_adb("shell", "getprop", "ro.build.version.sdk")
            info["sdk_version"] = sdk.strip()

            # Get device serial
            devices = await self.list_devices()
            if devices:
                info["serial"] = devices[0]

        except Exception as e:
            logger.error("Failed to get device info: %s", e)

        return info

    async def clear_app_data(self, package_name: str) -> bool:
        """Clear app data for the specified package.

        Args:
            package_name: Android package name

        Returns:
            True if data was cleared successfully.
        """
        try:
            output = await self._execute_adb("shell", "pm", "clear", package_name)
            return "Success" in output
        except Exception as e:
            logger.error("Failed to clear app data: %s", e)
            return False

    async def launch_app(self, package_name: str, activity: str | None = None) -> bool:
        """Launch an app on the device.

        Args:
            package_name: Android package name
            activity: Optional activity name. If not provided, launches default activity.

        Returns:
            True if app was launched successfully.
        """
        try:
            if activity:
                component = f"{package_name}/{activity}"
                await self._execute_adb("shell", "am", "start", "-n", component)
            else:
                await self._execute_adb(
                    "shell",
                    "monkey",
                    "-p",
                    package_name,
                    "-c",
                    "android.intent.category.LAUNCHER",
                    "1",
                )
            return True
        except Exception as e:
            logger.error("Failed to launch app: %s", e)
            return False


# =============================================================================
# Convenience Functions
# =============================================================================


def create_android_test_environment() -> tuple[EnvironmentInfo, AndroidEmulatorManager]:
    """Create an Android testing environment based on the current platform.

    Returns:
        Tuple of (EnvironmentInfo, AndroidEmulatorManager) configured for the platform.
    """
    env = detect_environment()

    if env.platform == "WSL2":
        # Create WSL2-aware ADB client
        adb_client = create_adb_client_for_wsl2()
        emulator_manager = AndroidEmulatorManager(adb_client)
    else:
        # Use local ADB
        emulator_manager = AndroidEmulatorManager()

    return env, emulator_manager


async def setup_complete_android_stack(
    adb_host: str | None = None,
    appium_port: int = 4723,
) -> tuple[AppiumManager, AndroidEmulatorManager]:
    """Set up a complete Android testing stack.

    This function sets up both Appium server and Android emulator manager,
    configured appropriately for the current environment.

    Args:
        adb_host: ADB host for remote connections (auto-detected in WSL2)
        appium_port: Port for Appium server

    Returns:
        Tuple of (AppiumManager, AndroidEmulatorManager)
    """
    env = detect_environment()

    # Determine ADB host
    if adb_host is None and env.platform == "WSL2":
        adb_host = get_wsl2_host_ip()

    # Create Appium manager (config will be passed to start_server when needed)
    appium_manager = AppiumManager()

    # Create emulator manager
    if env.platform == "WSL2":
        adb_client = create_adb_client_for_wsl2()
        emulator_manager = AndroidEmulatorManager(adb_client)
    else:
        emulator_manager = AndroidEmulatorManager()

    # Store suggested config for reference (can be used when starting server)
    appium_manager._suggested_config = AppiumConfig(
        port=appium_port,
        adb_host=adb_host,
        relaxed_security=True,
    )

    return appium_manager, emulator_manager


# =============================================================================
# Interview Phase Android Questions
# =============================================================================


class AndroidTestingConfigurationError(Exception):
    """Raised when Android testing configuration is missing or invalid."""


@dataclass
class AndroidTestingRequirements:
    """Requirements for Android testing gathered during interview phase.

    Attributes:
        needs_android_testing: Whether the project requires Android testing
        environment: Detected runtime environment info
        windows_config: Windows host configuration (for WSL2 scenarios)
        connection_verified: Whether the ADB connection has been verified
    """

    needs_android_testing: bool
    environment: EnvironmentInfo
    windows_config: WindowsHostConfig | None = None
    connection_verified: bool = False


async def interview_android_requirements(
    ask_question_fn: Callable[[str, list[str] | None], str],
) -> AndroidTestingRequirements:
    """Ask user about Android testing during interview phase.

    This function guides the user through Android testing requirements gathering.
    It detects the environment, asks if Android testing is needed, and for WSL2
    environments, collects Windows host configuration.

    IMPORTANT: If Android testing is required but configuration is missing or
    connection verification fails, this function will BLOCK (raise an exception)
    rather than silently skip Android testing.

    Args:
        ask_question_fn: Async-compatible callable that asks the user a question.
            Signature: (question: str, options: list[str] | None) -> str
            If options is None, expects free-form text input.
            Returns the user's answer.

    Returns:
        AndroidTestingRequirements with gathered configuration.

    Raises:
        AndroidTestingConfigurationError: If Android testing is required but
            configuration cannot be completed (missing config, failed verification).
    """
    # Detect current environment
    env = detect_environment()

    # Ask if Android testing is needed
    needs_android = ask_question_fn(
        "Does this project require Android app testing?",
        ["Yes", "No"],
    )

    if needs_android.lower() not in ("yes", "y"):
        return AndroidTestingRequirements(
            needs_android_testing=False,
            environment=env,
            windows_config=None,
            connection_verified=False,
        )

    # Android testing is required
    logger.info("Android testing required, configuring environment...")

    # Handle WSL2-specific configuration
    if env.platform == "WSL2":
        return await _configure_wsl2_android_testing(env, ask_question_fn)

    # For non-WSL2 platforms, verify local ADB is available
    if not env.capabilities.get("adb"):
        raise AndroidTestingConfigurationError(
            "Android testing required but ADB is not installed. "
            "Please install Android SDK platform-tools."
        )

    return AndroidTestingRequirements(
        needs_android_testing=True,
        environment=env,
        windows_config=None,
        connection_verified=True,  # Local ADB available
    )


async def _configure_wsl2_android_testing(
    env: EnvironmentInfo,
    ask_question_fn: Callable[[str, list[str] | None], str],
) -> AndroidTestingRequirements:
    """Configure Android testing for WSL2 environment.

    Args:
        env: Detected environment info
        ask_question_fn: Function to ask user questions

    Returns:
        AndroidTestingRequirements with WSL2-specific configuration

    Raises:
        AndroidTestingConfigurationError: If configuration fails
    """
    logger.info("WSL2 detected, configuring Windows host ADB connection...")

    # Try to auto-detect Windows host IP
    auto_host_ip = get_wsl2_host_ip()

    if auto_host_ip:
        use_auto = ask_question_fn(
            f"Detected Windows host IP: {auto_host_ip}. Use this address?",
            ["Yes", "No, enter manually"],
        )

        if use_auto.lower() in ("yes", "y"):
            host_ip = auto_host_ip
        else:
            host_ip = ask_question_fn(
                "Enter the Windows host IP address:",
                None,
            ).strip()
    else:
        host_ip = ask_question_fn(
            "Could not auto-detect Windows host IP. Enter the IP address:",
            None,
        ).strip()

    if not host_ip:
        raise AndroidTestingConfigurationError(
            "Android testing required in WSL2 but no Windows host IP provided."
        )

    # Validate IP format
    if not re.match(r"^\d+\.\d+\.\d+\.\d+$", host_ip):
        raise AndroidTestingConfigurationError(
            f"Invalid IP address format: {host_ip}"
        )

    # Ask for ADB port (with default)
    port_str = ask_question_fn(
        "Enter ADB port (default: 5037):",
        None,
    ).strip()

    adb_port = 5037
    if port_str:
        try:
            adb_port = int(port_str)
        except ValueError as e:
            raise AndroidTestingConfigurationError(
                f"Invalid ADB port: {port_str}"
            ) from e

    # Create configuration
    windows_config = WindowsHostConfig(
        host_ip=host_ip,
        adb_port=adb_port,
    )

    # Verify connection
    logger.info("Verifying ADB connection to Windows host...")
    client = WindowsADBClient(windows_config)

    try:
        result = await client.connect()
    except Exception as e:
        raise AndroidTestingConfigurationError(
            f"Failed to connect to Windows ADB server: {e}"
        ) from e

    if not result.connected:
        raise AndroidTestingConfigurationError(
            f"Failed to connect to Windows ADB server at {host_ip}:{adb_port}. "
            f"Error: {result.error_message}. "
            "Ensure ADB server is running on Windows (adb start-server)."
        )

    logger.info(
        "Successfully connected to Windows ADB server. Devices: %s",
        result.devices,
    )

    return AndroidTestingRequirements(
        needs_android_testing=True,
        environment=env,
        windows_config=windows_config,
        connection_verified=True,
    )


# =============================================================================
# VNC Session Management
# =============================================================================


@dataclass
class VNCSession:
    """Information about an active VNC session.

    Attributes:
        display: X display string (e.g., ":99")
        port: VNC port number (e.g., 5999 for display :99)
        password: Auto-generated session password
        websocket_port: Optional websockify port for web access
        resolution: Screen resolution (e.g., "1920x1080")
        pid: Process ID of the VNC server (x11vnc)
        xvfb_pid: Process ID of Xvfb (if started)
    """

    display: str
    port: int
    password: str
    websocket_port: int | None
    resolution: str
    pid: int | None = None
    xvfb_pid: int | None = None


class VNCManager:
    """Manager for VNC session lifecycle.

    Handles starting, stopping, and managing VNC sessions for headless
    display access. Supports Xvfb for virtual framebuffer and x11vnc
    for VNC serving.
    """

    # Package names by package manager
    _PACKAGE_MANAGERS: dict[str, dict[str, list[str]]] = {
        "apt": {
            "xvfb": ["xvfb"],
            "x11vnc": ["x11vnc"],
            "websockify": ["websockify"],
        },
        "dnf": {
            "xvfb": ["xorg-x11-server-Xvfb"],
            "x11vnc": ["x11vnc"],
            "websockify": ["python3-websockify"],
        },
        "brew": {
            "xvfb": [],  # Not available on macOS via brew
            "x11vnc": ["x11vnc"],
            "websockify": ["websockify"],
        },
    }

    def __init__(self) -> None:
        """Initialize the VNC manager."""
        self.active_sessions: dict[str, VNCSession] = {}

    def _generate_password(self) -> str:
        """Generate a secure 12-character password.

        Uses secrets.token_urlsafe which provides cryptographically
        secure random characters.

        Returns:
            12-character URL-safe random string.
        """
        # token_urlsafe(9) generates 12 characters (9 bytes = 12 base64 chars)
        return secrets.token_urlsafe(9)

    def _detect_display_server(self) -> tuple[str, str]:
        """Detect the display server type and current display string.

        Detection priority:
        1. Wayland (WAYLAND_DISPLAY set)
        2. X11 (DISPLAY set)
        3. Xvfb (check for running Xvfb process)
        4. Xvnc (check for running Xvnc process)

        Returns:
            Tuple of (server_type, display_string).
            server_type is one of: "wayland", "x11", "xvfb", "xvnc", "none"
            display_string is the DISPLAY value or empty string if none.
        """
        # Check Wayland first
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        if wayland_display:
            return ("wayland", wayland_display)

        # Check X11
        x11_display = os.environ.get("DISPLAY")
        if x11_display:
            # Determine if it's a real X server or virtual
            if self._check_process_running("Xvfb"):
                return ("xvfb", x11_display)
            if self._check_process_running("Xvnc"):
                return ("xvnc", x11_display)
            return ("x11", x11_display)

        # Check for running virtual servers without DISPLAY set
        if self._check_process_running("Xvfb"):
            return ("xvfb", "")
        if self._check_process_running("Xvnc"):
            return ("xvnc", "")

        return ("none", "")

    def _check_process_running(self, process_name: str) -> bool:
        """Check if a process is running by name.

        Args:
            process_name: Name of the process to check

        Returns:
            True if process is running.
        """
        try:
            result = subprocess.run(
                ["pgrep", "-x", process_name],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _detect_package_manager(self) -> str | None:
        """Detect available package manager.

        Returns:
            Package manager name ("apt", "dnf", "brew") or None.
        """
        for pm in ["apt", "dnf", "brew"]:
            if shutil.which(pm):
                return pm
        return None

    async def start_session(
        self,
        display: str = ":99",
        resolution: str = "1920x1080",
        websocket: bool = False,
        depth: int = 24,
    ) -> VNCSession:
        """Start a VNC session.

        This will:
        1. Generate a secure password
        2. Start Xvfb on the specified display
        3. Start x11vnc to serve the display
        4. Optionally start websockify for web browser access

        Args:
            display: X display string (default ":99")
            resolution: Screen resolution (default "1920x1080")
            websocket: Whether to start websockify for web access
            depth: Color depth (default 24)

        Returns:
            VNCSession with session details.

        Raises:
            RuntimeError: If required tools are not installed or session fails to start.
        """
        # Check if session already exists for this display
        if display in self.active_sessions:
            raise RuntimeError(f"VNC session already exists for display {display}")

        # Check required tools
        if not shutil.which("Xvfb"):
            raise RuntimeError(
                "Xvfb not found. Install with: sudo apt install xvfb"
            )
        if not shutil.which("x11vnc"):
            raise RuntimeError(
                "x11vnc not found. Install with: sudo apt install x11vnc"
            )

        # Generate password
        password = self._generate_password()

        # Calculate VNC port from display number
        # Display :99 -> port 5999
        display_num = int(display.lstrip(":"))
        vnc_port = 5900 + display_num

        # Parse resolution
        width, height = resolution.split("x")

        # Start Xvfb
        logger.info("Starting Xvfb on display %s with resolution %s", display, resolution)
        xvfb_cmd = [
            "Xvfb",
            display,
            "-screen", "0", f"{width}x{height}x{depth}",
        ]

        try:
            xvfb_process = await asyncio.create_subprocess_exec(
                *xvfb_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start Xvfb: {e}") from e

        # Wait briefly for Xvfb to initialize
        await asyncio.sleep(0.5)

        # Check if Xvfb started successfully
        if xvfb_process.returncode is not None:
            raise RuntimeError(
                f"Xvfb failed to start (exit code: {xvfb_process.returncode})"
            )

        # Start x11vnc
        logger.info(
            "Starting x11vnc on port %d (password: [REDACTED])",
            vnc_port,
        )

        x11vnc_cmd = [
            "x11vnc",
            "-display", display,
            "-rfbport", str(vnc_port),
            "-passwd", password,
            "-forever",  # Don't exit after first client disconnects
            "-shared",   # Allow multiple clients
            "-noxdamage",
            "-noxfixes",
            "-noxrecord",
        ]

        try:
            x11vnc_process = await asyncio.create_subprocess_exec(
                *x11vnc_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            # Cleanup Xvfb
            xvfb_process.terminate()
            raise RuntimeError(f"Failed to start x11vnc: {e}") from e

        # Wait briefly for x11vnc to initialize
        await asyncio.sleep(0.5)

        # Check if x11vnc started successfully
        if x11vnc_process.returncode is not None:
            xvfb_process.terminate()
            raise RuntimeError(
                f"x11vnc failed to start (exit code: {x11vnc_process.returncode})"
            )

        # Optionally start websockify
        websocket_port: int | None = None
        if websocket:
            if not shutil.which("websockify"):
                logger.warning("websockify not found, skipping WebSocket setup")
            else:
                websocket_port = vnc_port + 1000  # e.g., 6999 for VNC port 5999
                websockify_cmd = [
                    "websockify",
                    "--web", "/usr/share/novnc",
                    str(websocket_port),
                    f"localhost:{vnc_port}",
                ]

                try:
                    await asyncio.create_subprocess_exec(
                        *websockify_cmd,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    logger.info("WebSocket proxy started on port %d", websocket_port)
                except Exception as e:
                    logger.warning("Failed to start websockify: %s", e)
                    websocket_port = None

        # Create session object
        session = VNCSession(
            display=display,
            port=vnc_port,
            password=password,
            websocket_port=websocket_port,
            resolution=resolution,
            pid=x11vnc_process.pid,
            xvfb_pid=xvfb_process.pid,
        )

        self.active_sessions[display] = session
        logger.info(
            "VNC session started: display=%s, port=%d, websocket=%s",
            display,
            vnc_port,
            websocket_port,
        )

        return session

    async def stop_session(self, display: str) -> bool:
        """Stop a VNC session and cleanup processes.

        Args:
            display: X display string of the session to stop

        Returns:
            True if session was stopped successfully.
        """
        if display not in self.active_sessions:
            logger.warning("No active session found for display %s", display)
            return False

        session = self.active_sessions[display]

        # Kill x11vnc process
        if session.pid:
            try:
                os.kill(session.pid, 15)  # SIGTERM
                logger.debug("Sent SIGTERM to x11vnc (PID %d)", session.pid)
            except ProcessLookupError:
                pass  # Process already dead
            except OSError as e:
                logger.warning("Failed to kill x11vnc: %s", e)

        # Kill Xvfb process
        if session.xvfb_pid:
            try:
                os.kill(session.xvfb_pid, 15)  # SIGTERM
                logger.debug("Sent SIGTERM to Xvfb (PID %d)", session.xvfb_pid)
            except ProcessLookupError:
                pass  # Process already dead
            except OSError as e:
                logger.warning("Failed to kill Xvfb: %s", e)

        # Remove from active sessions
        del self.active_sessions[display]
        logger.info("VNC session stopped for display %s", display)

        return True

    async def install_vnc_deps(self) -> bool:
        """Install VNC dependencies using the system package manager.

        Attempts to install xvfb, x11vnc, and websockify using the
        detected package manager (apt, dnf, or brew).

        Returns:
            True if installation was successful.

        Raises:
            RuntimeError: If no supported package manager is found.
        """
        pm = self._detect_package_manager()
        if not pm:
            raise RuntimeError(
                "No supported package manager found (apt, dnf, brew)"
            )

        packages = self._PACKAGE_MANAGERS.get(pm, {})

        # Collect all packages to install
        to_install: list[str] = []
        for tool, pkg_list in packages.items():
            if not shutil.which(tool) and pkg_list:
                to_install.extend(pkg_list)

        if not to_install:
            logger.info("All VNC dependencies already installed")
            return True

        # Build install command
        if pm == "apt":
            cmd = ["sudo", "apt", "install", "-y"] + to_install
        elif pm == "dnf":
            cmd = ["sudo", "dnf", "install", "-y"] + to_install
        elif pm == "brew":
            cmd = ["brew", "install"] + to_install
        else:
            raise RuntimeError(f"Unsupported package manager: {pm}")

        logger.info("Installing VNC dependencies: %s", " ".join(to_install))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,  # 5 minute timeout
            )

            if process.returncode == 0:
                logger.info("VNC dependencies installed successfully")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error("Failed to install VNC dependencies: %s", error_msg)
                return False

        except TimeoutError:
            logger.error("VNC dependency installation timed out")
            return False
        except Exception as e:
            logger.error("Failed to install VNC dependencies: %s", e)
            return False

    def get_session(self, display: str) -> VNCSession | None:
        """Get session info for a display.

        Args:
            display: X display string

        Returns:
            VNCSession if exists, None otherwise.
        """
        return self.active_sessions.get(display)

    def list_sessions(self) -> list[VNCSession]:
        """List all active VNC sessions.

        Returns:
            List of active VNCSession objects.
        """
        return list(self.active_sessions.values())
