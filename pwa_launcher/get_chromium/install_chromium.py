"""
Cross-platform Chromium installer that downloads portable Chromium to a temporary folder.
Uses Chrome for Testing (official portable builds) for easy, self-contained installation.
"""
import logging
import os
import platform
import tempfile
import zipfile
import urllib.request
import shutil
import json
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def get_chrome_for_testing_url() -> tuple[str, str]:
    """
    Get the Chrome for Testing download URL for the current platform.
    Chrome for Testing provides portable, self-contained Chromium builds.
    
    Returns:
        tuple: (download_url, platform_name)
    """
    system = platform.system()
    machine = platform.machine().lower()
    
    # Determine platform identifier
    if system == "Windows":
        if "64" in machine or "amd64" in machine or "x86_64" in machine:
            platform_id = "win64"
        else:
            platform_id = "win32"
    elif system == "Darwin":  # macOS
        if "arm" in machine or "aarch64" in machine:
            platform_id = "mac-arm64"
        else:
            platform_id = "mac-x64"
    elif system == "Linux":
        platform_id = "linux64"
    else:
        raise OSError(f"Unsupported platform: {system}")
    
    # Get latest stable version info from Chrome for Testing API
    api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
    
    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read().decode())
        
        # Get chrome download URL for our platform
        chrome_downloads = data['channels']['Stable']['downloads']['chrome']
        
        for download in chrome_downloads:
            if download['platform'] == platform_id:
                return download['url'], platform_id
        
        raise ValueError(f"No download found for platform: {platform_id}")
    
    except Exception as e:
        raise RuntimeError(f"Failed to get Chrome for Testing download URL: {e}") from e


def download_file(url: str, dest_path: Path, progress_callback=None) -> None:
    """
    Download a file from URL to destination path with optional progress callback.
    
    Args:
        url: URL to download from
        dest_path: Path to save the file to
        progress_callback: Optional callback function(downloaded, total)
    """
    logger.debug("Downloading from: %s", url)
    
    with urllib.request.urlopen(url) as response:
        content_length = response.headers.get('content-length', '0')
        total_size = int(content_length) if content_length else 0
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                
                if progress_callback:
                    progress_callback(downloaded, total_size)
                elif total_size > 0:
                    percent = (downloaded / total_size) * 100
                    logger.debug("Download progress: %.1f%%", percent)
        
        logger.debug("Download complete")


def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """
    Extract a zip archive to the specified directory.
    
    Args:
        archive_path: Path to the zip file
        extract_to: Directory to extract to
    """
    logger.debug("Extracting %s to: %s", archive_path, extract_to)
    
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    logger.debug("Extraction complete")


def get_chromium_executable_path(install_dir: Path, platform_id: str) -> Path:
    """
    Get the path to the Chromium executable based on the platform.
    
    Args:
        install_dir: Directory where Chromium was extracted
        platform_id: Platform identifier (win64, mac-x64, linux64, etc.)
        
    Returns:
        Path to the Chromium executable
    """
    system = platform.system()
    
    if system == "Windows":
        # Chrome for Testing structure: chrome-win64/chrome.exe or chrome-win32/chrome.exe
        chrome_dir = install_dir / f"chrome-{platform_id}"
        if not chrome_dir.exists():
            # Fallback to other possible names
            for possible_dir in install_dir.glob("chrome-win*"):
                chrome_dir = possible_dir
                break
        
        executable = chrome_dir / "chrome.exe"
    
    elif system == "Darwin":  # macOS
        # Chrome for Testing structure: chrome-mac-*/Google Chrome for Testing.app
        chrome_dir = install_dir / f"chrome-{platform_id}"
        if not chrome_dir.exists():
            for possible_dir in install_dir.glob("chrome-mac*"):
                chrome_dir = possible_dir
                break
        
        executable = chrome_dir / "Google Chrome for Testing.app" / "Contents" / "MacOS" / "Google Chrome for Testing"
    
    elif system == "Linux":
        # Chrome for Testing structure: chrome-linux64/chrome
        chrome_dir = install_dir / f"chrome-{platform_id}"
        if not chrome_dir.exists():
            for possible_dir in install_dir.glob("chrome-linux*"):
                chrome_dir = possible_dir
                break
        
        executable = chrome_dir / "chrome"
    
    else:
        raise OSError(f"Unsupported platform: {system}")
    
    if not executable.exists():
        raise FileNotFoundError(f"Chrome executable not found at: {executable}")
    
    # Make executable on Unix systems
    if system in ["Darwin", "Linux"]:
        os.chmod(executable, 0o755)
    
    return executable


