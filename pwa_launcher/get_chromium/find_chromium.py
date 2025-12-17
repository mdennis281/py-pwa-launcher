"""
Find system-installed Chromium-based browsers (Chrome, Edge).
"""
import logging
import os
import platform
from pathlib import Path
from typing import List


logger = logging.getLogger(__name__)


def _get_chromium_paths() -> List[Path]:
    """Get all potential Chromium browser paths for the current platform."""
    system = platform.system()
    paths = []

    if system == "Windows":
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get(
            'PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        local_appdata = os.environ.get('LOCALAPPDATA', '')

        # Chrome paths
        paths.extend([
            Path(program_files) / "Google" / "Chrome" /
            "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" /
            "Chrome" / "Application" / "chrome.exe",
            Path(local_appdata) / "Google" / "Chrome" /
            "Application" / "chrome.exe",
        ])

        # Edge paths
        paths.extend([
            Path(program_files) / "Microsoft" /
            "Edge" / "Application" / "msedge.exe",
            Path(program_files_x86) / "Microsoft" /
            "Edge" / "Application" / "msedge.exe",
        ])

        # Chromium paths
        paths.extend([
            Path(program_files) / "Chromium" /
            "Application" / "chrome.exe",
            Path(program_files_x86) / "Chromium" /
            "Application" / "chrome.exe",
            Path(local_appdata) / "Chromium" /
            "Application" / "chrome.exe",
        ])

        # Brave paths
        paths.extend([
            Path(program_files) / "BraveSoftware" /
            "Brave-Browser" / "Application" / "brave.exe",
            Path(program_files_x86) / "BraveSoftware" /
            "Brave-Browser" / "Application" / "brave.exe",
            Path(local_appdata) / "BraveSoftware" /
            "Brave-Browser" / "Application" / "brave.exe",
        ])

        # Vivaldi paths
        paths.extend([
            Path(program_files) / "Vivaldi" /
            "Application" / "vivaldi.exe",
            Path(program_files_x86) / "Vivaldi" /
            "Application" / "vivaldi.exe",
            Path(local_appdata) / "Vivaldi" /
            "Application" / "vivaldi.exe",
        ])

        # Opera paths
        paths.extend([
            Path(program_files) / "Opera" / "opera.exe",
            Path(program_files_x86) / "Opera" / "opera.exe",
            Path(local_appdata) / "Programs" / "Opera" / "opera.exe",
        ])

    elif system == "Darwin":  # macOS
        # Chrome paths
        paths.extend([
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications" / "Google Chrome.app" /
            "Contents" / "MacOS" / "Google Chrome",
        ])

        # Edge paths
        paths.extend([
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path.home() / "Applications" / "Microsoft Edge.app" /
            "Contents" / "MacOS" / "Microsoft Edge",
        ])

        # Chromium paths
        paths.extend([
            Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
            Path.home() / "Applications" /
            "Chromium.app" / "Contents" / "MacOS" / "Chromium",
        ])

        # Brave paths
        paths.extend([
            Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
            Path.home() / "Applications" / "Brave Browser.app" /
            "Contents" / "MacOS" / "Brave Browser",
        ])

        # Vivaldi paths
        paths.extend([
            Path("/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"),
            Path.home() / "Applications" /
            "Vivaldi.app" / "Contents" / "MacOS" / "Vivaldi",
        ])

        # Opera paths
        paths.extend([
            Path("/Applications/Opera.app/Contents/MacOS/Opera"),
            Path.home() / "Applications" /
            "Opera.app" / "Contents" / "MacOS" / "Opera",
        ])

        # Arc paths
        paths.extend([
            Path("/Applications/Arc.app/Contents/MacOS/Arc"),
            Path.home() / "Applications" /
            "Arc.app" / "Contents" / "MacOS" / "Arc",
        ])

    elif system == "Linux":
        # Chrome paths
        paths.extend([
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/google-chrome-stable"),
            Path("/usr/bin/chrome"),
            Path("/usr/local/bin/google-chrome"),
            Path("/usr/local/bin/chrome"),
            Path("/opt/google/chrome/chrome"),
            Path("/snap/bin/chromium"),
        ])

        # Edge paths
        paths.extend([
            Path("/usr/bin/microsoft-edge"),
            Path("/usr/bin/microsoft-edge-stable"),
            Path("/usr/bin/microsoft-edge-beta"),
            Path("/usr/bin/microsoft-edge-dev"),
            Path("/opt/microsoft/msedge/msedge"),
            Path("/snap/bin/microsoft-edge"),
        ])

        # Chromium paths
        paths.extend([
            Path("/usr/bin/chromium"),
            Path("/usr/bin/chromium-browser"),
            Path("/usr/local/bin/chromium"),
            Path("/usr/local/bin/chromium-browser"),
            Path("/snap/bin/chromium"),
            Path("/var/lib/snapd/snap/bin/chromium"),
        ])

        # Brave paths
        paths.extend([
            Path("/usr/bin/brave-browser"),
            Path("/usr/bin/brave"),
            Path("/snap/bin/brave"),
            Path("/var/lib/flatpak/exports/bin/com.brave.Browser"),
            Path.home() / ".local" / "share" /
            "flatpak" / "exports" / "bin" / "com.brave.Browser",
        ])

        # Vivaldi paths
        paths.extend([
            Path("/usr/bin/vivaldi"),
            Path("/usr/bin/vivaldi-stable"),
            Path("/opt/vivaldi/vivaldi"),
            Path("/snap/bin/vivaldi"),
        ])

        # Opera paths
        paths.extend([
            Path("/usr/bin/opera"),
            Path("/usr/bin/opera-stable"),
            Path("/snap/bin/opera"),
        ])

    return paths


def find_system_chromium() -> Path:
    """
    Get the first found system-installed Chromium browser.

    Returns:
        Path to Chromium executable

    Raises:
        FileNotFoundError: No Chromium browser found
    """
    logger.debug("Searching for system Chromium browsers...")

    for path in _get_chromium_paths():
        if path.exists() and path.is_file():
            logger.debug("Found Chromium at: %s", path)
            return path

    logger.error("No Chromium-based browser found on system")
    raise FileNotFoundError(
        "No system Chromium browser found (Chrome or Edge)")


def find_system_chromiums() -> List[Path]:
    """
    Get all found system-installed Chromium browsers.

    Returns:
        List of Paths to Chromium executables (may be empty)
    """
    logger.debug("Searching for all system Chromium browsers...")

    found = []
    for path in _get_chromium_paths():
        if path.exists() and path.is_file():
            found.append(path)
            logger.debug("Found: %s", path)

    logger.debug("Found %d Chromium browser(s)", len(found))
    return found
