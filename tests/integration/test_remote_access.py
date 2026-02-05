"""Integration tests for remote access module.

Tests complete workflows and integration between components:
- Environment detection workflow
- WSL2 ADB connection flow
- Appium server lifecycle
- Android emulator operations
- VNC session lifecycle
- Interview flow for Android requirements
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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
    create_adb_client_for_wsl2,
    create_android_test_environment,
    detect_environment,
    get_wsl2_host_ip,
    interview_android_requirements,
    setup_complete_android_stack,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_adb_available() -> Mock:
    """Mock ADB being available in PATH."""
    with patch("shutil.which") as mock_which:
        def which_impl(cmd: str) -> str | None:
            if cmd == "adb":
                return "/usr/bin/adb"
            return None

        mock_which.side_effect = which_impl
        yield mock_which


@pytest.fixture
def mock_appium_available() -> Mock:
    """Mock Appium being available in PATH."""
    with patch("shutil.which") as mock_which:
        def which_impl(cmd: str) -> str | None:
            if cmd in ("appium", "node", "npm"):
                return f"/usr/bin/{cmd}"
            return None

        mock_which.side_effect = which_impl
        yield mock_which


# =============================================================================
# Environment Detection Workflow Tests
# =============================================================================


class TestEnvironmentDetectionWorkflow:
    """Test complete environment detection workflows."""

    def test_wsl2_environment_detection_workflow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test complete WSL2 detection including host IP discovery."""
        # Setup WSL2 environment
        monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

        # Mock resolv.conf for host IP
        def mock_path_exists(path: Path) -> bool:
            return str(path) == "/etc/resolv.conf"

        def mock_path_read_text(path: Path) -> str:
            if str(path) == "/etc/resolv.conf":
                return "nameserver 172.20.144.1\n"
            return ""

        with patch.object(Path, "exists", mock_path_exists):
            with patch.object(Path, "read_text", mock_path_read_text):
                with patch("shutil.which") as mock_which:
                    mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}" if cmd == "adb" else None

                    # Detect environment
                    env = detect_environment()

                    # Verify platform detection
                    assert env.platform == "WSL2"
                    assert env.android_testing_mode == "remote"
                    assert env.adb_access == "mirrored"

                    # Verify capabilities detected
                    assert env.capabilities["adb"] is True
                    assert env.capabilities["wsl2_host_ip"] == "172.20.144.1"
                    assert env.capabilities["windows_adb_reachable"] is True

    def test_linux_environment_detection_workflow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test complete native Linux detection."""
        # Setup Linux environment - ensure WSL2 markers are not present
        monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)

        # Mock /proc/version to not contain "microsoft"
        def mock_path_exists(path: Path) -> bool:
            return str(path) == "/proc/version"

        def mock_path_read_text(path: Path) -> str:
            if str(path) == "/proc/version":
                return "Linux version 5.15.0-generic"
            return ""

        with patch("sys.platform", "linux"):
            with patch.object(Path, "exists", mock_path_exists):
                with patch.object(Path, "read_text", mock_path_read_text):
                    with patch("shutil.which") as mock_which:
                        mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}" if cmd == "adb" else None

                        # Detect environment
                        env = detect_environment()

                        # Verify platform detection
                        assert env.platform == "LINUX"
                        assert env.android_testing_mode == "local"
                        assert env.adb_access == "direct"

                        # Verify capabilities
                        assert env.capabilities["adb"] is True
                        assert "wsl2_host_ip" not in env.capabilities

    def test_wsl2_without_host_ip_workflow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test WSL2 detection when host IP cannot be determined."""
        # Setup WSL2 environment
        monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

        # Mock resolv.conf not existing
        with patch.object(Path, "exists", return_value=False):
            with patch("subprocess.run") as mock_run:
                # Mock ip route command failing
                mock_run.return_value = Mock(returncode=1, stdout="")

                with patch("shutil.which", return_value="/usr/bin/adb"):
                    env = detect_environment()

                    assert env.platform == "WSL2"
                    assert env.capabilities["wsl2_host_ip"] is None
                    assert env.capabilities["windows_adb_reachable"] is False


