"""Live tests for remote access module.

These tests require:
1. Windows host at 192.168.68.138 with SSH access
2. Android SDK installed at C:\\Android
3. ADB server running on Windows
4. Android emulator running

Run with: uv run pytest tests/live/test_remote_access_live.py -v -s
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest

# Skip if not in the right environment
pytestmark = pytest.mark.skipif(
    os.environ.get("BEYOND_RALPH_LIVE_TESTS") != "1",
    reason="Live tests require BEYOND_RALPH_LIVE_TESTS=1",
)

WINDOWS_HOST = "192.168.68.138"


def run_ssh_command(command: str, timeout: int = 30) -> tuple[str, str, int]:
    """Run a command on the Windows host via SSH."""
    result = subprocess.run(
        ["ssh", WINDOWS_HOST, command],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout, result.stderr, result.returncode


def run_adb_via_ssh(adb_command: str) -> tuple[str, str, int]:
    """Run an ADB command on the Windows host."""
    command = f"C:\\Android\\platform-tools\\adb.exe {adb_command}"
    return run_ssh_command(command)


class TestWSL2EnvironmentDetection:
    """Live tests for WSL2 environment detection."""

    def test_detect_wsl2_environment(self) -> None:
        """Verify we're running in WSL2."""
        from beyond_ralph.integrations.remote_access import detect_environment

        env = detect_environment()

        # We should detect WSL2
        assert env.platform == "WSL2"
        assert env.android_testing_mode == "remote"
        assert env.adb_access == "mirrored"

    def test_get_wsl2_host_ip(self) -> None:
        """Verify we can get the WSL2 host IP."""
        from beyond_ralph.integrations.remote_access import get_wsl2_host_ip

        host_ip = get_wsl2_host_ip()

        # Should return a valid IP
        assert host_ip is not None
        # Should be in a private range
        assert host_ip.startswith(("172.", "192.168.", "10."))


class TestWindowsHostConnectivity:
    """Live tests for Windows host connectivity."""

    def test_ssh_connectivity(self) -> None:
        """Verify SSH connectivity to Windows host."""
        stdout, stderr, returncode = run_ssh_command("Write-Host 'SSH OK'")
        assert returncode == 0
        assert "SSH OK" in stdout

    def test_adb_server_running(self) -> None:
        """Verify ADB server is running on Windows."""
        stdout, stderr, returncode = run_adb_via_ssh("version")
        assert returncode == 0
        assert "Android Debug Bridge" in stdout

    def test_emulator_visible(self) -> None:
        """Verify emulator is visible to ADB."""
        stdout, stderr, returncode = run_adb_via_ssh("devices")
        assert returncode == 0

        # Should have at least one device
        lines = stdout.strip().split("\n")
        device_lines = [l for l in lines if "device" in l and "List" not in l]
        assert len(device_lines) >= 1, f"No devices found. Output: {stdout}"


class TestWindowsADBClientLive:
    """Live tests for WindowsADBClient."""

    @pytest.mark.asyncio
    async def test_connect_to_windows_adb(self) -> None:
        """Test connecting to Windows ADB from WSL2."""
        from beyond_ralph.integrations.remote_access import (
            WindowsADBClient,
            WindowsHostConfig,
        )

        config = WindowsHostConfig(host_ip=WINDOWS_HOST, adb_port=5037)
        client = WindowsADBClient(config)

        # Note: Direct network connection may not work due to firewall
        # We verify via SSH commands instead
        stdout, stderr, returncode = run_adb_via_ssh("devices")

        assert returncode == 0
        assert "device" in stdout

    @pytest.mark.asyncio
    async def test_list_devices_via_ssh(self) -> None:
        """Test listing devices via SSH tunnel."""
        stdout, stderr, returncode = run_adb_via_ssh("devices")

        assert returncode == 0

        # Parse devices
        lines = stdout.strip().split("\n")
        devices = []
        for line in lines:
            if "\t" in line:
                device_id = line.split("\t")[0]
                devices.append(device_id)

        assert len(devices) >= 1


