"""
Find system-installed Chromium-based browsers (Chrome, Edge).
"""
import logging
import os
import platform
from pathlib import Path
from typing import Optional, List


logger = logging.getLogger(__name__)


def get_chrome_paths() -> List[Path]:
    """
    Get potential Google Chrome installation paths for the current platform.
    
    Returns:
        List of potential Chrome executable paths
    """
    system = platform.system()
    paths = []
    
    if system == "Windows":
        # Common Chrome installation paths on Windows
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        
        paths.extend([
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(local_appdata) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ])
    
    elif system == "Darwin":  # macOS
        paths.extend([
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications" / "Google Chrome.app" / "Contents" / "MacOS" / "Google Chrome",
        ])
    
    elif system == "Linux":
        paths.extend([
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/google-chrome-stable"),
            Path("/usr/bin/chrome"),
            Path("/usr/local/bin/google-chrome"),
            Path("/usr/local/bin/chrome"),
            Path("/opt/google/chrome/chrome"),
            Path("/snap/bin/chromium"),
        ])
    
    return paths


def get_edge_paths() -> List[Path]:
    """
    Get potential Microsoft Edge installation paths for the current platform.
    
    Returns:
        List of potential Edge executable paths
    """
    system = platform.system()
    paths = []
    
    if system == "Windows":
        # Common Edge installation paths on Windows
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        paths.extend([
            Path(program_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(program_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ])
    
    elif system == "Darwin":  # macOS
        paths.extend([
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path.home() / "Applications" / "Microsoft Edge.app" / "Contents" / "MacOS" / "Microsoft Edge",
        ])
    
    elif system == "Linux":
        paths.extend([
            Path("/usr/bin/microsoft-edge"),
            Path("/usr/bin/microsoft-edge-stable"),
            Path("/usr/bin/microsoft-edge-beta"),
            Path("/usr/bin/microsoft-edge-dev"),
            Path("/opt/microsoft/msedge/msedge"),
            Path("/snap/bin/microsoft-edge"),
        ])
    
    return paths


def find_chrome() -> Optional[Path]:
    """
    Find Google Chrome installation on the system.
    
    Returns:
        Path to Chrome executable if found, None otherwise
    """
    logger.debug("Searching for Google Chrome...")
    for path in get_chrome_paths():
        if path.exists() and path.is_file():
            logger.info("Found Chrome at: %s", path)
            return path
    logger.debug("Chrome not found")
    return None


def find_edge() -> Optional[Path]:
    """
    Find Microsoft Edge installation on the system.
    
    Returns:
        Path to Edge executable if found, None otherwise
    """
    logger.debug("Searching for Microsoft Edge...")
    for path in get_edge_paths():
        if path.exists() and path.is_file():
            logger.info("Found Edge at: %s", path)
            return path
    logger.debug("Edge not found")
    return None


def find_system_chromium() -> Optional[Path]:
    """
    Find a system-installed Chromium-based browser.
    
    Searches for browsers in priority order:
    1. Google Chrome (preferred)
    2. Microsoft Edge (fallback)
    
    Returns:
        Path to the first found Chromium-based browser executable, None if not found
    """
    logger.debug("Searching for system Chromium browsers...")
    
    # Try Chrome first (priority)
    chrome_path = find_chrome()
    if chrome_path:
        logger.info("Using Chrome as preferred browser")
        return chrome_path
    
    # Fallback to Edge
    edge_path = find_edge()
    if edge_path:
        logger.info("Using Edge as fallback browser")
        return edge_path
    
    logger.warning("No Chromium-based browser found on system")
    return None


def get_chromium_info() -> dict:
    """
    Get information about available Chromium-based browsers on the system.
    
    Returns:
        Dictionary with browser availability information
    """
    chrome = find_chrome()
    edge = find_edge()
    
    return {
        'chrome': {
            'available': chrome is not None,
            'path': str(chrome) if chrome else None,
        },
        'edge': {
            'available': edge is not None,
            'path': str(edge) if edge else None,
        },
        'any_available': chrome is not None or edge is not None,
        'preferred': str(chrome) if chrome else (str(edge) if edge else None),
    }


if __name__ == "__main__":
    # Configure logging for the test
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    print("=== Chromium Browser Finder ===\n")
    
    info = get_chromium_info()
    
    print(f"Google Chrome: {'✓' if info['chrome']['available'] else '✗'}")
    if info['chrome']['available']:
        print(f"  Path: {info['chrome']['path']}")
    
    print(f"\nMicrosoft Edge: {'✓' if info['edge']['available'] else '✗'}")
    if info['edge']['available']:
        print(f"  Path: {info['edge']['path']}")
    
    print(f"\nPreferred browser: {info['preferred'] if info['preferred'] else 'None found'}")
    
    # Test the main function
    print("\n=== Using find_system_chromium() ===")
    chromium = find_system_chromium()
    if chromium:
        print(f"Found: {chromium}")
        print(f"Exists: {chromium.exists()}")
    else:
        print("No Chromium-based browser found")