# =============================================================================
# ADB Client Connection Flow Tests
# =============================================================================


class TestADBConnectionFlow:
    """Test complete ADB client connection workflows."""

    @pytest.mark.asyncio
    async def test_successful_connection_flow(
        self,
        mock_adb_available: Mock,
    ) -> None:
        """Test complete successful ADB connection workflow."""
        config = WindowsHostConfig(host_ip="172.20.144.1", adb_port=5037)
        client = WindowsADBClient(config)

        # Mock subprocess for connect and devices commands
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock connect command
            connect_process = AsyncMock()
            connect_process.communicate = AsyncMock(
                return_value=(b"connected to 172.20.144.1:5037\n", b"")
            )
            connect_process.returncode = 0

            # Mock devices command
            devices_process = AsyncMock()
            devices_output = b"List of devices attached\nemulator-5554\tdevice\n"
            devices_process.communicate = AsyncMock(
                return_value=(devices_output, b"")
            )
            devices_process.returncode = 0

            # Return appropriate process based on command
            async def exec_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
                if "connect" in args:
                    return connect_process
                else:
                    return devices_process

            mock_exec.side_effect = exec_side_effect

            # Execute connection flow
            result = await client.connect()

            # Verify connection successful
            assert result.connected is True
            assert "emulator-5554" in result.devices
            assert result.error_message is None
            assert config.verified is True
            assert client._connected is True

    @pytest.mark.asyncio
    async def test_failed_connection_flow(
        self,
        mock_adb_available: Mock,
    ) -> None:
        """Test ADB connection failure workflow."""
        config = WindowsHostConfig(host_ip="192.168.1.100", adb_port=5037)
        client = WindowsADBClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock connect command failing
            connect_process = AsyncMock()
            connect_process.communicate = AsyncMock(
                return_value=(b"failed to connect\n", b"")
            )
            connect_process.returncode = 0
            mock_exec.return_value = connect_process

            result = await client.connect()

            # Verify connection failed
            assert result.connected is False
            assert len(result.devices) == 0
            assert result.error_message is not None
            assert config.verified is False

    @pytest.mark.asyncio
    async def test_list_devices_flow(
        self,
        mock_adb_available: Mock,
    ) -> None:
        """Test listing devices through ADB client."""
        config = WindowsHostConfig(host_ip="172.20.144.1")
        client = WindowsADBClient(config)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock devices command with multiple devices
            devices_output = (
                b"List of devices attached\n"
                b"emulator-5554\tdevice\n"
                b"emulator-5556\temulator\n"
                b"192.168.1.50:5555\tdevice\n"
            )

            process = AsyncMock()
            process.communicate = AsyncMock(return_value=(devices_output, b""))
            process.returncode = 0
            mock_exec.return_value = process

            devices = await client.list_devices()

            # Verify all devices detected
            assert len(devices) == 3
            assert "emulator-5554" in devices
            assert "emulator-5556" in devices
            assert "192.168.1.50:5555" in devices

    @pytest.mark.asyncio
    async def test_disconnect_flow(
        self,
        mock_adb_available: Mock,
    ) -> None:
        """Test disconnection workflow."""
        config = WindowsHostConfig(host_ip="172.20.144.1")
        client = WindowsADBClient(config)
        client._connected = True
        config.verified = True

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            process = AsyncMock()
            process.communicate = AsyncMock(
                return_value=(b"disconnected from 172.20.144.1:5037\n", b"")
            )
            process.returncode = 0
            mock_exec.return_value = process

            success = await client.disconnect()

            assert success is True
            assert client._connected is False
            assert config.verified is False


# =============================================================================
# Appium Server Lifecycle Tests
# =============================================================================


