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
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        
        # Chrome paths
        paths.extend([
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(local_appdata) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ])
        
        # Edge paths
        paths.extend([
            Path(program_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(program_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ])
    
    elif system == "Darwin":  # macOS
        # Chrome paths
        paths.extend([
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications" / "Google Chrome.app" / "Contents" / "MacOS" / "Google Chrome",
        ])
        
        # Edge paths
        paths.extend([
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path.home() / "Applications" / "Microsoft Edge.app" / "Contents" / "MacOS" / "Microsoft Edge",
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
            logger.info("Found Chromium at: %s", path)
            return path
    
    logger.error("No Chromium-based browser found on system")
    raise FileNotFoundError("No system Chromium browser found (Chrome or Edge)")


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
    
    logger.info("Found %d Chromium browser(s)", len(found))
    return found
