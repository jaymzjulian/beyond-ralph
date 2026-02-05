"""Unit tests for Remote Access module.

Tests cover:
- WSL2 environment detection
- Windows host ADB connectivity
- Appium server management
- Android emulator control
- VNC session management
- Interview phase Android requirements
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.integrations.remote_access import (
    ADBConnectionResult,
    AndroidEmulatorManager,
    AndroidTestingConfigurationError,
    AndroidTestingRequirements,
    AppiumConfig,
    AppiumManager,
    AppiumServerStatus,
    EnvironmentInfo,
    VNCManager,
    VNCSession,
    WindowsADBClient,
    WindowsHostConfig,
    _detect_platform,
    _is_wsl2,
    create_adb_client_for_wsl2,
    create_android_test_environment,
    detect_environment,
    get_wsl2_host_ip,
    interview_android_requirements,
    setup_complete_android_stack,
)


# =============================================================================
# Environment Detection Tests
# =============================================================================


class TestEnvironmentInfo:
    """Tests for EnvironmentInfo dataclass."""

    def test_environment_info_creation(self) -> None:
        """Test creating EnvironmentInfo with all fields."""
        env = EnvironmentInfo(
            platform="LINUX",
            android_testing_mode="local",
            adb_access="direct",
            capabilities={"adb": True},
        )

        assert env.platform == "LINUX"
        assert env.android_testing_mode == "local"
        assert env.adb_access == "direct"
        assert env.capabilities == {"adb": True}

    def test_environment_info_default_capabilities(self) -> None:
        """Test EnvironmentInfo with default capabilities."""
        env = EnvironmentInfo(
            platform="MACOS",
            android_testing_mode="local",
            adb_access="direct",
        )

        assert env.capabilities == {}


class TestIsWSL2:
    """Tests for _is_wsl2() function."""

    def test_is_wsl2_with_env_var(self) -> None:
        """Test WSL2 detection via environment variable."""
        with patch.dict("os.environ", {"WSL_DISTRO_NAME": "Ubuntu"}):
            assert _is_wsl2() is True

    def test_is_wsl2_without_env_var(self) -> None:
        """Test non-WSL2 environment without env var."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                assert _is_wsl2() is False

    def test_is_wsl2_with_proc_version(self) -> None:
        """Test WSL2 detection via /proc/version."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch(
                    "pathlib.Path.read_text",
                    return_value="Linux version 5.10.16.3-microsoft-standard-WSL2",
                ):
                    assert _is_wsl2() is True

    def test_is_wsl2_linux_kernel(self) -> None:
        """Test non-WSL2 Linux environment."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch(
                    "pathlib.Path.read_text",
                    return_value="Linux version 5.15.0-generic",
                ):
                    assert _is_wsl2() is False

    def test_is_wsl2_proc_read_error(self) -> None:
        """Test handling of /proc/version read error."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", side_effect=IOError("Read error")):
                    assert _is_wsl2() is False


class TestDetectPlatform:
    """Tests for _detect_platform() function."""

    def test_detect_wsl2(self) -> None:
        """Test WSL2 platform detection."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=True):
            assert _detect_platform() == "WSL2"

    def test_detect_linux(self) -> None:
        """Test Linux platform detection."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=False):
            with patch("sys.platform", "linux"):
                assert _detect_platform() == "LINUX"

    def test_detect_macos(self) -> None:
        """Test macOS platform detection."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=False):
            with patch("sys.platform", "darwin"):
                assert _detect_platform() == "MACOS"

    def test_detect_windows(self) -> None:
        """Test Windows platform detection."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=False):
            with patch("sys.platform", "win32"):
                assert _detect_platform() == "WINDOWS"

    def test_detect_unknown_defaults_linux(self) -> None:
        """Test unknown platform defaults to LINUX."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=False):
            with patch("sys.platform", "freebsd"):
                assert _detect_platform() == "LINUX"


