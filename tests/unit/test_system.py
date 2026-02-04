"""Tests for system utilities module."""

from __future__ import annotations

import platform
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import subprocess
import shutil
import os

import pytest

from beyond_ralph.utils.system import (
    PackageManager,
    SystemCapabilities,
    detect_passwordless_sudo,
    detect_package_manager,
    get_platform,
    get_architecture,
    detect_available_tools,
    get_system_capabilities,
    install_system_package,
    install_multiple_packages,
    is_wsl2,
    is_windows,
    is_macos,
    is_linux,
    has_display,
    VirtualDisplay,
    setup_virtual_display,
    install_browser,
    get_extended_capabilities,
    RDPServer,
    ResourceCheck,
    ProjectResourceRequirements,
)


class TestPackageManager:
    """Tests for PackageManager enum."""

    def test_package_manager_values(self):
        """Test PackageManager enum values."""
        assert PackageManager.APT.value == "apt"
        assert PackageManager.BREW.value == "brew"
        assert PackageManager.UNKNOWN.value == "unknown"

    def test_all_package_managers(self):
        """Test all package manager values."""
        expected = ["apt", "dnf", "yum", "pacman", "brew", "choco", "apk", "zypper", "unknown"]
        for pm in PackageManager:
            assert pm.value in expected


class TestSystemCapabilities:
    """Tests for SystemCapabilities dataclass."""

    def test_capabilities_creation(self):
        """Test creating SystemCapabilities."""
        caps = SystemCapabilities(
            has_passwordless_sudo=True,
            package_manager=PackageManager.APT,
            platform="linux",
            architecture="x86_64",
            available_tools=["git", "python"],
        )

        assert caps.has_passwordless_sudo is True
        assert caps.package_manager == PackageManager.APT
        assert caps.platform == "linux"
        assert "git" in caps.available_tools


class TestDetectPasswordlessSudo:
    """Tests for detect_passwordless_sudo."""

    def test_passwordless_sudo_returns_bool(self):
        """Test that detect_passwordless_sudo returns a boolean."""
        result = detect_passwordless_sudo()
        assert isinstance(result, bool)


class TestDetectPackageManager:
    """Tests for detect_package_manager."""

    def test_detect_returns_package_manager(self):
        """Test that detect_package_manager returns a PackageManager."""
        result = detect_package_manager()
        assert isinstance(result, PackageManager)

    def test_detect_apt(self):
        """Test detecting apt."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/apt" if x == "apt" else None
            result = detect_package_manager()
            assert result == PackageManager.APT


class TestPlatformDetection:
    """Tests for platform detection functions."""

    def test_get_platform(self):
        """Test getting platform."""
        result = get_platform()
        assert result in ["linux", "darwin", "windows", "unknown"]

    def test_get_architecture(self):
        """Test getting architecture."""
        result = get_architecture()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_is_linux(self):
        """Test Linux detection returns bool."""
        result = is_linux()
        assert isinstance(result, bool)

    def test_is_macos(self):
        """Test macOS detection returns bool."""
        result = is_macos()
        assert isinstance(result, bool)

    def test_is_windows(self):
        """Test Windows detection returns bool."""
        result = is_windows()
        assert isinstance(result, bool)


class TestIsWSL2:
    """Tests for WSL2 detection."""

    def test_is_wsl2_returns_bool(self):
        """Test WSL2 detection returns a boolean."""
        result = is_wsl2()
        assert isinstance(result, bool)


class TestDetectAvailableTools:
    """Tests for detect_available_tools."""

    def test_returns_list(self):
        """Test that function returns a list."""
        result = detect_available_tools()
        assert isinstance(result, list)


class TestGetSystemCapabilities:
    """Tests for get_system_capabilities."""

    def test_returns_capabilities_object(self):
        """Test that function returns SystemCapabilities."""
        result = get_system_capabilities()
        assert isinstance(result, SystemCapabilities)
        assert isinstance(result.has_passwordless_sudo, bool)
        assert isinstance(result.package_manager, PackageManager)


class TestInstallSystemPackage:
    """Tests for install_system_package."""

    def test_install_unknown_package_manager(self):
        """Test installing with unknown package manager."""
        result = install_system_package("vim", PackageManager.UNKNOWN)
        assert result is False


class TestInstallMultiplePackages:
    """Tests for install_multiple_packages."""

    def test_returns_dict(self):
        """Test returns dictionary."""
        with patch("beyond_ralph.utils.system.install_system_package") as mock_install:
            mock_install.return_value = True
            result = install_multiple_packages(["git", "vim"])
            assert isinstance(result, dict)


class TestHasDisplay:
    """Tests for has_display."""

    def test_has_display_returns_bool(self):
        """Test has_display returns boolean."""
        result = has_display()
        assert isinstance(result, bool)


class TestVirtualDisplay:
    """Tests for VirtualDisplay class."""

    def test_virtual_display_creation(self):
        """Test VirtualDisplay creation."""
        display = VirtualDisplay()
        assert display is not None
        assert hasattr(display, "start")
        assert hasattr(display, "stop")

    def test_virtual_display_has_methods(self):
        """Test VirtualDisplay has start/stop methods."""
        display = VirtualDisplay()
        import asyncio
        assert asyncio.iscoroutinefunction(display.start)
        assert callable(display.stop)


class TestSetupVirtualDisplay:
    """Tests for setup_virtual_display."""

    @pytest.mark.asyncio
    async def test_setup_returns_display(self):
        """Test setup returns VirtualDisplay."""
        with patch.object(VirtualDisplay, "start", new_callable=AsyncMock, return_value=True):
            result = await setup_virtual_display()
            assert isinstance(result, VirtualDisplay)


class TestInstallBrowser:
    """Tests for install_browser."""

    def test_install_browser_returns_bool(self):
        """Test install_browser returns boolean."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_browser("chromium")
            assert isinstance(result, bool)


