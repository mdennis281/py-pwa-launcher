"""
Get Chromium - Find or install Chromium-based browsers.
"""
import logging
from pathlib import Path
from typing import Optional, List

from pwa_launcher.get_chromium.find_chromium import find_system_chromium, find_system_chromiums
from pwa_launcher.get_chromium.install_chromium import find_existing_chromium, install_chromium


logger = logging.getLogger(__name__)


class ChromiumNotFoundError(Exception):
    """Raised when no Chromium browser is found and installation is disallowed."""


def get_chromium_install(
    allow_system: bool = True,
    allow_download: bool = True,
    install_dir: Optional[Path] = None,
    force_reinstall: bool = False,
) -> Path:
    """
    Get a Chromium browser executable path.
    
    Attempts to find Chromium in the following order:
    1. System-installed Chrome/Edge (if allow_system=True)
    2. Previously downloaded portable Chrome (if allow_download=True)
    3. Download new portable Chrome (if allow_download=True)
    
    Args:
        allow_system: Search for system-installed Chrome/Edge first
        allow_download: Allow downloading portable Chrome if not found
        install_dir: Directory for portable Chrome installation
        force_reinstall: Force download even if portable Chrome exists
        
    Returns:
        Path to Chromium executable
        
    Raises:
        ChromiumNotFoundError: No Chromium found and installation is disallowed
    """
    # Step 1: Try system-installed browsers
    if allow_system:
        logger.debug("Searching for system-installed Chromium browsers...")
        try:
            system_chrome = find_system_chromium()
            logger.info("Using system-installed browser: %s", system_chrome)
            return system_chrome
        except FileNotFoundError:
            logger.debug("No system browser found")
    
    # Step 2: Check if portable Chrome was already downloaded
    if allow_download and not force_reinstall:
        logger.debug("Checking for existing portable Chromium installation...")
        existing_chrome = find_existing_chromium(install_dir)
        if existing_chrome:
            logger.info("Using existing portable Chromium: %s", existing_chrome)
            return existing_chrome
        logger.debug("No existing portable installation found")
    
    # Step 3: Download portable Chrome
    if allow_download:
        logger.info("Downloading portable Chromium...")
        try:
            chrome_path = install_chromium(
                install_dir=install_dir,
                clean_existing=False,
                force_reinstall=force_reinstall
            )
            logger.info("Using downloaded portable Chromium: %s", chrome_path)
            return chrome_path
        except Exception as e:
            logger.error("Failed to download Chromium: %s", e)
            raise ChromiumNotFoundError(
                "Failed to download Chromium and no other browser found"
            ) from e
    
    # No options left
    logger.error("No Chromium browser found and installation is disallowed")
    raise ChromiumNotFoundError(
        "No Chromium browser found. Either install Chrome/Edge on your system, "
        "or allow Chromium download by setting allow_download=True"
    )


def get_chromium_installs(
    allow_system: bool = True,
    allow_download: bool = False,
    install_dir: Optional[Path] = None,
) -> List[Path]:
    """
    Get all found Chromium browser executable paths.
    
    Args:
        allow_system: Include system-installed Chrome/Edge
        allow_download: Include downloaded portable Chrome
        install_dir: Directory for portable Chrome installation
        
    Returns:
        List of Paths to Chromium executables (may be empty)
    """
    found = []
    
    # Get system browsers
    if allow_system:
        logger.debug("Searching for system-installed Chromium browsers...")
        found.extend(find_system_chromiums())
    
    # Get portable Chrome
    if allow_download:
        logger.debug("Checking for portable Chromium installation...")
        existing_chrome = find_existing_chromium(install_dir)
        if existing_chrome:
            found.append(existing_chrome)
    
    logger.info("Found %d Chromium browser(s)", len(found))
    return found


__all__ = [
    "get_chromium_install",
    "get_chromium_installs",
    "ChromiumNotFoundError",
]