class TestAppiumServerLifecycle:
    """Test complete Appium server lifecycle workflows."""

    @pytest.mark.asyncio
    async def test_start_server_workflow(
        self,
        mock_appium_available: Mock,
    ) -> None:
        """Test complete server start workflow including health check."""
        manager = AppiumManager()
        config = AppiumConfig(port=4723, relaxed_security=True)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock Appium process
            appium_process = AsyncMock()
            appium_process.pid = 12345
            appium_process.returncode = None

            # Mock curl health check
            curl_process = AsyncMock()
            curl_process.communicate = AsyncMock(return_value=(b"200", b""))

            async def exec_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
                if args[0] == "curl":
                    return curl_process
                return appium_process

            mock_exec.side_effect = exec_side_effect

            # Start server
            status = await manager.start_server(config)

            # Verify server started
            assert status.running is True
            assert status.port == 4723
            assert status.url == "http://localhost:4723"
            assert status.pid == 12345
            assert manager._config == config

    @pytest.mark.asyncio
    async def test_stop_server_workflow(
        self,
        mock_appium_available: Mock,
    ) -> None:
        """Test complete server stop workflow."""
        manager = AppiumManager()

        # Create mock process
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_process.wait = AsyncMock(return_value=0)

        manager._process = mock_process
        manager._config = AppiumConfig(port=4723)

        # Stop server
        success = await manager.stop_server()

        # Verify cleanup
        assert success is True
        assert manager._process is None
        assert manager._config is None
        mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_workflow(
        self,
        mock_appium_available: Mock,
    ) -> None:
        """Test server health check workflow."""
        manager = AppiumManager()
        manager._config = AppiumConfig(port=4723)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock successful health check
            process = AsyncMock()
            process.communicate = AsyncMock(return_value=(b"200", b""))
            mock_exec.return_value = process

            healthy = await manager.health_check()

            assert healthy is True

            # Verify curl command
            call_args = mock_exec.call_args[0]
            assert call_args[0] == "curl"
            assert "http://localhost:4723/status" in call_args

    @pytest.mark.asyncio
    async def test_server_restart_workflow(
        self,
        mock_appium_available: Mock,
    ) -> None:
        """Test stopping existing server before starting new one."""
        manager = AppiumManager()

        # Setup existing process
        old_process = AsyncMock()
        old_process.pid = 11111
        old_process.returncode = None
        old_process.wait = AsyncMock(return_value=0)
        manager._process = old_process
        manager._config = AppiumConfig(port=4720)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # New server process
            new_process = AsyncMock()
            new_process.pid = 22222
            new_process.returncode = None

            # Health check
            curl_process = AsyncMock()
            curl_process.communicate = AsyncMock(return_value=(b"200", b""))

            async def exec_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
                if args[0] == "curl":
                    return curl_process
                return new_process

            mock_exec.side_effect = exec_side_effect

            # Start new server
            new_config = AppiumConfig(port=4723)
            status = await manager.start_server(new_config)

            # Verify old server was stopped
            old_process.terminate.assert_called_once()

            # Verify new server started
            assert status.pid == 22222
            assert manager._config == new_config


# =============================================================================
# Android Emulator Operations Flow Tests
# =============================================================================