def find_existing_chromium(install_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Check if Chromium is already installed at the specified location.
    
    Args:
        install_dir: Optional installation directory to check. If None, uses default temp directory.
        
    Returns:
        Path to the Chromium executable if found, None otherwise
    """
    if install_dir is None:
        install_dir = Path(tempfile.gettempdir()) / "chromium_install"
    else:
        install_dir = Path(install_dir)
    
    if not install_dir.exists():
        return None
    
    try:
        # Try to detect platform and find executable
        system = platform.system()
        
        # Look for common Chrome directory patterns
        if system == "Windows":
            for chrome_dir in install_dir.glob("chrome-win*"):
                exe_path = chrome_dir / "chrome.exe"
                if exe_path.exists():
                    return exe_path
        
        elif system == "Darwin":  # macOS
            for chrome_dir in install_dir.glob("chrome-mac*"):
                exe_path = chrome_dir / "Google Chrome for Testing.app" / "Contents" / "MacOS" / "Google Chrome for Testing"
                if exe_path.exists():
                    return exe_path
        
        elif system == "Linux":
            for chrome_dir in install_dir.glob("chrome-linux*"):
                exe_path = chrome_dir / "chrome"
                if exe_path.exists():
                    return exe_path
        
        return None
    
    except Exception:
        return None


def install_chromium(install_dir: Optional[Path] = None, clean_existing: bool = True, force_reinstall: bool = False) -> Path:
    """
    Download and install Chromium to a temporary folder.
    
    Args:
        install_dir: Optional custom installation directory. If None, uses system temp directory.
        clean_existing: If True, removes existing installation in the directory.
        force_reinstall: If True, always download even if Chromium is already installed.
        
    Returns:
        Path to the Chromium executable
    """
    # Create or use provided installation directory
    if install_dir is None:
        temp_base = Path(tempfile.gettempdir()) / "chromium_install"
    else:
        temp_base = Path(install_dir)
    
    # Check if Chromium is already installed (unless force_reinstall is True)
    if not force_reinstall:
        existing_chrome = find_existing_chromium(temp_base)
        if existing_chrome:
            logger.info("Using existing Chromium installation at: %s", existing_chrome)
            return existing_chrome
    
    # Clean existing installation if requested
    if clean_existing and temp_base.exists():
        logger.debug("Removing existing installation at: %s", temp_base)
        shutil.rmtree(temp_base, ignore_errors=True)
    
    # Create installation directory
    temp_base.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get download URL
        download_url, platform_id = get_chrome_for_testing_url()
        
        # Download archive
        archive_path = temp_base / "chrome.zip"
        download_file(download_url, archive_path)
        
        # Extract archive
        extract_archive(archive_path, temp_base)
        
        # Remove archive to save space
        if archive_path.exists():
            archive_path.unlink()
        
        # Get executable path
        executable_path = get_chromium_executable_path(temp_base, platform_id)
        
        logger.info("Chrome for Testing installed successfully at: %s", executable_path)
        logger.debug("Installation directory: %s", temp_base)
        
        return executable_path
    
    except Exception as e:
        # Clean up on failure
        if temp_base.exists():
            shutil.rmtree(temp_base, ignore_errors=True)
        raise RuntimeError(f"Failed to install Chrome for Testing: {e}") from e


def main():
    """Main function for testing the installer."""
    # Configure logging for the test
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    try:
        chromium_path = install_chromium()
        print(f"\nChrome executable: {chromium_path}")
        print(f"Exists: {chromium_path.exists()}")
        return 0
    except (OSError, RuntimeError, ValueError) as e:
        logger.error("Installation failed: %s", e)
        return 1


if __name__ == "__main__":
    exit(main())