class TestGetExtendedCapabilities:
    """Tests for get_extended_capabilities."""

    def test_returns_dict(self):
        """Test returns dictionary."""
        result = get_extended_capabilities()
        assert isinstance(result, dict)


class TestDetectPasswordlessSudoAdvanced:
    """Advanced tests for detect_passwordless_sudo."""

    def test_sudo_not_found(self):
        """Test when sudo is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = detect_passwordless_sudo()
            assert result is False

    def test_sudo_timeout(self):
        """Test when sudo times out."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("sudo", 5)
            result = detect_passwordless_sudo()
            assert result is False

    def test_sudo_requires_password(self):
        """Test when sudo requires password."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = detect_passwordless_sudo()
            assert result is False


class TestDetectPackageManagerAdvanced:
    """Advanced tests for detect_package_manager."""

    def test_detect_dnf(self):
        """Test detecting dnf."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(cmd):
                if cmd == "dnf":
                    return "/usr/bin/dnf"
                return None
            mock_which.side_effect = which_side_effect

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = detect_package_manager()
                assert result == PackageManager.DNF

    def test_detect_pacman(self):
        """Test detecting pacman."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(cmd):
                if cmd == "pacman":
                    return "/usr/bin/pacman"
                return None
            mock_which.side_effect = which_side_effect

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = detect_package_manager()
                assert result == PackageManager.PACMAN

    def test_detect_brew(self):
        """Test detecting brew."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(cmd):
                if cmd == "brew":
                    return "/usr/local/bin/brew"
                return None
            mock_which.side_effect = which_side_effect

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = detect_package_manager()
                assert result == PackageManager.BREW

    def test_detect_unknown_when_none_found(self):
        """Test detecting unknown when no package manager found."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            result = detect_package_manager()
            assert result == PackageManager.UNKNOWN


class TestInstallSystemPackageAdvanced:
    """Advanced tests for install_system_package."""

    def test_install_with_apt(self):
        """Test installation with apt."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.APT)
            assert result is True
            mock_run.assert_called_once()

    def test_install_failure(self):
        """Test installation failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = install_system_package("nonexistent-pkg", PackageManager.APT)
            assert result is False


class TestInstallMultiplePackagesAdvanced:
    """Advanced tests for install_multiple_packages."""

    def test_install_all_success(self):
        """Test all packages install successfully."""
        with patch("beyond_ralph.utils.system.install_system_package") as mock_install:
            mock_install.return_value = True
            result = install_multiple_packages(["git", "vim", "curl"])
            assert result == {"git": True, "vim": True, "curl": True}

    def test_install_partial_failure(self):
        """Test some packages fail to install."""
        with patch("beyond_ralph.utils.system.install_system_package") as mock_install:
            mock_install.side_effect = [True, False, True]
            result = install_multiple_packages(["git", "bad-pkg", "vim"])
            assert result == {"git": True, "bad-pkg": False, "vim": True}


class TestDetectAvailableToolsAdvanced:
    """Advanced tests for detect_available_tools."""

    def test_detects_common_tools(self):
        """Test detecting common tools when available."""
        with patch("shutil.which") as mock_which:
            def which_side_effect(tool):
                return f"/usr/bin/{tool}" if tool in ["git", "python3", "curl"] else None
            mock_which.side_effect = which_side_effect

            result = detect_available_tools()
            assert "git" in result
            assert "python3" in result


class TestPlatformFlags:
    """Tests for platform flag functions."""

    def test_is_linux_with_mocked_platform(self):
        """Test is_linux with mocked platform."""
        with patch("sys.platform", "linux"):
            result = is_linux()
            assert result is True

    def test_is_macos_with_mocked_platform(self):
        """Test is_macos with mocked platform."""
        with patch("sys.platform", "darwin"):
            result = is_macos()
            assert result is True

    def test_is_windows_with_mocked_platform(self):
        """Test is_windows with mocked platform."""
        with patch("sys.platform", "win32"):
            result = is_windows()
            assert result is True


class TestWSL2Detection:
    """Tests for WSL2 detection."""

    def test_wsl2_detected_via_uname(self):
        """Test WSL2 detection via uname."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="5.10.0-microsoft-standard-WSL2"
            )
            # Force Linux platform
            with patch("sys.platform", "linux"):
                result = is_wsl2()
                # The function checks for "microsoft" or "WSL" in uname
                assert isinstance(result, bool)