class TestAndroidEmulatorOperationsFlow:
    """Test complete Android emulator operation workflows."""

    @pytest.mark.asyncio
    async def test_list_devices_with_remote_client(
        self,
        mock_adb_available: Mock,
    ) -> None:
        """Test listing devices using remote ADB client."""
        # Setup remote client
        config = WindowsHostConfig(host_ip="172.20.144.1")
        adb_client = WindowsADBClient(config)

        manager = AndroidEmulatorManager(adb_client=adb_client)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            devices_output = b"List of devices attached\nemulator-5554\tdevice\n"
            process = AsyncMock()
            process.communicate = AsyncMock(return_value=(devices_output, b""))
            process.returncode = 0
            mock_exec.return_value = process

            devices = await manager.list_devices()

            # Verify remote client was used
            assert len(devices) == 1
            assert "emulator-5554" in devices

            # Verify command included host flags
            call_args = mock_exec.call_args[0]
            assert "-H" in call_args
            assert "172.20.144.1" in call_args

    @pytest.mark.asyncio
    async def test_screenshot_capture_flow(
        self,
        mock_adb_available: Mock,
        tmp_path: Path,
    ) -> None:
        """Test complete screenshot capture workflow."""
        manager = AndroidEmulatorManager()

        # Create fake screenshot data
        fake_screenshot = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        screenshot_file = tmp_path / "screenshot.png"
        screenshot_file.write_bytes(fake_screenshot)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock screencap command
            screencap_process = AsyncMock()
            screencap_process.communicate = AsyncMock(return_value=(b"", b""))
            screencap_process.returncode = 0

            # Mock pull command
            pull_process = AsyncMock()
            pull_process.communicate = AsyncMock(return_value=(b"", b""))
            pull_process.returncode = 0

            # Mock rm command
            rm_process = AsyncMock()
            rm_process.communicate = AsyncMock(return_value=(b"", b""))
            rm_process.returncode = 0

            call_count = 0

            async def exec_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
                nonlocal call_count
                call_count += 1

                if call_count == 1:  # screencap
                    return screencap_process
                elif call_count == 2:  # pull
                    # Write fake screenshot to temp file
                    return pull_process
                else:  # rm
                    return rm_process

            mock_exec.side_effect = exec_side_effect

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_file = MagicMock()
                mock_file.name = str(screenshot_file)
                mock_temp.return_value.__enter__.return_value = mock_file

                # Capture screenshot
                data = await manager.take_screenshot()

                # Verify workflow
                assert data == fake_screenshot
                assert mock_exec.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_for_boot_workflow(
        self,
        mock_adb_available: Mock,
    ) -> None:
        """Test waiting for emulator boot completion."""
        manager = AndroidEmulatorManager()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            call_count = 0

            async def exec_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
                nonlocal call_count
                call_count += 1

                process = AsyncMock()

                if "devices" in args:
                    # First 2 calls: no devices, then device appears
                    if call_count <= 2:
                        output = b"List of devices attached\n"
                    else:
                        output = b"List of devices attached\nemulator-5554\tdevice\n"
                    process.communicate = AsyncMock(return_value=(output, b""))
                else:  # getprop
                    # First call returns 0, second returns 1 (booted)
                    if call_count <= 4:
                        output = b"0"
                    else:
                        output = b"1"
                    process.communicate = AsyncMock(return_value=(output, b""))

                process.returncode = 0
                return process

            mock_exec.side_effect = exec_side_effect

            # Wait for boot
            booted = await manager.wait_for_boot(timeout=30)

            assert booted is True
            assert call_count >= 3  # At least devices + getprop calls


# =============================================================================
# VNC Session Lifecycle Tests
# =============================================================================