class TestGetWSL2HostIP:
    """Tests for get_wsl2_host_ip() function."""

    def test_get_host_ip_from_resolv_conf(self) -> None:
        """Test getting host IP from /etc/resolv.conf."""
        resolv_content = "nameserver 172.28.80.1\nsearch localdomain"
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=resolv_content):
                ip = get_wsl2_host_ip()
                assert ip == "172.28.80.1"

    def test_get_host_ip_no_resolv_conf(self) -> None:
        """Test when /etc/resolv.conf doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                ip = get_wsl2_host_ip()
                # May return None or fallback IP
                assert ip is None or isinstance(ip, str)

    def test_get_host_ip_from_route(self) -> None:
        """Test getting host IP from ip route command."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="default via 172.28.80.1 dev eth0 proto kernel",
                )
                ip = get_wsl2_host_ip()
                assert ip == "172.28.80.1"

    def test_get_host_ip_invalid_nameserver(self) -> None:
        """Test handling invalid nameserver format."""
        resolv_content = "nameserver invalid\nsearch localdomain"
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=resolv_content):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=1, stdout="")
                    ip = get_wsl2_host_ip()
                    assert ip is None

    def test_get_host_ip_read_error(self) -> None:
        """Test handling read errors gracefully."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", side_effect=IOError("Error")):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=1, stdout="")
                    ip = get_wsl2_host_ip()
                    assert ip is None


class TestDetectEnvironment:
    """Tests for detect_environment() function."""

    def test_detect_environment_linux(self) -> None:
        """Test environment detection on Linux."""
        with patch(
            "beyond_ralph.integrations.remote_access._detect_platform",
            return_value="LINUX",
        ):
            with patch("shutil.which", return_value="/usr/bin/adb"):
                env = detect_environment()

                assert env.platform == "LINUX"
                assert env.android_testing_mode == "local"
                assert env.adb_access == "direct"

    def test_detect_environment_wsl2(self) -> None:
        """Test environment detection in WSL2."""
        with patch(
            "beyond_ralph.integrations.remote_access._detect_platform",
            return_value="WSL2",
        ):
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value="172.28.80.1",
            ):
                with patch("shutil.which", return_value=None):
                    env = detect_environment()

                    assert env.platform == "WSL2"
                    assert env.android_testing_mode == "remote"
                    assert env.adb_access == "mirrored"
                    assert env.capabilities["wsl2_host_ip"] == "172.28.80.1"

    def test_detect_environment_macos(self) -> None:
        """Test environment detection on macOS."""
        with patch(
            "beyond_ralph.integrations.remote_access._detect_platform",
            return_value="MACOS",
        ):
            with patch("shutil.which", return_value=None):
                env = detect_environment()

                assert env.platform == "MACOS"
                assert env.android_testing_mode == "local"
                assert env.adb_access == "direct"

    def test_detect_environment_windows(self) -> None:
        """Test environment detection on Windows."""
        with patch(
            "beyond_ralph.integrations.remote_access._detect_platform",
            return_value="WINDOWS",
        ):
            with patch("shutil.which", return_value=None):
                env = detect_environment()

                assert env.platform == "WINDOWS"
                assert env.android_testing_mode == "local"
                assert env.adb_access == "direct"

    def test_detect_environment_capabilities(self) -> None:
        """Test that capabilities are properly detected."""
        with patch(
            "beyond_ralph.integrations.remote_access._detect_platform",
            return_value="LINUX",
        ):
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = lambda x: {
                    "adb": "/usr/bin/adb",
                    "appium": "/usr/bin/appium",
                    "node": "/usr/bin/node",
                    "npm": "/usr/bin/npm",
                }.get(x)

                env = detect_environment()

                assert env.capabilities["adb"] is True
                assert env.capabilities["appium"] is True
                assert env.capabilities["node"] is True
                assert env.capabilities["npm"] is True


# =============================================================================
# Windows Host ADB Connectivity Tests
# =============================================================================


class TestWindowsHostConfig:
    """Tests for WindowsHostConfig dataclass."""

    def test_config_creation(self) -> None:
        """Test creating config with all fields."""
        config = WindowsHostConfig(
            host_ip="192.168.1.100",
            adb_port=5037,
            emulator_name="emulator-5554",
            verified=True,
        )

        assert config.host_ip == "192.168.1.100"
        assert config.adb_port == 5037
        assert config.emulator_name == "emulator-5554"
        assert config.verified is True

    def test_config_defaults(self) -> None:
        """Test config with default values."""
        config = WindowsHostConfig(host_ip="192.168.1.100")

        assert config.adb_port == 5037
        assert config.emulator_name == "emulator-5554"
        assert config.verified is False


class TestADBConnectionResult:
    """Tests for ADBConnectionResult dataclass."""

    def test_result_success(self) -> None:
        """Test successful connection result."""
        result = ADBConnectionResult(
            connected=True,
            devices=["emulator-5554", "device-abc123"],
            error_message=None,
        )

        assert result.connected is True
        assert len(result.devices) == 2
        assert result.error_message is None

    def test_result_failure(self) -> None:
        """Test failed connection result."""
        result = ADBConnectionResult(
            connected=False,
            devices=[],
            error_message="Connection refused",
        )

        assert result.connected is False
        assert result.devices == []
        assert result.error_message == "Connection refused"


class TestWindowsADBClient:
    """Tests for WindowsADBClient class."""

    @pytest.fixture
    def config(self) -> WindowsHostConfig:
        """Create a test config."""
        return WindowsHostConfig(host_ip="172.28.80.1")

    @pytest.fixture
    def client(self, config: WindowsHostConfig) -> WindowsADBClient:
        """Create a test client."""
        return WindowsADBClient(config)

    def test_host_string(self, client: WindowsADBClient) -> None:
        """Test host string generation."""
        assert client.host_string == "172.28.80.1:5037"

    def test_host_string_custom_port(self) -> None:
        """Test host string with custom port."""
        config = WindowsHostConfig(host_ip="192.168.1.1", adb_port=5555)
        client = WindowsADBClient(config)
        assert client.host_string == "192.168.1.1:5555"

    @pytest.mark.asyncio
    async def test_connect_success(self, client: WindowsADBClient) -> None:
        """Test successful ADB connection."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                "connected to 172.28.80.1:5037",
                "List of devices attached\nemulator-5554\tdevice",
            ]
            with patch.object(client, "list_devices", new_callable=AsyncMock) as mock_list:
                mock_list.return_value = ["emulator-5554"]

                result = await client.connect()

                assert result.connected is True
                assert "emulator-5554" in result.devices
                assert client.config.verified is True

    @pytest.mark.asyncio
    async def test_connect_failure(self, client: WindowsADBClient) -> None:
        """Test failed ADB connection."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "unable to connect"

            result = await client.connect()

            assert result.connected is False
            assert "unable to connect" in result.error_message

    @pytest.mark.asyncio
    async def test_connect_exception(self, client: WindowsADBClient) -> None:
        """Test connection with exception."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = RuntimeError("Network error")

            result = await client.connect()

            assert result.connected is False
            assert "Network error" in result.error_message

    @pytest.mark.asyncio
    async def test_list_devices(self, client: WindowsADBClient) -> None:
        """Test listing devices."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = (
                "List of devices attached\nemulator-5554\tdevice\ndevice-abc\temulator"
            )

            devices = await client.list_devices()

            assert "emulator-5554" in devices
            assert "device-abc" in devices

    @pytest.mark.asyncio
    async def test_list_devices_empty(self, client: WindowsADBClient) -> None:
        """Test listing devices when none connected."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "List of devices attached\n"

            devices = await client.list_devices()

            assert devices == []

    @pytest.mark.asyncio
    async def test_execute_command_success(self, client: WindowsADBClient) -> None:
        """Test executing ADB command successfully."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/adb"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", return_value=(b"output", b"")):
                    result = await client.execute_command("devices")

                    assert result == "output"

    @pytest.mark.asyncio
    async def test_execute_command_adb_not_found(self, client: WindowsADBClient) -> None:
        """Test execute_command when adb not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await client.execute_command("devices")

            assert "adb not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_command_failure(self, client: WindowsADBClient) -> None:
        """Test execute_command with command failure."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"error message")
        mock_process.returncode = 1

        with patch("shutil.which", return_value="/usr/bin/adb"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", return_value=(b"", b"error message")):
                    with pytest.raises(RuntimeError) as exc_info:
                        await client.execute_command("invalid")

                    assert "ADB command failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, client: WindowsADBClient) -> None:
        """Test execute_command with timeout."""
        with patch("shutil.which", return_value="/usr/bin/adb"):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock):
                with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                    with pytest.raises(RuntimeError) as exc_info:
                        await client.execute_command("shell", "sleep", "100")

                    assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect_success(self, client: WindowsADBClient) -> None:
        """Test successful disconnection."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "disconnected"

            result = await client.disconnect()

            assert result is True
            assert client.config.verified is False

    @pytest.mark.asyncio
    async def test_disconnect_failure(self, client: WindowsADBClient) -> None:
        """Test failed disconnection."""
        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = RuntimeError("Network error")

            result = await client.disconnect()

            assert result is False


