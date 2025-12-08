# py-pwa-launcher
Launch Progressive Web Apps from Python

A Python library for launching Progressive Web Apps (PWAs) using Chromium-based browsers. Automatically finds or downloads a Chromium browser and launches PWAs in app mode with all necessary flags.

## Features

- 🚀 **Launch PWAs with a single function call**
- 🔍 **Auto-detect** system Chrome/Edge browsers
- 📥 **Auto-download** portable Chromium if needed
- ⚙️ **PWA-optimized flags** for installation and features
- 🔒 **Custom profiles** for isolated PWA data
- ✅ **Check PWA support** before launching
- 🧪 **Fully tested** with comprehensive test suite

## Installation

```bash
pip install py-pwa-launcher
```

## Quick Start

### Launch a PWA

```python
from pwa_launcher import open_pwa

# Launch a PWA - that's it!
open_pwa("https://weatherlite.app")
```

### Check PWA Support

```python
from pwa_launcher import check_pwa_support

# Check if a URL supports PWA
result = check_pwa_support("https://weatherlite.app")

if result.is_pwa_supported:
    print(f"✓ {result.url} is PWA-ready!")
    print(f"  Manifest: {result.manifest_url}")
    print(f"  Service Worker: {result.service_worker_url}")
else:
    print(f"✗ Not a PWA")
    for error in result.errors:
        print(f"  - {error}")
```

### Launch with Custom Options

```python
from pwa_launcher import open_pwa
from pathlib import Path

# Launch with custom profile and flags
process = open_pwa(
    "https://excalidraw.com",
    user_data_dir=Path("./my_pwa_profile"),
    additional_flags=["--start-maximized"]
)

print(f"Launched PWA (PID: {process.pid})")
```

## API Reference

### `open_pwa(url, **kwargs)`

Launch a PWA using Chromium browser.

**Parameters:**
- `url` (str): URL to open as PWA (required)
- `chromium_path` (Path, optional): Path to Chromium executable
- `allow_system` (bool, default=True): Allow using system Chrome/Edge
- `allow_download` (bool, default=True): Allow downloading portable Chromium
- `install_dir` (Path, optional): Directory for portable Chromium
- `user_data_dir` (Path, optional): Custom browser profile directory
- `additional_flags` (List[str], optional): Extra Chromium flags
- `wait` (bool, default=False): Wait for browser to exit

**Returns:** `subprocess.Popen` - Browser process

**Raises:**
- `ChromiumNotFoundError`: No browser found
- `ValueError`: Invalid URL

### `check_pwa_support(url, timeout=10)`

Check if a URL supports PWA features.

**Parameters:**
- `url` (str): URL to check
- `timeout` (int): Request timeout in seconds

**Returns:** `PWACheckResult` with:
- `is_pwa_supported` (bool): Whether PWA is supported
- `has_manifest` (bool): Has web manifest
- `manifest_url` (str): URL of manifest file
- `manifest_data` (dict): Parsed manifest data
- `has_service_worker` (bool): Has service worker
- `service_worker_url` (str): URL of service worker
- `has_https` (bool): Uses HTTPS
- `errors` (list): List of error messages
- `warnings` (list): List of warnings

### `get_chromium_install(**options)`

Get a single Chromium browser executable path (tries system → portable → download).

**Parameters:**
- `allow_system` (bool, default=True): Search for system Chrome/Edge
- `allow_download` (bool, default=True): Allow downloading portable Chrome
- `install_dir` (Path, optional): Directory for portable Chrome
- `force_reinstall` (bool, default=False): Force download even if exists

**Returns:** `Path` - Path to Chromium executable

**Raises:** `ChromiumNotFoundError` - No browser found

### `get_chromium_installs(**options)`

Get all available Chromium browser executable paths.

**Parameters:**
- `allow_system` (bool, default=True): Search for system Chrome/Edge
- `allow_download` (bool, default=True): Allow downloading portable Chrome
- `install_dir` (Path, optional): Directory for portable Chrome

**Returns:** `List[Path]` - List of paths to Chromium executables

## Examples

See the `examples/` directory for more examples:

- `examples/check_pwa.py` - Check PWA support

## Command Line Usage

### Launch a PWA

```bash
python -m pwa_launcher.open_pwa https://weatherlite.app
```

### Check PWA Support

```bash
python -m pwa_launcher.pwa_support https://weatherlite.app
```

## How It Works

1. **Get Chromium**: Finds system Chrome/Edge or downloads portable Chromium
2. **Build Command**: Creates command with `--app={url}` and PWA flags
3. **Launch**: Starts browser in app mode with PWA features enabled

### PWA Flags Included

- `--app={url}`: Launch in app mode (no browser UI)
- `--enable-features=WebAppInstallation`: Enable PWA installation
- `--enable-features=DesktopPWAsTabStrip`: Enable tab strip in PWAs
- `--enable-features=FileSystemAccessAPI`: Enable file system access
- `--enable-features=NotificationTriggers`: Enable notifications
- `--no-default-browser-check`: Skip default browser check
- `--no-first-run`: Skip first run experience

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/py-pwa-launcher.git
cd py-pwa-launcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pwa_launcher

# Run specific test file
pytest tests/test_open_pwa.py -v
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