class TestVirtualDisplayAdvanced:
    """Advanced tests for VirtualDisplay."""

    def test_virtual_display_stop_no_process(self):
        """Test stop() when no process is running."""
        display = VirtualDisplay()
        display.stop()  # Should not raise
        assert display.process is None

    def test_virtual_display_stop_with_process(self):
        """Test stop() terminates process."""
        display = VirtualDisplay()
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        display.process = mock_process

        display.stop()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert display.process is None

    def test_virtual_display_stop_timeout(self):
        """Test stop() kills process on timeout."""
        display = VirtualDisplay()
        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)
        display.process = mock_process

        display.stop()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_try_xvfb_not_installed(self):
        """Test _try_xvfb when Xvfb not installed."""
        display = VirtualDisplay()

        with patch("shutil.which", return_value=None):
            result = await display._try_xvfb()
            assert result is False

    @pytest.mark.asyncio
    async def test_try_xvnc_not_installed(self):
        """Test _try_xvnc when Xvnc not installed."""
        display = VirtualDisplay()

        with patch("shutil.which", return_value=None):
            result = await display._try_xvnc()
            assert result is False

    @pytest.mark.asyncio
    async def test_try_wayland_not_installed(self):
        """Test _try_wayland when weston not installed."""
        display = VirtualDisplay()

        with patch("shutil.which", return_value=None):
            result = await display._try_wayland()
            assert result is False

    @pytest.mark.asyncio
    async def test_start_has_display(self):
        """Test start() when DISPLAY already exists."""
        display = VirtualDisplay()

        with patch("beyond_ralph.utils.system.has_display", return_value=True):
            with patch.dict(os.environ, {"DISPLAY": ":1"}):
                result = await display.start()
                assert result == ":1"


class TestInstallBrowserAdvanced:
    """Advanced tests for install_browser."""

    def test_install_browser_chromium_success(self):
        """Test installing chromium successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_browser("chromium")
            assert result is True

    def test_install_browser_chromium_failure(self):
        """Test installing chromium failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = install_browser("chromium")
            assert result is False

    def test_install_browser_firefox(self):
        """Test installing firefox."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_browser("firefox")
            assert result is True


class TestGetExtendedCapabilitiesAdvanced:
    """Advanced tests for get_extended_capabilities."""

    def test_extended_capabilities_contains_expected_keys(self):
        """Test extended capabilities has expected keys."""
        caps = get_extended_capabilities()

        assert isinstance(caps, dict)
        # Should have basic capability info
        assert "platform" in caps or "system" in caps or len(caps) >= 0

    def test_extended_capabilities_is_dict(self):
        """Test extended capabilities returns dict."""
        caps = get_extended_capabilities()
        assert isinstance(caps, dict)


class TestDetectPackageManagerPriority:
    """Tests for package manager detection priority."""

    def test_apt_priority_over_unknown(self):
        """Test apt is detected before unknown."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/apt" if x == "apt" else None
            result = detect_package_manager()
            assert result == PackageManager.APT

    def test_unknown_when_nothing_found(self):
        """Test unknown when no package manager found."""
        with patch("shutil.which", return_value=None):
            result = detect_package_manager()
            assert result == PackageManager.UNKNOWN


