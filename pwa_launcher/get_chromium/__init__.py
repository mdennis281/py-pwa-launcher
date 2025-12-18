"""
Get Chromium - Find system-installed Chromium-based browsers.
"""
import logging
from pathlib import Path
from typing import List

from pwa_launcher.get_chromium.find_chromium import find_system_chromium, find_system_chromiums


logger = logging.getLogger(__name__)


class ChromiumNotFoundError(Exception):
    """Raised when no Chromium browser is found."""


def get_chromium_install() -> Path:
    """
    Get a Chromium browser executable path.

    Searches for system-installed Chromium-based browsers (Chrome, Edge, Brave, etc.).

    Returns:
        Path to Chromium executable

    Raises:
        ChromiumNotFoundError: No Chromium browser found on system
    """
    logger.debug("Searching for system-installed Chromium browsers...")
    try:
        system_chrome = find_system_chromium()
        logger.debug("Found system-installed browser: %s", system_chrome)
        return system_chrome
    except FileNotFoundError as exc:
        logger.error("No Chromium browser found on system")
        raise ChromiumNotFoundError(
            "No Chromium browser found. Please install Chrome, Edge, Brave, Vivaldi, or another Chromium-based browser."
        ) from exc


def get_chromium_installs() -> List[Path]:
    """
    Get all found Chromium browser executable paths.

    Returns:
        List of Paths to Chromium executables (may be empty)
    """
    logger.debug("Searching for system-installed Chromium browsers...")
    found = find_system_chromiums()
    logger.debug("Found %d Chromium browser(s)", len(found))
    return found


__all__ = [
    "get_chromium_install",
    "get_chromium_installs",
    "ChromiumNotFoundError",
]