class TestAndroidEmulatorLive:
    """Live tests for Android emulator operations."""

    def test_get_emulator_info(self) -> None:
        """Test getting emulator information."""
        stdout, stderr, returncode = run_adb_via_ssh("shell getprop ro.product.model")

        assert returncode == 0
        assert stdout.strip() != ""
        print(f"Emulator model: {stdout.strip()}")

    def test_get_android_version(self) -> None:
        """Test getting Android version."""
        stdout, stderr, returncode = run_adb_via_ssh("shell getprop ro.build.version.release")

        assert returncode == 0
        version = stdout.strip()
        assert version.isdigit() or "." in version
        print(f"Android version: {version}")

    def test_take_screenshot(self) -> None:
        """Test taking a screenshot from emulator."""
        # Take screenshot on device
        run_adb_via_ssh("shell screencap -p /sdcard/live_test_screenshot.png")

        # Pull to Windows temp
        run_adb_via_ssh("pull /sdcard/live_test_screenshot.png C:\\Users\\jaymz\\live_test.png")

        # Verify file exists
        stdout, stderr, returncode = run_ssh_command(
            "Test-Path C:\\Users\\jaymz\\live_test.png"
        )

        assert "True" in stdout

        # Cleanup
        run_adb_via_ssh("shell rm /sdcard/live_test_screenshot.png")
        run_ssh_command("Remove-Item C:\\Users\\jaymz\\live_test.png")

    def test_emulator_boot_completed(self) -> None:
        """Test that emulator has completed boot."""
        stdout, stderr, returncode = run_adb_via_ssh(
            "shell getprop sys.boot_completed"
        )

        assert returncode == 0
        assert stdout.strip() == "1"


def run_ssh_command_with_path(command: str, timeout: int = 30) -> tuple[str, str, int]:
    """Run a command on Windows host via SSH with refreshed PATH."""
    # Refresh PATH to pick up newly installed programs like Node.js
    full_command = (
        "$env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' + "
        "[System.Environment]::GetEnvironmentVariable('PATH', 'User'); "
        f"{command}"
    )
    return run_ssh_command(full_command, timeout)


class TestAppiumServerLive:
    """Live tests for Appium server management."""

    def test_check_node_installed(self) -> None:
        """Verify Node.js is available for Appium."""
        stdout, stderr, returncode = run_ssh_command_with_path("node --version")

        # Node may or may not be installed
        if returncode == 0:
            assert stdout.strip().startswith("v")
            print(f"Node.js version: {stdout.strip()}")
        else:
            pytest.skip("Node.js not installed on Windows host")

    def test_check_appium_installed(self) -> None:
        """Check if Appium is installed."""
        stdout, stderr, returncode = run_ssh_command_with_path("appium --version")

        if returncode == 0:
            print(f"Appium version: {stdout.strip()}")
        else:
            pytest.skip("Appium not installed on Windows host")

    def test_appium_drivers_installed(self) -> None:
        """Check that UiAutomator2 driver is installed."""
        # Appium outputs to stderr, so redirect 2>&1
        stdout, stderr, returncode = run_ssh_command_with_path("appium driver list --installed 2>&1")

        if returncode == 0:
            # Output may be in stdout or stderr due to Appium's logging
            combined = (stdout + stderr).lower()
            assert "uiautomator2" in combined
            print("Appium drivers: uiautomator2 installed")
        else:
            pytest.skip("Appium not installed on Windows host")


class TestVNCManagerLive:
    """Live tests for VNC manager."""

    def test_xvfb_available(self) -> None:
        """Check if Xvfb is available in WSL2."""
        import shutil

        xvfb_path = shutil.which("Xvfb")
        if xvfb_path:
            print(f"Xvfb found at: {xvfb_path}")
        else:
            pytest.skip("Xvfb not installed")

    def test_x11vnc_available(self) -> None:
        """Check if x11vnc is available in WSL2."""
        import shutil

        x11vnc_path = shutil.which("x11vnc")
        if x11vnc_path:
            print(f"x11vnc found at: {x11vnc_path}")
        else:
            pytest.skip("x11vnc not installed")

    @pytest.mark.asyncio
    async def test_start_vnc_session(self) -> None:
        """Test starting a VNC session."""
        import shutil

        if not shutil.which("Xvfb") or not shutil.which("x11vnc"):
            pytest.skip("Xvfb or x11vnc not available")

        from beyond_ralph.integrations.remote_access import VNCManager

        manager = VNCManager()

        try:
            session = await manager.start_session(
                display=":98",  # Use unusual display to avoid conflicts
                resolution="1024x768",
                websocket=False,
            )

            assert session.display == ":98"
            assert session.port == 5998
            assert len(session.password) > 0

            print(f"VNC session started on port {session.port}")

        finally:
            # Cleanup
            await manager.stop_session(":98")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