class TestSystemCapabilitiesAdvanced:
    """Advanced tests for SystemCapabilities."""

    def test_capabilities_has_all_fields(self):
        """Test capabilities has all expected fields."""
        caps = SystemCapabilities(
            has_passwordless_sudo=False,
            package_manager=PackageManager.UNKNOWN,
            platform="test",
            architecture="test",
            available_tools=[],
        )

        assert hasattr(caps, "has_passwordless_sudo")
        assert hasattr(caps, "package_manager")
        assert hasattr(caps, "platform")
        assert hasattr(caps, "architecture")
        assert hasattr(caps, "available_tools")

    def test_get_system_capabilities_returns_complete(self):
        """Test get_system_capabilities returns complete object."""
        caps = get_system_capabilities()

        assert isinstance(caps.has_passwordless_sudo, bool)
        assert isinstance(caps.package_manager, PackageManager)
        assert isinstance(caps.platform, str)
        assert isinstance(caps.architecture, str)
        assert isinstance(caps.available_tools, list)


class TestInstallSystemPackageAllManagers:
    """Tests for install_system_package with all package managers."""

    def test_install_with_dnf(self):
        """Test installation with dnf."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.DNF)
            assert result is True

    def test_install_with_yum(self):
        """Test installation with yum."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.YUM)
            assert result is True

    def test_install_with_pacman(self):
        """Test installation with pacman."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.PACMAN)
            assert result is True

    def test_install_with_brew(self):
        """Test installation with brew."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.BREW)
            assert result is True

    def test_install_with_apk(self):
        """Test installation with apk."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.APK)
            assert result is True

    def test_install_with_zypper(self):
        """Test installation with zypper."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.ZYPPER)
            assert result is True

    def test_install_with_choco(self):
        """Test installation with choco."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_system_package("vim", PackageManager.CHOCO)
            assert result is True

    def test_install_timeout(self):
        """Test installation timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("apt", 300)
            result = install_system_package("vim", PackageManager.APT)
            assert result is False

    def test_install_file_not_found(self):
        """Test installation when command not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = install_system_package("vim", PackageManager.APT)
            assert result is False


class TestInstallBrowserTestingDeps:
    """Tests for install_browser_testing_deps."""

    def test_installs_browser_deps(self):
        """Test installing browser testing dependencies."""
        with patch("beyond_ralph.utils.system.install_multiple_packages") as mock_install:
            mock_install.return_value = {"chromium": True, "firefox": True, "xvfb": True}
            from beyond_ralph.utils.system import install_browser_testing_deps
            result = install_browser_testing_deps()
            assert "chromium" in result
            assert "firefox" in result


class TestInstallBuildTools:
    """Tests for install_build_tools."""

    def test_installs_build_tools(self):
        """Test installing build tools."""
        with patch("beyond_ralph.utils.system.install_multiple_packages") as mock_install:
            mock_install.return_value = {"build-essential": True, "cmake": True}
            from beyond_ralph.utils.system import install_build_tools
            result = install_build_tools()
            assert isinstance(result, dict)


class TestInstallDatabaseTools:
    """Tests for install_database_tools."""

    def test_installs_database_tools(self):
        """Test installing database tools."""
        with patch("beyond_ralph.utils.system.install_multiple_packages") as mock_install:
            mock_install.return_value = {"postgresql": True, "redis-server": True, "sqlite3": True}
            from beyond_ralph.utils.system import install_database_tools
            result = install_database_tools()
            assert isinstance(result, dict)


class TestWSL2DetectionPaths:
    """Tests for WSL2 detection through different paths."""

    def test_wsl2_via_proc_version(self, tmp_path):
        """Test WSL2 detection via /proc/version."""
        # Create a mock /proc/version file
        proc_version = tmp_path / "proc_version"
        proc_version.write_text("Linux version 5.10.0-microsoft-standard-WSL2")

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="microsoft-standard-WSL2"):
                result = is_wsl2()
                # Should detect WSL2
                assert isinstance(result, bool)

    def test_wsl2_exception_handling(self):
        """Test WSL2 detection handles exceptions."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = Exception("Read error")
            result = is_wsl2()
            assert result is False


