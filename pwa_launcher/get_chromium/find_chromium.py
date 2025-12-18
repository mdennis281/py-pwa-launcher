"""
Find system-installed Chromium-based browsers (Chrome, Edge).
"""
import logging
import platform
from pathlib import Path
from typing import List

from .constants import (
    get_windows_chromium_paths,
    get_macos_chromium_paths,
    get_linux_chromium_paths,
)


logger = logging.getLogger(__name__)


def _get_chromium_paths() -> List[Path]:
    """Get all potential Chromium browser paths for the current platform."""
    system = platform.system()

    if system == "Windows":
        return get_windows_chromium_paths()
    elif system == "Darwin":  # macOS
        return get_macos_chromium_paths()
    elif system == "Linux":
        return get_linux_chromium_paths()

    return []


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