class TestVNCSessionLifecycle:
    """Test complete VNC session lifecycle workflows."""

    @pytest.mark.asyncio
    async def test_start_session_workflow(self) -> None:
        """Test complete VNC session start workflow."""
        manager = VNCManager()

        with patch("shutil.which") as mock_which:
            # Mock Xvfb and x11vnc available
            mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}" if cmd in ("Xvfb", "x11vnc") else None

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                # Mock Xvfb process
                xvfb_process = AsyncMock()
                xvfb_process.pid = 11111
                xvfb_process.returncode = None

                # Mock x11vnc process
                x11vnc_process = AsyncMock()
                x11vnc_process.pid = 22222
                x11vnc_process.returncode = None

                call_count = 0

                async def exec_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
                    nonlocal call_count
                    call_count += 1
                    if args[0] == "Xvfb":
                        return xvfb_process
                    else:
                        return x11vnc_process

                mock_exec.side_effect = exec_side_effect

                # Start session
                session = await manager.start_session(
                    display=":99",
                    resolution="1920x1080",
                    websocket=False,
                )

                # Verify session started
                assert session.display == ":99"
                assert session.port == 5999
                assert session.resolution == "1920x1080"
                assert session.pid == 22222
                assert session.xvfb_pid == 11111
                assert len(session.password) > 0
                assert session.websocket_port is None

                # Verify processes started
                assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_stop_session_workflow(self) -> None:
        """Test complete VNC session stop workflow."""
        manager = VNCManager()

        # Create active session
        session = VNCSession(
            display=":99",
            port=5999,
            password="test123",
            websocket_port=None,
            resolution="1920x1080",
            pid=22222,
            xvfb_pid=11111,
        )
        manager.active_sessions[":99"] = session

        with patch("os.kill") as mock_kill:
            # Stop session
            success = await manager.stop_session(":99")

            # Verify cleanup
            assert success is True
            assert ":99" not in manager.active_sessions

            # Verify both processes killed
            assert mock_kill.call_count == 2
            kill_pids = [call[0][0] for call in mock_kill.call_args_list]
            assert 22222 in kill_pids  # x11vnc
            assert 11111 in kill_pids  # Xvfb

    @pytest.mark.asyncio
    async def test_session_with_websocket_workflow(self) -> None:
        """Test VNC session with WebSocket proxy."""
        manager = VNCManager()

        with patch("shutil.which") as mock_which:
            # All tools available
            mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                # Mock processes
                process = AsyncMock()
                process.pid = 12345
                process.returncode = None
                mock_exec.return_value = process

                # Start session with websocket
                session = await manager.start_session(
                    display=":99",
                    resolution="1920x1080",
                    websocket=True,
                )

                # Verify websocket port assigned
                assert session.websocket_port == 6999

                # Verify websockify was started (3 processes: Xvfb, x11vnc, websockify)
                assert mock_exec.call_count == 3

    @pytest.mark.asyncio
    async def test_multiple_sessions_workflow(self) -> None:
        """Test managing multiple VNC sessions."""
        manager = VNCManager()

        with patch("shutil.which", return_value="/usr/bin/mock"):
            with patch("asyncio.create_subprocess_exec") as mock_exec:
                process = AsyncMock()
                process.pid = 12345
                process.returncode = None
                mock_exec.return_value = process

                # Start multiple sessions
                session1 = await manager.start_session(display=":99")
                session2 = await manager.start_session(display=":98")

                # Verify both sessions tracked
                sessions = manager.list_sessions()
                assert len(sessions) == 2

                # Verify sessions are distinct
                assert session1.display == ":99"
                assert session1.port == 5999
                assert session2.display == ":98"
                assert session2.port == 5998

                # Stop one session
                with patch("os.kill"):
                    await manager.stop_session(":99")

                # Verify only one remains
                sessions = manager.list_sessions()
                assert len(sessions) == 1
                assert sessions[0].display == ":98"


# =============================================================================
# Interview Flow Tests
# =============================================================================


