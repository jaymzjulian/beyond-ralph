"""System utilities for Beyond Ralph.

Includes detection of system capabilities like passwordless sudo,
package managers, and available tools.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
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