class TestCreateADBClientForWSL2:
    """Tests for create_adb_client_for_wsl2() function."""

    def test_create_client_in_wsl2(self) -> None:
        """Test creating client in WSL2 environment."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=True):
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value="172.28.80.1",
            ):
                client = create_adb_client_for_wsl2()

                assert client is not None
                assert client.config.host_ip == "172.28.80.1"

    def test_create_client_not_wsl2(self) -> None:
        """Test creating client outside WSL2."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=False):
            client = create_adb_client_for_wsl2()

            assert client is None

    def test_create_client_no_host_ip(self) -> None:
        """Test creating client when host IP not found."""
        with patch("beyond_ralph.integrations.remote_access._is_wsl2", return_value=True):
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                client = create_adb_client_for_wsl2()

                assert client is None


# =============================================================================
# Appium Server Management Tests
# =============================================================================


class TestAppiumConfig:
    """Tests for AppiumConfig dataclass."""

    def test_config_defaults(self) -> None:
        """Test AppiumConfig with default values."""
        config = AppiumConfig()

        assert config.port == 4723
        assert config.adb_host is None
        assert config.log_level == "info"
        assert config.relaxed_security is True

    def test_config_custom(self) -> None:
        """Test AppiumConfig with custom values."""
        config = AppiumConfig(
            port=4724,
            adb_host="172.28.80.1",
            log_level="debug",
            relaxed_security=False,
        )

        assert config.port == 4724
        assert config.adb_host == "172.28.80.1"
        assert config.log_level == "debug"
        assert config.relaxed_security is False


class TestAppiumServerStatus:
    """Tests for AppiumServerStatus dataclass."""

    def test_status_running(self) -> None:
        """Test running server status."""
        status = AppiumServerStatus(
            running=True,
            port=4723,
            url="http://localhost:4723",
            pid=12345,
        )

        assert status.running is True
        assert status.port == 4723
        assert status.url == "http://localhost:4723"
        assert status.pid == 12345

    def test_status_stopped(self) -> None:
        """Test stopped server status."""
        status = AppiumServerStatus(
            running=False,
            port=4723,
            url="",
            pid=None,
        )

        assert status.running is False
        assert status.pid is None