class TestInterviewFlow:
    """Test complete Android requirements interview workflows."""

    @pytest.mark.asyncio
    async def test_no_android_testing_flow(self) -> None:
        """Test interview when Android testing is not needed."""

        def ask_question(question: str, options: list[str] | None) -> str:
            if "Android app testing" in question:
                return "No"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
                capabilities={"adb": True},
            )

            requirements = await interview_android_requirements(ask_question)

            assert requirements.needs_android_testing is False
            assert requirements.windows_config is None
            assert requirements.connection_verified is False

    @pytest.mark.asyncio
    async def test_linux_android_testing_flow(self) -> None:
        """Test interview for Android testing on native Linux."""

        def ask_question(question: str, options: list[str] | None) -> str:
            if "Android app testing" in question:
                return "Yes"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
                capabilities={"adb": True},
            )

            requirements = await interview_android_requirements(ask_question)

            assert requirements.needs_android_testing is True
            assert requirements.windows_config is None
            assert requirements.connection_verified is True

    @pytest.mark.asyncio
    async def test_wsl2_android_testing_auto_detect_flow(self) -> None:
        """Test WSL2 Android testing with auto-detected host IP."""

        responses = ["Yes", "Yes", ""]  # Android testing yes, use auto-detected IP yes, port default
        response_index = 0

        def ask_question(question: str, options: list[str] | None) -> str:
            nonlocal response_index
            response = responses[response_index]
            response_index = min(response_index + 1, len(responses) - 1)
            return response

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={"wsl2_host_ip": "172.20.144.1"},
            )

            with patch("beyond_ralph.integrations.remote_access.get_wsl2_host_ip") as mock_get_ip:
                mock_get_ip.return_value = "172.20.144.1"

                with patch("beyond_ralph.integrations.remote_access.WindowsADBClient") as mock_client:
                    # Mock successful connection
                    mock_instance = AsyncMock()
                    mock_instance.connect = AsyncMock(
                        return_value=ADBConnectionResult(
                            connected=True,
                            devices=["emulator-5554"],
                        )
                    )
                    mock_client.return_value = mock_instance

                    requirements = await interview_android_requirements(ask_question)

                    assert requirements.needs_android_testing is True
                    assert requirements.windows_config is not None
                    assert requirements.windows_config.host_ip == "172.20.144.1"
                    assert requirements.connection_verified is True

    @pytest.mark.asyncio
    async def test_wsl2_android_testing_manual_ip_flow(self) -> None:
        """Test WSL2 Android testing with manually entered host IP."""

        responses = ["Yes", "No, enter manually", "192.168.1.100", ""]  # Port uses default
        response_index = 0

        def ask_question(question: str, options: list[str] | None) -> str:
            nonlocal response_index
            response = responses[response_index]
            response_index += 1
            return response

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={},
            )

            with patch("beyond_ralph.integrations.remote_access.get_wsl2_host_ip") as mock_get_ip:
                mock_get_ip.return_value = "172.20.144.1"

                with patch("beyond_ralph.integrations.remote_access.WindowsADBClient") as mock_client:
                    mock_instance = AsyncMock()
                    mock_instance.connect = AsyncMock(
                        return_value=ADBConnectionResult(
                            connected=True,
                            devices=["emulator-5554"],
                        )
                    )
                    mock_client.return_value = mock_instance

                    requirements = await interview_android_requirements(ask_question)

                    assert requirements.windows_config is not None
                    assert requirements.windows_config.host_ip == "192.168.1.100"
                    assert requirements.windows_config.adb_port == 5037

    @pytest.mark.asyncio
    async def test_wsl2_connection_failure_flow(self) -> None:
        """Test WSL2 interview when ADB connection fails."""

        def ask_question(question: str, options: list[str] | None) -> str:
            if "Android app testing" in question:
                return "Yes"
            elif "Use this address" in question:
                return "Yes"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="WSL2",
                android_testing_mode="remote",
                adb_access="mirrored",
                capabilities={"wsl2_host_ip": "172.20.144.1"},
            )

            with patch("beyond_ralph.integrations.remote_access.get_wsl2_host_ip") as mock_get_ip:
                mock_get_ip.return_value = "172.20.144.1"

                with patch("beyond_ralph.integrations.remote_access.WindowsADBClient") as mock_client:
                    # Mock failed connection
                    mock_instance = AsyncMock()
                    mock_instance.connect = AsyncMock(
                        return_value=ADBConnectionResult(
                            connected=False,
                            error_message="Connection refused",
                        )
                    )
                    mock_client.return_value = mock_instance

                    # Should raise configuration error
                    with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                        await interview_android_requirements(ask_question)

                    assert "Failed to connect" in str(exc_info.value)
                    assert "Ensure ADB server is running" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_linux_missing_adb_flow(self) -> None:
        """Test interview when Android testing needed but ADB missing."""

        def ask_question(question: str, options: list[str] | None) -> str:
            if "Android app testing" in question:
                return "Yes"
            return ""

        with patch("beyond_ralph.integrations.remote_access.detect_environment") as mock_detect:
            mock_detect.return_value = EnvironmentInfo(
                platform="LINUX",
                android_testing_mode="local",
                adb_access="direct",
                capabilities={"adb": False},  # ADB not available
            )

            with pytest.raises(AndroidTestingConfigurationError) as exc_info:
                await interview_android_requirements(ask_question)

            assert "ADB is not installed" in str(exc_info.value)


