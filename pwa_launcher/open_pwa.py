"""
Open PWA - Launch a Progressive Web App using Chromium.
"""
import hashlib
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

from pwa_launcher.get_chromium import get_chromium_install, ChromiumNotFoundError


logger = logging.getLogger(__name__)


def open_pwa(
    url: str,
    chromium_path: Optional[Path] = None,
    allow_system: bool = True,
    allow_download: bool = True,
    install_dir: Optional[Path] = None,
    user_data_dir: Optional[Path] = None,
    additional_flags: Optional[List[str]] = None,
    wait: bool = False,
    auto_profile: bool = True,
) -> subprocess.Popen:
    """
    Open a URL as a Progressive Web App using Chromium.
    
    Gets the Chromium binary and launches it with the --app flag plus
    flags to enable PWA installation and features.
    
    Args:
        url: URL to open as PWA
        chromium_path: Path to Chromium executable (auto-detected if None)
        allow_system: Allow using system Chrome/Edge
        allow_download: Allow downloading portable Chromium if needed
        install_dir: Directory for portable Chromium installation
        user_data_dir: Custom user data directory for browser profile
        additional_flags: Additional Chromium flags
        wait: Wait for the browser process to exit
        auto_profile: Auto-generate isolated profile for the PWA (keeps process alive)
        
    Returns:
        subprocess.Popen object representing the browser process
        
    Raises:
        ChromiumNotFoundError: No Chromium browser found
        ValueError: Invalid or empty URL
        
    Note:
        When auto_profile=True (default), each PWA gets its own isolated profile
        based on the URL hostname. This keeps the browser process alive and prevents
        Chrome from handing off to an existing instance. If you need a shared profile,
        set auto_profile=False or provide a custom user_data_dir.
    """
    # Validate URL
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Normalize URL - add https:// if no scheme
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    logger.debug("Launching PWA for URL: %s", url)
    
    # Get Chromium executable if not provided
    if chromium_path is None:
        logger.debug("Auto-detecting Chromium browser...")
        chromium_path = get_chromium_install(
            allow_system=allow_system,
            allow_download=allow_download,
            install_dir=install_dir,
        )
    
    logger.info("Using Chromium: %s", chromium_path)
    
    # Build command line arguments
    cmd = [str(chromium_path)]
    
    # Core PWA flags
    cmd.append(f'--app={url}')
    
    # Flags to enable PWA installation and features
    pwa_flags = [
        # Allow installation of web apps
        '--enable-features=WebAppInstallation',
        
        # Enable app mode features
        '--enable-features=DesktopPWAsTabStrip',
        '--enable-features=DesktopPWAsTabStripSettings',
        
        # Allow file system access for PWAs (some apps need this)
        '--enable-features=FileSystemAccessAPI',
        
        # Enable notifications (PWA feature)
        '--enable-features=NotificationTriggers',
        
        # Disable default browser check (prevents popup on launch)
        '--no-default-browser-check',
        
        # Disable first run experience
        '--no-first-run',
        
        # Disable automation/testing banners
        '--disable-infobars',
    ]
    
    cmd.extend(pwa_flags)
    
    # Auto-generate isolated profile if requested and user_data_dir not provided
    if auto_profile and user_data_dir is None:
        # Create a profile directory based on the URL hostname
        # This ensures each PWA runs in its own process
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.path.split('/')[0]
        
        # Use a hash to handle special characters and long hostnames
        hostname_hash = hashlib.md5(hostname.encode()).hexdigest()[:8]
        profile_name = f"pwa_{hostname.replace('.', '_')}_{hostname_hash}"
        
        temp_base = Path(tempfile.gettempdir()) / "py-pwa-launcher"
        user_data_dir = temp_base / profile_name
        
        logger.debug("Auto-generated profile directory for %s: %s", hostname, user_data_dir)
    
    # Add custom user data directory if provided or auto-generated
    if user_data_dir:
        user_data_dir = Path(user_data_dir)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        cmd.append(f'--user-data-dir={user_data_dir}')
        logger.debug("Using custom user data directory: %s", user_data_dir)
    
    # Add any additional flags
    if additional_flags:
        cmd.extend(additional_flags)
        logger.debug("Added additional flags: %s", additional_flags)
    
    # Log the full command
    logger.debug("Launch command: %s", ' '.join(cmd))
    
    # Launch the browser
    try:
        # On Linux/macOS, we need to allow the process to run independently
        import platform
        
        if platform.system() in ('Linux', 'Darwin'):
            # On Linux, temporarily capture stderr to check for dependency errors
            if platform.system() == 'Linux':
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                
                # Give it a moment to start
                import time
                time.sleep(0.5)
                poll_result = process.poll()
                
                if poll_result is not None:
                    # Process failed - read stderr to see why
                    stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
                    
                    logger.error("Chrome failed to start on Linux (exit code: %s)", poll_result)
                    if stderr_output:
                        logger.error("Chrome error output:\n%s", stderr_output)
                    
                    # Check for common dependency errors
                    if 'error while loading shared libraries' in stderr_output.lower():
                        logger.error("\n=== MISSING DEPENDENCIES ===")
                        logger.error("Chrome requires system libraries that are not installed.")
                        logger.error("Run this command to install them:")
                        logger.error("sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2")
                        raise RuntimeError(
                            "Chrome failed to start due to missing system libraries. "
                            "Install dependencies with: sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2"
                        )
                    else:
                        raise RuntimeError(f"Chrome failed to start on Linux (exit code: {poll_result}). Check logs for details.")
                
                # Process started successfully - now detach stderr
                # Close the pipe since we don't need it anymore
                process.stderr.close()
            else:
                # macOS - just detach completely
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
        else:
            # Windows - keep original behavior
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        
        logger.debug("Browser launched with PID: %s", process.pid)
        
        # Wait for process if requested
        if wait:
            logger.debug("Waiting for browser process to exit...")
            process.wait()
            logger.debug("Browser process exited with code: %s", process.returncode)
        
        return process
        
    except Exception as e:
        logger.error("Failed to launch browser: %s", e)
        raise


def main():
    """Main function for testing the PWA launcher."""
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://weatherlite.com"
        print(f"No URL provided, using default: {url}")
        print("Usage: python -m pwa_launcher.open_pwa <url>")
        print()
    
    try:
        print(f"Launching PWA: {url}")
        process = open_pwa(url, wait=False)
        print(f"✓ Browser launched (PID: {process.pid})")
        print("The PWA is now running in a separate window.")
        
    except ChromiumNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except ValueError as e:
        print(f"✗ Invalid URL: {e}")
        return 1
    except (OSError, subprocess.SubprocessError) as e:
        print(f"✗ Failed to launch: {e}")
        logger.exception("Unexpected error")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