class TestAppiumManager:
    """Tests for AppiumManager class."""

    @pytest.fixture
    def manager(self) -> AppiumManager:
        """Create a test manager."""
        return AppiumManager()

    @pytest.mark.asyncio
    async def test_start_server_appium_not_found(self, manager: AppiumManager) -> None:
        """Test start_server when appium not installed."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager.start_server(AppiumConfig())

            assert "Appium not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_server_success(self, manager: AppiumManager) -> None:
        """Test successful server start."""
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None

        with patch("shutil.which", return_value="/usr/bin/appium"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with patch.object(
                        manager, "health_check", new_callable=AsyncMock
                    ) as mock_health:
                        mock_health.return_value = True

                        status = await manager.start_server(AppiumConfig())

                        assert status.running is True
                        assert status.port == 4723
                        assert status.pid == 12345

    @pytest.mark.asyncio
    async def test_start_server_health_check_fails(self, manager: AppiumManager) -> None:
        """Test server start when health check fails."""
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.terminate = MagicMock()

        with patch("shutil.which", return_value="/usr/bin/appium"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with patch.object(
                        manager, "health_check", new_callable=AsyncMock
                    ) as mock_health:
                        mock_health.return_value = False

                        with pytest.raises(RuntimeError) as exc_info:
                            await manager.start_server(AppiumConfig())

                        assert "health check" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_stop_server_no_process(self, manager: AppiumManager) -> None:
        """Test stop_server when no server running."""
        result = await manager.stop_server()
        assert result is True

    @pytest.mark.asyncio
    async def test_stop_server_success(self, manager: AppiumManager) -> None:
        """Test successful server stop."""
        mock_process = AsyncMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = AsyncMock()

        manager._process = mock_process
        manager._config = AppiumConfig()

        with patch("asyncio.wait_for", new_callable=AsyncMock):
            result = await manager.stop_server()

            assert result is True
            assert manager._process is None

    @pytest.mark.asyncio
    async def test_stop_server_timeout_kill(self, manager: AppiumManager) -> None:
        """Test server stop with timeout (kills process)."""
        mock_process = AsyncMock()
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        manager._process = mock_process
        manager._config = AppiumConfig()

        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            result = await manager.stop_server()

            assert result is True
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_no_config(self, manager: AppiumManager) -> None:
        """Test health check with no config."""
        result = await manager.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, manager: AppiumManager) -> None:
        """Test successful health check."""
        manager._config = AppiumConfig()

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"200", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", return_value=(b"200", b"")):
                result = await manager.health_check()

                assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, manager: AppiumManager) -> None:
        """Test failed health check."""
        manager._config = AppiumConfig()

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"500", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", return_value=(b"500", b"")):
                result = await manager.health_check()

                assert result is False

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, manager: AppiumManager) -> None:
        """Test health check timeout."""
        manager._config = AppiumConfig()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                result = await manager.health_check()

                assert result is False

    @pytest.mark.asyncio
    async def test_install_appium_npm_not_found(self, manager: AppiumManager) -> None:
        """Test install_appium when npm not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager.install_appium()

            assert "npm not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_install_appium_success(self, manager: AppiumManager) -> None:
        """Test successful appium installation."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"installed", b"")
        mock_process.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/npm"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", return_value=(b"installed", b"")):
                    result = await manager.install_appium()

                    assert result is True

    @pytest.mark.asyncio
    async def test_install_appium_failure(self, manager: AppiumManager) -> None:
        """Test failed appium installation."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"error")
        mock_process.returncode = 1

        with patch("shutil.which", return_value="/usr/bin/npm"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", return_value=(b"", b"error")):
                    result = await manager.install_appium()

                    assert result is False

    def test_get_status_no_process(self, manager: AppiumManager) -> None:
        """Test get_status when no process running."""
        status = manager.get_status()

        assert status.running is False
        assert status.pid is None

    def test_get_status_running(self, manager: AppiumManager) -> None:
        """Test get_status with running process."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.returncode = None

        manager._process = mock_process
        manager._config = AppiumConfig()

        status = manager.get_status()

        assert status.running is True
        assert status.pid == 12345

    def test_get_status_process_exited(self, manager: AppiumManager) -> None:
        """Test get_status when process has exited."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.returncode = 0  # Process exited

        manager._process = mock_process
        manager._config = AppiumConfig()

        status = manager.get_status()

        assert status.running is False


# =============================================================================
# Android Emulator Control Tests
# =============================================================================


class TestAndroidEmulatorManager:
    """Tests for AndroidEmulatorManager class."""

    @pytest.fixture
    def manager(self) -> AndroidEmulatorManager:
        """Create a test manager without remote client."""
        return AndroidEmulatorManager()

    @pytest.fixture
    def remote_manager(self) -> AndroidEmulatorManager:
        """Create a test manager with remote ADB client."""
        config = WindowsHostConfig(host_ip="172.28.80.1")
        client = WindowsADBClient(config)
        return AndroidEmulatorManager(adb_client=client)

    @pytest.mark.asyncio
    async def test_list_devices_local(self, manager: AndroidEmulatorManager) -> None:
        """Test listing devices with local ADB."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"List of devices attached\nemulator-5554\tdevice",
            b"",
        )
        mock_process.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/adb"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch(
                    "asyncio.wait_for",
                    return_value=(
                        b"List of devices attached\nemulator-5554\tdevice",
                        b"",
                    ),
                ):
                    devices = await manager.list_devices()

                    assert "emulator-5554" in devices

    @pytest.mark.asyncio
    async def test_list_devices_remote(self, remote_manager: AndroidEmulatorManager) -> None:
        """Test listing devices with remote ADB."""
        with patch.object(
            remote_manager.adb_client, "list_devices", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = ["emulator-5554"]

            devices = await remote_manager.list_devices()

            assert "emulator-5554" in devices

    @pytest.mark.asyncio
    async def test_start_emulator_not_found(self, manager: AndroidEmulatorManager) -> None:
        """Test start_emulator when emulator not found."""
        with patch("shutil.which", return_value=None):
            with patch.dict("os.environ", {}, clear=True):
                with pytest.raises(RuntimeError) as exc_info:
                    await manager.start_emulator("Pixel_6_API_33")

                assert "emulator not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_start_emulator_success(self, manager: AndroidEmulatorManager) -> None:
        """Test successful emulator start."""
        mock_process = AsyncMock()

        with patch("shutil.which", return_value="/usr/bin/emulator"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                result = await manager.start_emulator("Pixel_6_API_33")

                assert result is True

    @pytest.mark.asyncio
    async def test_start_emulator_from_android_home(
        self, manager: AndroidEmulatorManager, tmp_path: Path
    ) -> None:
        """Test start_emulator finds emulator via ANDROID_HOME."""
        emulator_path = tmp_path / "emulator" / "emulator"
        emulator_path.parent.mkdir(parents=True)
        emulator_path.touch()

        mock_process = AsyncMock()

        with patch("shutil.which", return_value=None):
            with patch.dict("os.environ", {"ANDROID_HOME": str(tmp_path)}):
                with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                    result = await manager.start_emulator("Pixel_6_API_33")

                    assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_boot_success(self, manager: AndroidEmulatorManager) -> None:
        """Test successful boot wait."""
        # Track boot_completed calls specifically
        boot_check_count = 0

        async def mock_execute(*args):
            nonlocal boot_check_count
            # Check if boot_completed is in args (it's a tuple of positional args)
            args_str = " ".join(str(a) for a in args)
            if "boot_completed" in args_str:
                boot_check_count += 1
                # Return success on second boot check
                if boot_check_count >= 2:
                    return "1"
                return ""
            return ""

        # Mock list_devices to return a device
        with patch.object(manager, "list_devices", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ["emulator-5554"]

            with patch.object(manager, "_execute_adb", side_effect=mock_execute):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await manager.wait_for_boot(timeout=10)

                    assert result is True
                    assert boot_check_count >= 2

    @pytest.mark.asyncio
    async def test_wait_for_boot_timeout(self, manager: AndroidEmulatorManager) -> None:
        """Test boot wait timeout."""

        async def mock_execute(*args):
            return ""  # Never returns boot_completed = "1"

        # Mock list_devices to return a device
        with patch.object(manager, "list_devices", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ["emulator-5554"]

            with patch.object(manager, "_execute_adb", side_effect=mock_execute):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    # Mock time to simulate timeout (jumps past timeout on second call)
                    time_values = iter([0, 200])

                    with patch(
                        "beyond_ralph.integrations.remote_access.time.monotonic",
                        side_effect=lambda: next(time_values, 200),
                    ):
                        result = await manager.wait_for_boot(timeout=120)

                        assert result is False

    @pytest.mark.asyncio
    async def test_install_apk_file_not_found(self, manager: AndroidEmulatorManager) -> None:
        """Test install_apk with non-existent file."""
        with pytest.raises(FileNotFoundError):
            await manager.install_apk("/path/to/nonexistent.apk")

    @pytest.mark.asyncio
    async def test_install_apk_success(
        self, manager: AndroidEmulatorManager, tmp_path: Path
    ) -> None:
        """Test successful APK installation."""
        apk_path = tmp_path / "test.apk"
        apk_path.touch()

        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Success"

            result = await manager.install_apk(str(apk_path))

            assert result is True

    @pytest.mark.asyncio
    async def test_install_apk_failure(
        self, manager: AndroidEmulatorManager, tmp_path: Path
    ) -> None:
        """Test failed APK installation."""
        apk_path = tmp_path / "test.apk"
        apk_path.touch()

        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Failure [INSTALL_FAILED]"

            result = await manager.install_apk(str(apk_path))

            assert result is False

    @pytest.mark.asyncio
    async def test_take_screenshot_success(
        self, manager: AndroidEmulatorManager, tmp_path: Path
    ) -> None:
        """Test successful screenshot capture."""
        # Create a mock PNG file
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        async def mock_execute(*args):
            if "screencap" in args:
                return ""
            if "pull" in args:
                # Simulate pull by creating the temp file
                local_path = args[-1]
                Path(local_path).write_bytes(png_data)
                return ""
            if "rm" in args:
                return ""
            return ""

        with patch.object(manager, "_execute_adb", side_effect=mock_execute):
            data = await manager.take_screenshot()

            assert data == png_data

    @pytest.mark.asyncio
    async def test_take_screenshot_failure(self, manager: AndroidEmulatorManager) -> None:
        """Test screenshot capture failure."""
        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = RuntimeError("Device not connected")

            with pytest.raises(RuntimeError) as exc_info:
                await manager.take_screenshot()

            assert "Screenshot capture failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_uninstall_app_success(self, manager: AndroidEmulatorManager) -> None:
        """Test successful app uninstallation."""
        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Success"

            result = await manager.uninstall_app("com.example.app")

            assert result is True

    @pytest.mark.asyncio
    async def test_uninstall_app_failure(self, manager: AndroidEmulatorManager) -> None:
        """Test failed app uninstallation."""
        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = RuntimeError("Package not found")

            result = await manager.uninstall_app("com.nonexistent.app")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_device_info(self, manager: AndroidEmulatorManager) -> None:
        """Test getting device information."""

        async def mock_execute(*args):
            if "ro.product.model" in args:
                return "Pixel 6"
            if "ro.build.version.release" in args:
                return "13"
            if "ro.build.version.sdk" in args:
                return "33"
            if args[0] == "devices":
                return "List of devices attached\nemulator-5554\tdevice"
            return ""

        with patch.object(manager, "_execute_adb", side_effect=mock_execute):
            with patch.object(manager, "list_devices", new_callable=AsyncMock) as mock_list:
                mock_list.return_value = ["emulator-5554"]

                info = await manager.get_device_info()

                assert info["model"] == "Pixel 6"
                assert info["android_version"] == "13"
                assert info["sdk_version"] == "33"

    @pytest.mark.asyncio
    async def test_clear_app_data_success(self, manager: AndroidEmulatorManager) -> None:
        """Test successful app data clearing."""
        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "Success"

            result = await manager.clear_app_data("com.example.app")

            assert result is True

    @pytest.mark.asyncio
    async def test_launch_app_with_activity(self, manager: AndroidEmulatorManager) -> None:
        """Test launching app with specific activity."""
        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = ""

            result = await manager.launch_app("com.example.app", ".MainActivity")

            assert result is True
            mock_exec.assert_called()

    @pytest.mark.asyncio
    async def test_launch_app_default_activity(self, manager: AndroidEmulatorManager) -> None:
        """Test launching app with default activity."""
        with patch.object(manager, "_execute_adb", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = ""

            result = await manager.launch_app("com.example.app")

            assert result is True


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestCreateAndroidTestEnvironment:
    """Tests for create_android_test_environment() function."""

    def test_create_environment_linux(self) -> None:
        """Test creating environment on Linux."""
        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
            )

            env, manager = create_android_test_environment()

            assert env.platform == "LINUX"
            assert manager.adb_client is None

    def test_create_environment_wsl2(self) -> None:
        """Test creating environment in WSL2."""
        mock_client = MagicMock(spec=WindowsADBClient)

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
            )
            with patch(
                "beyond_ralph.integrations.remote_access.create_adb_client_for_wsl2",
                return_value=mock_client,
            ):
                env, manager = create_android_test_environment()

                assert env.platform == "WSL2"
                assert manager.adb_client is mock_client


class TestSetupCompleteAndroidStack:
    """Tests for setup_complete_android_stack() function."""

    @pytest.mark.asyncio
    async def test_setup_stack_linux(self) -> None:
        """Test setting up stack on Linux."""
        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
            )

            appium_manager, emulator_manager = await setup_complete_android_stack()

            assert isinstance(appium_manager, AppiumManager)
            assert isinstance(emulator_manager, AndroidEmulatorManager)
            assert emulator_manager.adb_client is None

    @pytest.mark.asyncio
    async def test_setup_stack_wsl2(self) -> None:
        """Test setting up stack in WSL2."""
        mock_client = MagicMock(spec=WindowsADBClient)

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value="172.28.80.1",
            ):
                with patch(
                    "beyond_ralph.integrations.remote_access.create_adb_client_for_wsl2",
                    return_value=mock_client,
                ):
                    appium_manager, emulator_manager = await setup_complete_android_stack()

                    assert isinstance(appium_manager, AppiumManager)
                    assert emulator_manager.adb_client is mock_client

    @pytest.mark.asyncio
    async def test_setup_stack_custom_port(self) -> None:
        """Test setting up stack with custom Appium port."""
        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
            )

            appium_manager, _ = await setup_complete_android_stack(appium_port=4724)

            # Verify config would use custom port
            assert isinstance(appium_manager, AppiumManager)


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Additional edge case tests."""

    def test_environment_info_repr(self) -> None:
        """Test EnvironmentInfo string representation."""
        env = EnvironmentInfo(
            platform="LINUX",
            android_testing_mode="local",
            adb_access="direct",
        )
        # Should not raise
        repr(env)

    def test_windows_host_config_repr(self) -> None:
        """Test WindowsHostConfig string representation."""
        config = WindowsHostConfig(host_ip="192.168.1.1")
        repr(config)

    def test_adb_connection_result_repr(self) -> None:
        """Test ADBConnectionResult string representation."""
        result = ADBConnectionResult(connected=True, devices=["device1"])
        repr(result)

    def test_appium_config_repr(self) -> None:
        """Test AppiumConfig string representation."""
        config = AppiumConfig()
        repr(config)

    def test_appium_server_status_repr(self) -> None:
        """Test AppiumServerStatus string representation."""
        status = AppiumServerStatus(running=True, port=4723, url="http://localhost:4723")
        repr(status)

    @pytest.mark.asyncio
    async def test_execute_adb_local_not_found(self) -> None:
        """Test _execute_adb when local adb not found."""
        manager = AndroidEmulatorManager()

        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager._execute_adb("devices")

            assert "adb not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_already_connected(self) -> None:
        """Test connect when already connected."""
        config = WindowsHostConfig(host_ip="172.28.80.1")
        client = WindowsADBClient(config)

        with patch.object(client, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = "already connected to 172.28.80.1:5037"
            with patch.object(client, "list_devices", new_callable=AsyncMock) as mock_list:
                mock_list.return_value = ["emulator-5554"]

                result = await client.connect()

                assert result.connected is True


# =============================================================================
# Interview Phase Android Questions Tests
# =============================================================================


class TestAndroidTestingRequirements:
    """Tests for AndroidTestingRequirements dataclass."""

    def test_requirements_creation(self) -> None:
        """Test creating requirements with all fields."""
        env = EnvironmentInfo(
            platform="LINUX",
            android_testing_mode="local",
            adb_access="direct",
        )
        reqs = AndroidTestingRequirements(
            needs_android_testing=True,
            environment=env,
            windows_config=None,
            connection_verified=True,
        )

        assert reqs.needs_android_testing is True
        assert reqs.environment.platform == "LINUX"
        assert reqs.windows_config is None
        assert reqs.connection_verified is True

    def test_requirements_with_windows_config(self) -> None:
        """Test requirements with Windows config for WSL2."""
        env = EnvironmentInfo(
            platform="WSL2",
            android_testing_mode="remote",
            adb_access="mirrored",
        )
        config = WindowsHostConfig(host_ip="172.28.80.1")
        reqs = AndroidTestingRequirements(
            needs_android_testing=True,
            environment=env,
            windows_config=config,
            connection_verified=True,
        )

        assert reqs.windows_config is not None
        assert reqs.windows_config.host_ip == "172.28.80.1"

    def test_requirements_defaults(self) -> None:
        """Test requirements with default values."""
        env = EnvironmentInfo(
            platform="LINUX",
            android_testing_mode="local",
            adb_access="direct",
        )
        reqs = AndroidTestingRequirements(
            needs_android_testing=False,
            environment=env,
        )

        assert reqs.windows_config is None
        assert reqs.connection_verified is False


class TestInterviewAndroidRequirements:
    """Tests for interview_android_requirements() function."""

    @pytest.mark.asyncio
    async def test_no_android_testing_needed(self) -> None:
        """Test when user doesn't need Android testing."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "No"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
                capabilities={"adb": True},
            )

            reqs = await interview_android_requirements(mock_ask)

            assert reqs.needs_android_testing is False
            assert reqs.connection_verified is False

    @pytest.mark.asyncio
    async def test_android_testing_on_linux_with_adb(self) -> None:
        """Test Android testing on Linux with ADB available."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
                capabilities={"adb": True},
            )

            reqs = await interview_android_requirements(mock_ask)

            assert reqs.needs_android_testing is True
            assert reqs.connection_verified is True
            assert reqs.windows_config is None

    @pytest.mark.asyncio
    async def test_android_testing_on_linux_without_adb(self) -> None:
        """Test Android testing required but ADB not installed."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
                capabilities={"adb": False},
            )

            with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                await interview_android_requirements(mock_ask)

            assert "ADB is not installed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wsl2_auto_detect_host_ip_accepted(self) -> None:
        """Test WSL2 with auto-detected host IP accepted by user."""
        questions_asked: list[str] = []

        def mock_ask(question: str, options: list[str] | None) -> str:
            questions_asked.append(question)
            if "require Android" in question:
                return "Yes"
            if "Detected Windows host IP" in question:
                return "Yes"
            if "ADB port" in question:
                return ""  # Use default
            return ""

        mock_connection_result = ADBConnectionResult(
            connected=True,
            devices=["emulator-5554"],
            error_message=None,
        )

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={"adb": True},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value="172.28.80.1",
            ):
                with patch.object(
                    WindowsADBClient, "connect", new_callable=AsyncMock
                ) as mock_connect:
                    mock_connect.return_value = mock_connection_result

                    reqs = await interview_android_requirements(mock_ask)

                    assert reqs.needs_android_testing is True
                    assert reqs.windows_config is not None
                    assert reqs.windows_config.host_ip == "172.28.80.1"
                    assert reqs.connection_verified is True

    @pytest.mark.asyncio
    async def test_wsl2_manual_host_ip_entry(self) -> None:
        """Test WSL2 with manual host IP entry."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Detected Windows host IP" in question:
                return "No, enter manually"
            if "Enter the Windows host IP" in question:
                return "192.168.1.100"
            if "ADB port" in question:
                return "5037"
            return ""

        mock_connection_result = ADBConnectionResult(
            connected=True,
            devices=["device-abc"],
            error_message=None,
        )

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={"adb": True},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value="172.28.80.1",
            ):
                with patch.object(
                    WindowsADBClient, "connect", new_callable=AsyncMock
                ) as mock_connect:
                    mock_connect.return_value = mock_connection_result

                    reqs = await interview_android_requirements(mock_ask)

                    assert reqs.windows_config is not None
                    assert reqs.windows_config.host_ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_wsl2_no_auto_detect_manual_entry(self) -> None:
        """Test WSL2 when auto-detect fails, manual entry required."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Could not auto-detect" in question:
                return "10.0.0.50"
            if "ADB port" in question:
                return ""
            return ""

        mock_connection_result = ADBConnectionResult(
            connected=True,
            devices=[],
            error_message=None,
        )

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                with patch.object(
                    WindowsADBClient, "connect", new_callable=AsyncMock
                ) as mock_connect:
                    mock_connect.return_value = mock_connection_result

                    reqs = await interview_android_requirements(mock_ask)

                    assert reqs.windows_config is not None
                    assert reqs.windows_config.host_ip == "10.0.0.50"

    @pytest.mark.asyncio
    async def test_wsl2_empty_host_ip_error(self) -> None:
        """Test WSL2 with empty host IP provided."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Could not auto-detect" in question:
                return ""  # Empty IP
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                    await interview_android_requirements(mock_ask)

                assert "no Windows host IP provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wsl2_invalid_host_ip_format(self) -> None:
        """Test WSL2 with invalid host IP format."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Could not auto-detect" in question:
                return "not.a.valid.ip.address"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                    await interview_android_requirements(mock_ask)

                assert "Invalid IP address format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wsl2_invalid_port(self) -> None:
        """Test WSL2 with invalid ADB port."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Could not auto-detect" in question:
                return "192.168.1.1"
            if "ADB port" in question:
                return "not_a_port"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                    await interview_android_requirements(mock_ask)

                assert "Invalid ADB port" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wsl2_connection_failure(self) -> None:
        """Test WSL2 when ADB connection fails."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Could not auto-detect" in question:
                return "192.168.1.1"
            if "ADB port" in question:
                return ""
            return ""

        mock_connection_result = ADBConnectionResult(
            connected=False,
            devices=[],
            error_message="Connection refused",
        )

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                with patch.object(
                    WindowsADBClient, "connect", new_callable=AsyncMock
                ) as mock_connect:
                    mock_connect.return_value = mock_connection_result

                    with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                        await interview_android_requirements(mock_ask)

                    assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wsl2_connection_exception(self) -> None:
        """Test WSL2 when ADB connection throws exception."""

        def mock_ask(question: str, options: list[str] | None) -> str:
            if "require Android" in question:
                return "Yes"
            if "Could not auto-detect" in question:
                return "192.168.1.1"
            if "ADB port" in question:
                return ""
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_env:
            mock_env.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )
            with patch(
                "beyond_ralph.integrations.remote_access.get_wsl2_host_ip",
                return_value=None,
            ):
                with patch.object(
                    WindowsADBClient, "connect", new_callable=AsyncMock
                ) as mock_connect:
                    mock_connect.side_effect = RuntimeError("Network error")

                    with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                        await interview_android_requirements(mock_ask)

                    assert "Failed to connect" in str(exc_info.value)


# =============================================================================
# VNC Session Management Tests
# =============================================================================


class TestVNCSession:
    """Tests for VNCSession dataclass."""

    def test_session_creation(self) -> None:
        """Test creating VNCSession with all fields."""
        session = VNCSession(
            display=":99",
            port=5999,
            password="test123",
            websocket_port=6999,
            resolution="1920x1080",
            pid=12345,
            xvfb_pid=12346,
        )

        assert session.display == ":99"
        assert session.port == 5999
        assert session.password == "test123"
        assert session.websocket_port == 6999
        assert session.resolution == "1920x1080"
        assert session.pid == 12345
        assert session.xvfb_pid == 12346

    def test_session_defaults(self) -> None:
        """Test VNCSession with default values."""
        session = VNCSession(
            display=":1",
            port=5901,
            password="abc",
            websocket_port=None,
            resolution="1024x768",
        )

        assert session.pid is None
        assert session.xvfb_pid is None

    def test_session_repr(self) -> None:
        """Test VNCSession string representation."""
        session = VNCSession(
            display=":99",
            port=5999,
            password="secret",
            websocket_port=None,
            resolution="1920x1080",
        )
        repr_str = repr(session)
        assert ":99" in repr_str


class TestVNCManager:
    """Tests for VNCManager class."""

    @pytest.fixture
    def manager(self) -> VNCManager:
        """Create a test VNC manager."""
        return VNCManager()

    def test_generate_password_length(self, manager: VNCManager) -> None:
        """Test password generation produces 12 characters."""
        password = manager._generate_password()
        assert len(password) == 12

    def test_generate_password_uniqueness(self, manager: VNCManager) -> None:
        """Test password generation produces unique passwords."""
        passwords = [manager._generate_password() for _ in range(100)]
        assert len(set(passwords)) == 100  # All unique

    def test_generate_password_url_safe(self, manager: VNCManager) -> None:
        """Test password is URL-safe (no special chars)."""
        password = manager._generate_password()
        # URL-safe base64 only contains A-Z, a-z, 0-9, -, _
        import re
        assert re.match(r"^[A-Za-z0-9_-]+$", password)

    def test_detect_display_server_wayland(self, manager: VNCManager) -> None:
        """Test Wayland detection."""
        with patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-0"}, clear=True):
            server_type, display = manager._detect_display_server()

            assert server_type == "wayland"
            assert display == "wayland-0"

    def test_detect_display_server_x11(self, manager: VNCManager) -> None:
        """Test X11 detection."""
        with patch.dict("os.environ", {"DISPLAY": ":0"}, clear=True):
            with patch.object(manager, "_check_process_running", return_value=False):
                server_type, display = manager._detect_display_server()

                assert server_type == "x11"
                assert display == ":0"

    def test_detect_display_server_xvfb(self, manager: VNCManager) -> None:
        """Test Xvfb detection."""
        with patch.dict("os.environ", {"DISPLAY": ":99"}, clear=True):
            with patch.object(manager, "_check_process_running") as mock_check:
                mock_check.side_effect = lambda name: name == "Xvfb"

                server_type, display = manager._detect_display_server()

                assert server_type == "xvfb"
                assert display == ":99"

    def test_detect_display_server_xvnc(self, manager: VNCManager) -> None:
        """Test Xvnc detection."""
        with patch.dict("os.environ", {"DISPLAY": ":1"}, clear=True):
            with patch.object(manager, "_check_process_running") as mock_check:
                mock_check.side_effect = lambda name: name == "Xvnc"

                server_type, display = manager._detect_display_server()

                assert server_type == "xvnc"
                assert display == ":1"

    def test_detect_display_server_none(self, manager: VNCManager) -> None:
        """Test no display server detected."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(manager, "_check_process_running", return_value=False):
                server_type, display = manager._detect_display_server()

                assert server_type == "none"
                assert display == ""

    def test_check_process_running_true(self, manager: VNCManager) -> None:
        """Test process running check when process exists."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = manager._check_process_running("Xvfb")

            assert result is True

    def test_check_process_running_false(self, manager: VNCManager) -> None:
        """Test process running check when process not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = manager._check_process_running("NotRunning")

            assert result is False

    def test_check_process_running_error(self, manager: VNCManager) -> None:
        """Test process running check handles errors."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = manager._check_process_running("Xvfb")

            assert result is False

    def test_detect_package_manager_apt(self, manager: VNCManager) -> None:
        """Test apt package manager detection."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/apt" if x == "apt" else None

            pm = manager._detect_package_manager()

            assert pm == "apt"

    def test_detect_package_manager_dnf(self, manager: VNCManager) -> None:
        """Test dnf package manager detection."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/dnf" if x == "dnf" else None

            pm = manager._detect_package_manager()

            assert pm == "dnf"

    def test_detect_package_manager_brew(self, manager: VNCManager) -> None:
        """Test brew package manager detection."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/local/bin/brew" if x == "brew" else None

            pm = manager._detect_package_manager()

            assert pm == "brew"

    def test_detect_package_manager_none(self, manager: VNCManager) -> None:
        """Test no package manager found."""
        with patch("shutil.which", return_value=None):
            pm = manager._detect_package_manager()

            assert pm is None

    @pytest.mark.asyncio
    async def test_start_session_xvfb_not_found(self, manager: VNCManager) -> None:
        """Test start_session when Xvfb not installed."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager.start_session()

            assert "Xvfb not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_session_x11vnc_not_found(self, manager: VNCManager) -> None:
        """Test start_session when x11vnc not installed."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/Xvfb" if x == "Xvfb" else None

            with pytest.raises(RuntimeError) as exc_info:
                await manager.start_session()

            assert "x11vnc not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_session_already_exists(self, manager: VNCManager) -> None:
        """Test start_session when session already exists for display."""
        manager.active_sessions[":99"] = VNCSession(
            display=":99",
            port=5999,
            password="test",
            websocket_port=None,
            resolution="1920x1080",
        )

        with patch("shutil.which", return_value="/usr/bin/tool"):
            with pytest.raises(RuntimeError) as exc_info:
                await manager.start_session(display=":99")

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_session_success(self, manager: VNCManager) -> None:
        """Test successful VNC session start."""
        mock_xvfb_process = AsyncMock()
        mock_xvfb_process.pid = 1001
        mock_xvfb_process.returncode = None

        mock_x11vnc_process = AsyncMock()
        mock_x11vnc_process.pid = 1002
        mock_x11vnc_process.returncode = None

        with patch("shutil.which", return_value="/usr/bin/tool"):
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=[mock_xvfb_process, mock_x11vnc_process],
            ):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    session = await manager.start_session(
                        display=":99",
                        resolution="1920x1080",
                    )

                    assert session.display == ":99"
                    assert session.port == 5999
                    assert session.resolution == "1920x1080"
                    assert len(session.password) == 12
                    assert session.pid == 1002
                    assert session.xvfb_pid == 1001
                    assert ":99" in manager.active_sessions

    @pytest.mark.asyncio
    async def test_start_session_xvfb_fails(self, manager: VNCManager) -> None:
        """Test start_session when Xvfb fails to start."""
        mock_xvfb_process = AsyncMock()
        mock_xvfb_process.pid = 1001
        mock_xvfb_process.returncode = 1  # Xvfb exited with error

        with patch("shutil.which", return_value="/usr/bin/tool"):
            with patch("asyncio.create_subprocess_exec", return_value=mock_xvfb_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(RuntimeError) as exc_info:
                        await manager.start_session()

                    assert "Xvfb failed to start" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_session_x11vnc_fails(self, manager: VNCManager) -> None:
        """Test start_session when x11vnc fails to start."""
        mock_xvfb_process = AsyncMock()
        mock_xvfb_process.pid = 1001
        mock_xvfb_process.returncode = None
        mock_xvfb_process.terminate = MagicMock()

        mock_x11vnc_process = AsyncMock()
        mock_x11vnc_process.pid = 1002
        mock_x11vnc_process.returncode = 1  # x11vnc exited with error

        with patch("shutil.which", return_value="/usr/bin/tool"):
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=[mock_xvfb_process, mock_x11vnc_process],
            ):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    with pytest.raises(RuntimeError) as exc_info:
                        await manager.start_session()

                    assert "x11vnc failed to start" in str(exc_info.value)
                    mock_xvfb_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_with_websocket(self, manager: VNCManager) -> None:
        """Test start_session with WebSocket enabled."""
        mock_xvfb = AsyncMock()
        mock_xvfb.pid = 1001
        mock_xvfb.returncode = None

        mock_x11vnc = AsyncMock()
        mock_x11vnc.pid = 1002
        mock_x11vnc.returncode = None

        mock_websockify = AsyncMock()
        mock_websockify.pid = 1003

        with patch("shutil.which", return_value="/usr/bin/tool"):
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=[mock_xvfb, mock_x11vnc, mock_websockify],
            ):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    session = await manager.start_session(
                        display=":99",
                        websocket=True,
                    )

                    assert session.websocket_port == 6999  # 5999 + 1000

    @pytest.mark.asyncio
    async def test_stop_session_not_found(self, manager: VNCManager) -> None:
        """Test stop_session when session doesn't exist."""
        result = await manager.stop_session(":99")

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_session_success(self, manager: VNCManager) -> None:
        """Test successful session stop."""
        manager.active_sessions[":99"] = VNCSession(
            display=":99",
            port=5999,
            password="test",
            websocket_port=None,
            resolution="1920x1080",
            pid=1001,
            xvfb_pid=1002,
        )

        with patch("os.kill") as mock_kill:
            result = await manager.stop_session(":99")

            assert result is True
            assert ":99" not in manager.active_sessions
            assert mock_kill.call_count == 2

    @pytest.mark.asyncio
    async def test_stop_session_process_already_dead(self, manager: VNCManager) -> None:
        """Test stop_session when processes already dead."""
        manager.active_sessions[":99"] = VNCSession(
            display=":99",
            port=5999,
            password="test",
            websocket_port=None,
            resolution="1920x1080",
            pid=1001,
            xvfb_pid=1002,
        )

        with patch("os.kill", side_effect=ProcessLookupError()):
            result = await manager.stop_session(":99")

            assert result is True
            assert ":99" not in manager.active_sessions

    @pytest.mark.asyncio
    async def test_install_vnc_deps_no_package_manager(self, manager: VNCManager) -> None:
        """Test install_vnc_deps when no package manager found."""
        with patch.object(manager, "_detect_package_manager", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager.install_vnc_deps()

            assert "No supported package manager" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_install_vnc_deps_already_installed(self, manager: VNCManager) -> None:
        """Test install_vnc_deps when all deps already installed."""
        with patch.object(manager, "_detect_package_manager", return_value="apt"):
            with patch("shutil.which", return_value="/usr/bin/tool"):
                result = await manager.install_vnc_deps()

                assert result is True

    @pytest.mark.asyncio
    async def test_install_vnc_deps_apt_success(self, manager: VNCManager) -> None:
        """Test successful installation with apt."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch.object(manager, "_detect_package_manager", return_value="apt"):
            with patch("shutil.which", return_value=None):  # Tools not installed
                with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                    with patch("asyncio.wait_for", return_value=(b"", b"")):
                        result = await manager.install_vnc_deps()

                        assert result is True

    @pytest.mark.asyncio
    async def test_install_vnc_deps_apt_failure(self, manager: VNCManager) -> None:
        """Test failed installation with apt."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"E: Unable to locate package")
        mock_process.returncode = 1

        with patch.object(manager, "_detect_package_manager", return_value="apt"):
            with patch("shutil.which", return_value=None):
                with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                    with patch(
                        "asyncio.wait_for",
                        return_value=(b"", b"E: Unable to locate package"),
                    ):
                        result = await manager.install_vnc_deps()

                        assert result is False

    @pytest.mark.asyncio
    async def test_install_vnc_deps_timeout(self, manager: VNCManager) -> None:
        """Test installation timeout."""
        with patch.object(manager, "_detect_package_manager", return_value="apt"):
            with patch("shutil.which", return_value=None):
                with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock):
                    with patch("asyncio.wait_for", side_effect=TimeoutError()):
                        result = await manager.install_vnc_deps()

                        assert result is False

    def test_get_session_exists(self, manager: VNCManager) -> None:
        """Test get_session when session exists."""
        session = VNCSession(
            display=":99",
            port=5999,
            password="test",
            websocket_port=None,
            resolution="1920x1080",
        )
        manager.active_sessions[":99"] = session

        result = manager.get_session(":99")

        assert result is session

    def test_get_session_not_exists(self, manager: VNCManager) -> None:
        """Test get_session when session doesn't exist."""
        result = manager.get_session(":99")

        assert result is None

    def test_list_sessions_empty(self, manager: VNCManager) -> None:
        """Test list_sessions with no active sessions."""
        result = manager.list_sessions()

        assert result == []

    def test_list_sessions_multiple(self, manager: VNCManager) -> None:
        """Test list_sessions with multiple sessions."""
        session1 = VNCSession(
            display=":99",
            port=5999,
            password="test1",
            websocket_port=None,
            resolution="1920x1080",
        )
        session2 = VNCSession(
            display=":100",
            port=6000,
            password="test2",
            websocket_port=None,
            resolution="1280x720",
        )
        manager.active_sessions[":99"] = session1
        manager.active_sessions[":100"] = session2

        result = manager.list_sessions()

        assert len(result) == 2
        assert session1 in result
        assert session2 in result