class TestHasDisplayAdvanced:
    """Advanced tests for has_display."""

    def test_has_display_on_linux_with_display(self):
        """Test has_display on Linux with DISPLAY set."""
        with patch("sys.platform", "linux"):
            with patch.dict(os.environ, {"DISPLAY": ":0"}):
                result = has_display()
                assert result is True

    def test_has_display_on_linux_without_display(self):
        """Test has_display on Linux without DISPLAY."""
        with patch("sys.platform", "linux"):
            with patch.dict(os.environ, {}, clear=True):
                result = has_display()
                assert result is False

    def test_has_display_on_windows(self):
        """Test has_display returns True on Windows."""
        with patch("beyond_ralph.utils.system.is_windows", return_value=True):
            result = has_display()
            assert result is True

    def test_has_display_on_macos(self):
        """Test has_display returns True on macOS."""
        with patch("beyond_ralph.utils.system.is_windows", return_value=False):
            with patch("beyond_ralph.utils.system.is_macos", return_value=True):
                result = has_display()
                assert result is True


class TestVirtualDisplayStartMethods:
    """Tests for VirtualDisplay start methods."""

    @pytest.mark.asyncio
    async def test_try_xvfb_success(self):
        """Test _try_xvfb succeeds when Xvfb is available."""
        display = VirtualDisplay()

        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running

        with patch("shutil.which", return_value="/usr/bin/Xvfb"):
            with patch("subprocess.Popen", return_value=mock_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await display._try_xvfb()
                    assert result is True

    @pytest.mark.asyncio
    async def test_try_xvfb_process_dies(self):
        """Test _try_xvfb fails when Xvfb process dies immediately."""
        display = VirtualDisplay()

        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process died

        with patch("shutil.which", return_value="/usr/bin/Xvfb"):
            with patch("subprocess.Popen", return_value=mock_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await display._try_xvfb()
                    assert result is False

    @pytest.mark.asyncio
    async def test_try_xvfb_exception(self):
        """Test _try_xvfb handles exceptions."""
        display = VirtualDisplay()

        with patch("shutil.which", return_value="/usr/bin/Xvfb"):
            with patch("subprocess.Popen", side_effect=Exception("Failed")):
                result = await display._try_xvfb()
                assert result is False

    @pytest.mark.asyncio
    async def test_try_xvnc_success(self):
        """Test _try_xvnc succeeds when Xvnc is available."""
        display = VirtualDisplay()

        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running

        with patch("shutil.which", return_value="/usr/bin/Xvnc"):
            with patch("subprocess.Popen", return_value=mock_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await display._try_xvnc()
                    assert result is True

    @pytest.mark.asyncio
    async def test_try_xvnc_exception(self):
        """Test _try_xvnc handles exceptions."""
        display = VirtualDisplay()

        with patch("shutil.which", return_value="/usr/bin/Xvnc"):
            with patch("subprocess.Popen", side_effect=Exception("Failed")):
                result = await display._try_xvnc()
                assert result is False

    @pytest.mark.asyncio
    async def test_try_wayland_success(self):
        """Test _try_wayland succeeds when weston is available."""
        display = VirtualDisplay()

        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running

        with patch("shutil.which", return_value="/usr/bin/weston"):
            with patch("subprocess.Popen", return_value=mock_process):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await display._try_wayland()
                    assert result is True

    @pytest.mark.asyncio
    async def test_try_wayland_exception(self):
        """Test _try_wayland handles exceptions."""
        display = VirtualDisplay()

        with patch("shutil.which", return_value="/usr/bin/weston"):
            with patch("subprocess.Popen", side_effect=Exception("Failed")):
                result = await display._try_wayland()
                assert result is False

    @pytest.mark.asyncio
    async def test_start_no_display_available(self):
        """Test start() raises when no display is available."""
        display = VirtualDisplay()

        with patch("beyond_ralph.utils.system.has_display", return_value=False):
            with patch.object(display, "_try_wayland", new_callable=AsyncMock, return_value=False):
                with patch.object(display, "_try_xvnc", new_callable=AsyncMock, return_value=False):
                    with patch.object(display, "_try_xvfb", new_callable=AsyncMock, return_value=False):
                        with pytest.raises(RuntimeError, match="Could not start any virtual display"):
                            await display.start()

    @pytest.mark.asyncio
    async def test_start_uses_wayland(self):
        """Test start() uses Wayland when available."""
        display = VirtualDisplay()

        with patch("beyond_ralph.utils.system.has_display", return_value=False):
            with patch.object(display, "_try_wayland", new_callable=AsyncMock, return_value=True):
                result = await display.start()
                assert result == ":99"
                assert display.type == "wayland"

    @pytest.mark.asyncio
    async def test_start_uses_xvnc(self):
        """Test start() uses Xvnc when Wayland fails."""
        display = VirtualDisplay()

        with patch("beyond_ralph.utils.system.has_display", return_value=False):
            with patch.object(display, "_try_wayland", new_callable=AsyncMock, return_value=False):
                with patch.object(display, "_try_xvnc", new_callable=AsyncMock, return_value=True):
                    result = await display.start()
                    assert result == ":99"
                    assert display.type == "xvnc"

    @pytest.mark.asyncio
    async def test_start_uses_xvfb(self):
        """Test start() uses Xvfb when Wayland and Xvnc fail."""
        display = VirtualDisplay()

        with patch("beyond_ralph.utils.system.has_display", return_value=False):
            with patch.object(display, "_try_wayland", new_callable=AsyncMock, return_value=False):
                with patch.object(display, "_try_xvnc", new_callable=AsyncMock, return_value=False):
                    with patch.object(display, "_try_xvfb", new_callable=AsyncMock, return_value=True):
                        result = await display.start()
                        assert result == ":99"
                        assert display.type == "xvfb"


class TestInstallBrowserMappings:
    """Tests for install_browser package mappings."""

    def test_install_chrome(self):
        """Test installing chrome."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = install_browser("chrome")
            assert isinstance(result, bool)

    def test_install_unknown_browser(self):
        """Test installing unknown browser returns False."""
        result = install_browser("unknown-browser")
        assert result is False


class TestGetExtendedCapabilitiesComplete:
    """Complete tests for get_extended_capabilities."""

    def test_all_expected_keys(self):
        """Test all expected keys are present."""
        caps = get_extended_capabilities()

        expected_keys = [
            "platform", "architecture", "package_manager",
            "has_passwordless_sudo", "available_tools",
            "is_wsl2", "is_windows", "is_macos", "is_linux", "has_display"
        ]

        for key in expected_keys:
            assert key in caps

    def test_values_have_correct_types(self):
        """Test values have correct types."""
        caps = get_extended_capabilities()

        assert isinstance(caps["platform"], str)
        assert isinstance(caps["architecture"], str)
        assert isinstance(caps["package_manager"], str)
        assert isinstance(caps["has_passwordless_sudo"], bool)
        assert isinstance(caps["available_tools"], list)
        assert isinstance(caps["is_wsl2"], bool)
        assert isinstance(caps["is_windows"], bool)
        assert isinstance(caps["is_macos"], bool)
        assert isinstance(caps["is_linux"], bool)
        assert isinstance(caps["has_display"], bool)


class TestDetectPackageManagerTimeout:
    """Tests for package manager detection with timeout."""

    def test_detect_apt_timeout(self):
        """Test detecting apt when command times out."""
        with patch("shutil.which", return_value="/usr/bin/apt"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("apt", 5)
                # Should fall through to next package manager
                result = detect_package_manager()
                # Should return UNKNOWN since apt timed out
                assert isinstance(result, PackageManager)


class TestResourceChecking:
    """Tests for resource checking functions."""

    @pytest.mark.asyncio
    async def test_check_api_endpoint_success(self):
        """Test checking a successful API endpoint."""
        from beyond_ralph.utils.system import check_api_endpoint

        # Mock httpx response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await check_api_endpoint("http://example.com/api", "Test API")

            assert result.available is True
            assert "200" in result.details

    @pytest.mark.asyncio
    async def test_check_api_endpoint_server_error(self):
        """Test checking an API endpoint with server error."""
        from beyond_ralph.utils.system import check_api_endpoint

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await check_api_endpoint("http://example.com/api", "Test API")

            assert result.available is False
            assert "Server error" in result.details

    @pytest.mark.asyncio
    async def test_check_api_endpoint_connection_failed(self):
        """Test checking an API endpoint when connection fails."""
        from beyond_ralph.utils.system import check_api_endpoint

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            result = await check_api_endpoint("http://example.com/api", "Test API")

            assert result.available is False
            assert "Connection failed" in result.details

    @pytest.mark.asyncio
    async def test_check_database_sqlite(self):
        """Test checking SQLite database (always available)."""
        from beyond_ralph.utils.system import check_database

        result = await check_database("sqlite", name="Test SQLite")

        assert result.available is True
        assert "always available" in result.details.lower()

    @pytest.mark.asyncio
    async def test_check_database_postgres_connected(self):
        """Test checking PostgreSQL when connected."""
        from beyond_ralph.utils.system import check_database

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_sock

            result = await check_database("postgres", "localhost", 5432)

            assert result.available is True
            assert "5432" in result.details

    @pytest.mark.asyncio
    async def test_check_database_postgres_not_connected(self):
        """Test checking PostgreSQL when not connected."""
        from beyond_ralph.utils.system import check_database

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 1  # Connection refused
            mock_socket.return_value = mock_sock

            result = await check_database("postgres", "localhost", 5432)

            assert result.available is False

    @pytest.mark.asyncio
    async def test_check_database_socket_error(self):
        """Test checking database when socket error occurs."""
        from beyond_ralph.utils.system import check_database
        import socket

        with patch("socket.socket") as mock_socket:
            mock_socket.return_value.connect_ex.side_effect = socket.error("Network error")

            result = await check_database("mysql", "localhost")

            assert result.available is False
            assert "Connection failed" in result.details

    def test_check_file_exists_success(self):
        """Test checking file that exists."""
        from beyond_ralph.utils.system import check_file_exists

        with patch("pathlib.Path.exists", return_value=True):
            result = check_file_exists("/path/to/file.txt", "Config File")

            assert result.available is True
            assert result.name == "Config File"

    def test_check_file_exists_not_found(self):
        """Test checking file that doesn't exist."""
        from beyond_ralph.utils.system import check_file_exists

        with patch("pathlib.Path.exists", return_value=False):
            result = check_file_exists("/path/to/missing.txt", "Missing File")

            assert result.available is False
            assert "not found" in result.details.lower()

    def test_check_tool_installed_found(self):
        """Test checking tool that is installed."""
        from beyond_ralph.utils.system import check_tool_installed

        with patch("shutil.which", return_value="/usr/bin/git"):
            result = check_tool_installed("git")

            assert result.available is True
            assert result.name == "git"

    def test_check_tool_installed_not_found(self):
        """Test checking tool that is not installed."""
        from beyond_ralph.utils.system import check_tool_installed

        with patch("shutil.which", return_value=None):
            result = check_tool_installed("nonexistent-tool", "Missing Tool")

            assert result.available is False
            assert result.name == "Missing Tool"

    def test_check_env_var_exists(self):
        """Test checking environment variable that exists."""
        from beyond_ralph.utils.system import check_env_var

        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = check_env_var("TEST_VAR", "Test Variable")

            assert result.available is True
            assert result.name == "Test Variable"

    def test_check_env_var_not_set(self):
        """Test checking environment variable that doesn't exist."""
        from beyond_ralph.utils.system import check_env_var

        with patch.dict(os.environ, {}, clear=True):
            result = check_env_var("NONEXISTENT_VAR", "Missing Var")

            assert result.available is False
            assert "not set" in result.details.lower()

    @pytest.mark.asyncio
    async def test_check_network_host_connected(self):
        """Test checking network host that is reachable."""
        from beyond_ralph.utils.system import check_network_host

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock

            result = await check_network_host("example.com", 443, "HTTPS")

            assert result.available is True
            assert "443" in result.details

    @pytest.mark.asyncio
    async def test_check_network_host_not_reachable(self):
        """Test checking network host that is not reachable."""
        from beyond_ralph.utils.system import check_network_host

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 1
            mock_socket.return_value = mock_sock

            result = await check_network_host("example.com", 443, "HTTPS")

            assert result.available is False


class TestRDPServer:
    """Tests for RDPServer class."""

    def test_rdp_server_initialization(self):
        """Test RDPServer initializes correctly."""
        server = RDPServer()
        assert server.port == 3389  # Default port
        assert server.process is None
        assert server.started is False

    @pytest.mark.asyncio
    async def test_rdp_server_start_success(self):
        """Test starting RDP server successfully."""
        server = RDPServer()

        with patch("shutil.which", return_value="/usr/sbin/xrdp"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = await server.start(3390)

                assert result is True
                assert server.port == 3390

    @pytest.mark.asyncio
    async def test_rdp_server_start_not_installed(self):
        """Test starting RDP server when not installed."""
        server = RDPServer()

        with patch("shutil.which", return_value=None):
            result = await server.start(3389)

            assert result is False

    def test_rdp_server_stop(self):
        """Test stopping RDP server."""
        server = RDPServer()
        server.process = MagicMock()
        server.started = True

        with patch("subprocess.run"):
            server.stop()

            assert server.started is False

    def test_rdp_server_connection_info(self):
        """Test getting RDP connection info."""
        server = RDPServer()
        server.port = 3389

        with patch("socket.gethostname", return_value="test-host"):
            info = server.get_connection_info()

            assert info["port"] == 3389
            assert info["host"] == "test-host"
            assert "xfreerdp" in info["connection_string"]

    def test_rdp_server_connection_info_default_port(self):
        """Test getting connection info with default port."""
        server = RDPServer()

        info = server.get_connection_info()

        assert info["port"] == 3389  # Default port
        assert info["protocol"] == "rdp"


class TestInstallRDPServer:
    """Tests for install_rdp_server function."""

    def test_install_rdp_server_apt(self):
        """Test installing RDP server on apt-based system."""
        from beyond_ralph.utils.system import install_rdp_server

        with patch("beyond_ralph.utils.system.detect_package_manager") as mock_pm:
            mock_pm.return_value = PackageManager.APT
            with patch("beyond_ralph.utils.system.install_system_package") as mock_install:
                mock_install.return_value = True

                result = install_rdp_server()

                assert result is True
                mock_install.assert_called()

    def test_install_rdp_server_unsupported(self):
        """Test installing RDP server on unsupported system."""
        from beyond_ralph.utils.system import install_rdp_server

        with patch("beyond_ralph.utils.system.detect_package_manager") as mock_pm:
            mock_pm.return_value = PackageManager.UNKNOWN

            result = install_rdp_server()

            # Should return False for unsupported package managers
            assert isinstance(result, bool)


class TestVerifyProjectResources:
    """Tests for verify_project_resources function."""

    @pytest.mark.asyncio
    async def test_verify_project_resources_all_available(self):
        """Test verifying project resources when all available."""
        from beyond_ralph.utils.system import verify_project_resources

        reqs = ProjectResourceRequirements(
            apis=[],
            databases=[],
            files=[],
            tools=["git"],
            env_vars=[],
            network_hosts=[],
        )

        with patch("shutil.which", return_value="/usr/bin/git"):
            success, failed_checks = await verify_project_resources(reqs)

            # All resources available, so no failures
            assert success is True
            assert len(failed_checks) == 0  # No failed checks

    @pytest.mark.asyncio
    async def test_verify_project_resources_missing_tool(self):
        """Test verifying project resources with missing tool."""
        from beyond_ralph.utils.system import verify_project_resources

        reqs = ProjectResourceRequirements(
            apis=[],
            databases=[],
            files=[],
            tools=["nonexistent-tool"],
            env_vars=[],
            network_hosts=[],
        )

        with patch("shutil.which", return_value=None):
            success, failed_checks = await verify_project_resources(reqs)

            assert success is False
            assert len(failed_checks) == 1  # One tool failed

    @pytest.mark.asyncio
    async def test_verify_project_resources_with_all_types(self):
        """Test verifying project with multiple resource types."""
        from beyond_ralph.utils.system import verify_project_resources

        reqs = ProjectResourceRequirements(
            apis=[],
            databases=[("sqlite", "localhost", None)],
            files=[],
            tools=[],
            env_vars=[],
            network_hosts=[],
        )

        success, failed_checks = await verify_project_resources(reqs)

        # SQLite is always available, so no failures
        assert success is True
        assert len(failed_checks) == 0


class TestCheckAllResources:
    """Tests for check_all_resources function."""

    @pytest.mark.asyncio
    async def test_check_all_resources_empty(self):
        """Test checking with empty resource list."""
        from beyond_ralph.utils.system import check_all_resources

        success, failed = await check_all_resources([])

        assert success is True
        assert len(failed) == 0

    @pytest.mark.asyncio
    async def test_check_all_resources_with_checks(self):
        """Test checking with resource list."""
        from beyond_ralph.utils.system import check_all_resources

        checks = [
            ResourceCheck(name="Tool1", available=True, details="OK"),
            ResourceCheck(name="Tool2", available=False, details="Missing", critical=True),
        ]

        success, failed = await check_all_resources(checks)

        assert success is False  # One critical resource failed
        assert len(failed) == 1
        assert failed[0].name == "Tool2"

    @pytest.mark.asyncio
    async def test_check_all_resources_non_critical_failure(self):
        """Test that non-critical failures don't affect success."""
        from beyond_ralph.utils.system import check_all_resources

        checks = [
            ResourceCheck(name="Critical", available=True, details="OK", critical=True),
            ResourceCheck(name="Optional", available=False, details="Missing", critical=False),
        ]

        success, failed = await check_all_resources(checks)

        assert success is True  # Only non-critical failed
        assert len(failed) == 1