# =============================================================================
# Convenience Functions Integration Tests
# =============================================================================


class TestConvenienceFunctions:
    """Test convenience functions that integrate multiple components."""

    def test_create_android_test_environment_wsl2(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test creating Android test environment for WSL2."""
        monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

        with patch("beyond_ralph.integrations.remote_access.get_wsl2_host_ip") as mock_get_ip:
            mock_get_ip.return_value = "172.20.144.1"

            with patch("shutil.which", return_value="/usr/bin/adb"):
                env, manager = create_android_test_environment()

                assert env.platform == "WSL2"
                assert manager.adb_client is not None
                assert manager._use_remote is True

    def test_create_android_test_environment_linux(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test creating Android test environment for native Linux."""
        monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)

        # Mock to ensure we're not detected as WSL2
        def mock_path_exists(path: Path) -> bool:
            return str(path) == "/proc/version"

        def mock_path_read_text(path: Path) -> str:
            if str(path) == "/proc/version":
                return "Linux version 5.15.0-generic"
            return ""

        with patch("sys.platform", "linux"):
            with patch.object(Path, "exists", mock_path_exists):
                with patch.object(Path, "read_text", mock_path_read_text):
                    with patch("shutil.which", return_value="/usr/bin/adb"):
                        env, manager = create_android_test_environment()

                        assert env.platform == "LINUX"
                        assert manager.adb_client is None
                        assert manager._use_remote is False

    @pytest.mark.asyncio
    async def test_setup_complete_android_stack_wsl2(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test setting up complete Android stack for WSL2."""
        monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

        with patch("beyond_ralph.integrations.remote_access.get_wsl2_host_ip") as mock_get_ip:
            mock_get_ip.return_value = "172.20.144.1"

            with patch("shutil.which", return_value="/usr/bin/mock"):
                appium_manager, emulator_manager = await setup_complete_android_stack(
                    appium_port=4723
                )

                # Verify Appium manager has suggested config
                assert appium_manager._suggested_config is not None
                assert appium_manager._suggested_config.port == 4723
                assert appium_manager._suggested_config.adb_host == "172.20.144.1"

                # Verify emulator manager uses remote client
                assert emulator_manager.adb_client is not None
                assert emulator_manager._use_remote is True

    @pytest.mark.asyncio
    async def test_setup_complete_android_stack_linux(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test setting up complete Android stack for Linux."""
        monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)

        # Mock to ensure we're not detected as WSL2
        def mock_path_exists(path: Path) -> bool:
            return str(path) == "/proc/version"

        def mock_path_read_text(path: Path) -> str:
            if str(path) == "/proc/version":
                return "Linux version 5.15.0-generic"
            return ""

        with patch("sys.platform", "linux"):
            with patch.object(Path, "exists", mock_path_exists):
                with patch.object(Path, "read_text", mock_path_read_text):
                    with patch("shutil.which", return_value="/usr/bin/mock"):
                        appium_manager, emulator_manager = await setup_complete_android_stack(
                            appium_port=4723
                        )

                        # Verify suggested config has no ADB host
                        assert appium_manager._suggested_config is not None
                        assert appium_manager._suggested_config.adb_host is None

                        # Verify emulator manager uses local ADB
                        assert emulator_manager.adb_client is None
                        assert emulator_manager._use_remote is False
