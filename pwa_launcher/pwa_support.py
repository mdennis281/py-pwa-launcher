"""
PWA Support Checker - Validates if a URL supports Progressive Web App features.
"""
import json
import logging
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse


logger = logging.getLogger(__name__)


@dataclass
class PWACheckResult:
    """Result of PWA support check."""
    url: str
    is_pwa_supported: bool
    has_manifest: bool
    manifest_url: Optional[str] = None
    manifest_data: Optional[Dict[str, Any]] = None
    has_service_worker: bool = False
    service_worker_url: Optional[str] = None
    has_https: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """String representation of check result."""
        status = "✓ PWA Supported" if self.is_pwa_supported else "✗ Not PWA Supported"
        parts = [
            f"PWA Check Results for: {self.url}",
            f"Status: {status}",
            f"",
            f"Requirements:",
            f"  HTTPS: {'✓' if self.has_https else '✗'}",
            f"  Web Manifest: {'✓' if self.has_manifest else '✗'}",
            f"  Service Worker: {'✓' if self.has_service_worker else '✗'}",
        ]
        
        if self.manifest_url:
            parts.append(f"\nManifest URL: {self.manifest_url}")
        
        if self.manifest_data:
            parts.append(f"App Name: {self.manifest_data.get('name', 'N/A')}")
            parts.append(f"Short Name: {self.manifest_data.get('short_name', 'N/A')}")
        
        if self.service_worker_url:
            parts.append(f"\nService Worker URL: {self.service_worker_url}")
        
        if self.errors:
            parts.append(f"\nErrors:")
            for error in self.errors:
                parts.append(f"  - {error}")
        
        if self.warnings:
            parts.append(f"\nWarnings:")
            for warning in self.warnings:
                parts.append(f"  - {warning}")
        
        return "\n".join(parts)


def normalize_url(url: str) -> str:
    """
    Normalize URL to ensure it has a scheme.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL with scheme
    """
    url = url.strip()
    
    # Add https:// if no scheme
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    return url


def is_https(url: str) -> bool:
    """
    Check if URL uses HTTPS.
    
    Args:
        url: URL to check
        
    Returns:
        True if HTTPS, False otherwise
    """
    return urlparse(url).scheme == 'https'


def fetch_url(url: str, timeout: int = 10) -> tuple[str, Dict[str, str]]:
    """
    Fetch content from URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (content, headers)
        
    Raises:
        urllib.error.URLError: If request fails
    """
    logger.debug("Fetching URL: %s", url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    request = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read().decode('utf-8', errors='ignore')
        response_headers = dict(response.headers)
        
    return content, response_headers


def find_manifest_url(html_content: str, base_url: str) -> Optional[str]:
    """
    Find web manifest URL from HTML content.
    
    Args:
        html_content: HTML content to search
        base_url: Base URL for resolving relative paths
        
    Returns:
        Absolute manifest URL if found, None otherwise
    """
    logger.debug("Searching for manifest in HTML")
    
    # Look for <link rel="manifest" href="...">
    manifest_pattern = r'<link[^>]*rel=["\']manifest["\'][^>]*href=["\']([^"\']+)["\'][^>]*>'
    match = re.search(manifest_pattern, html_content, re.IGNORECASE)
    
    if not match:
        # Try alternate order: href before rel
        manifest_pattern = r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']manifest["\'][^>]*>'
        match = re.search(manifest_pattern, html_content, re.IGNORECASE)
    
    if match:
        manifest_href = match.group(1)
        manifest_url = urljoin(base_url, manifest_href)
        logger.info("Found manifest URL: %s", manifest_url)
        return manifest_url
    
    logger.debug("No manifest found in HTML")
    return None


def fetch_manifest(manifest_url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and parse web manifest JSON.
    
    Args:
        manifest_url: URL of the manifest file
        
    Returns:
        Parsed manifest data or None if failed
    """
    try:
        content, _ = fetch_url(manifest_url)
        manifest_data = json.loads(content)
        logger.info("Successfully parsed manifest")
        return manifest_data
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse manifest JSON: %s", e)
        return None
    except Exception as e:
        logger.warning("Failed to fetch manifest: %s", e)
        return None


def check_service_worker(html_content: str, base_url: str) -> tuple[bool, Optional[str]]:
    """
    Check if HTML registers a service worker.
    
    Searches for service worker registration in:
    1. Inline scripts in HTML
    2. External JavaScript files linked in HTML
    3. Common service worker file locations
    
    Args:
        html_content: HTML content to search
        base_url: Base URL for resolving relative paths
        
    Returns:
        Tuple of (has_service_worker, service_worker_url)
    """
    logger.debug("Checking for service worker registration")
    
    # Pattern to find service worker registration
    sw_register_pattern = r'(?:navigator\.)?serviceWorker\.register\s*\(\s*["\']([^"\']+)["\']'
    
    # 1. Check inline scripts in HTML
    inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
    for script_content in inline_scripts:
        match = re.search(sw_register_pattern, script_content, re.IGNORECASE)
        if match:
            sw_path = match.group(1)
            sw_url = urljoin(base_url, sw_path)
            logger.info("Found service worker registration in inline script: %s", sw_url)
            return True, sw_url
    
    # 2. Check external JavaScript files
    # Find all script tags with src attribute
    external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
    
    for script_src in external_scripts:
        script_url = urljoin(base_url, script_src)
        logger.debug("Checking external script: %s", script_url)
        
        try:
            script_content, _ = fetch_url(script_url, timeout=5)
            match = re.search(sw_register_pattern, script_content, re.IGNORECASE)
            if match:
                sw_path = match.group(1)
                # Resolve relative to the script's URL
                sw_url = urljoin(script_url, sw_path)
                logger.info("Found service worker registration in external script %s: %s", script_url, sw_url)
                return True, sw_url
        except Exception as e:
            logger.debug("Failed to fetch external script %s: %s", script_url, e)
            continue
    
    # 3. Check common service worker filenames by trying to fetch them
    common_sw_paths = [
        '/sw.js',
        '/service-worker.js',
        '/serviceworker.js',
        '/serviceWorker.js',
        '/pwa-sw.js',
        '/firebase-messaging-sw.js',
    ]
    
    for sw_path in common_sw_paths:
        sw_url = urljoin(base_url, sw_path)
        try:
            # Try to fetch the file
            content, headers = fetch_url(sw_url, timeout=5)
            # Check if it looks like a service worker (contains common SW API calls)
            if any(keyword in content for keyword in ['self.addEventListener', 'caches.open', 'fetch(', 'ServiceWorkerGlobalScope']):
                logger.info("Found service worker at common path: %s", sw_url)
                return True, sw_url
        except Exception:
            continue
    
    logger.debug("No service worker found")
    return False, None


def validate_manifest(manifest_data: Dict[str, Any]) -> List[str]:
    """
    Validate manifest data and return list of issues.
    
    Args:
        manifest_data: Parsed manifest data
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    # Check required/recommended fields
    if 'name' not in manifest_data and 'short_name' not in manifest_data:
        warnings.append("Manifest missing both 'name' and 'short_name'")
    
    if 'start_url' not in manifest_data:
        warnings.append("Manifest missing 'start_url'")
    
    if 'display' not in manifest_data:
        warnings.append("Manifest missing 'display' property")
    
    if 'icons' not in manifest_data:
        warnings.append("Manifest missing 'icons'")
    elif isinstance(manifest_data['icons'], list):
        if not manifest_data['icons']:
            warnings.append("Manifest 'icons' array is empty")
        else:
            # Check for required icon sizes
            sizes = set()
            for icon in manifest_data['icons']:
                if 'sizes' in icon:
                    sizes.update(icon['sizes'].split())
            
            if '192x192' not in sizes:
                warnings.append("Manifest missing 192x192 icon")
            if '512x512' not in sizes:
                warnings.append("Manifest missing 512x512 icon")
    
    return warnings


def check_pwa_support(url: str, timeout: int = 10) -> PWACheckResult:
    """
    Check if a URL supports PWA features.
    
    Checks for:
    - HTTPS (required for service workers)
    - Web manifest file
    - Service worker registration
    
    Args:
        url: URL to check (e.g., 'https://example.com' or 'localhost:5000')
        timeout: Request timeout in seconds
        
    Returns:
        PWACheckResult with detailed check results
    """
    logger.info("Checking PWA support for: %s", url)
    
    # Normalize URL
    url = normalize_url(url)
    
    result = PWACheckResult(
        url=url,
        is_pwa_supported=False,
        has_manifest=False,
        has_service_worker=False,
        has_https=is_https(url)
    )
    
    # Check HTTPS (allow http for localhost)
    parsed = urlparse(url)
    is_localhost = parsed.hostname in ('localhost', '127.0.0.1', '::1')
    
    if not result.has_https and not is_localhost:
        result.warnings.append("HTTPS is required for PWA (except localhost)")
    
    # Fetch the page
    try:
        html_content, headers = fetch_url(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP error {e.code}: {e.reason}"
        logger.error("Failed to fetch URL: %s", error_msg)
        result.errors.append(error_msg)
        return result
    except urllib.error.URLError as e:
        error_msg = f"URL error: {e.reason}"
        logger.error("Failed to fetch URL: %s", error_msg)
        result.errors.append(error_msg)
        return result
    except Exception as e:
        error_msg = f"Failed to fetch URL: {e}"
        logger.error("Unexpected error: %s", error_msg)
        result.errors.append(error_msg)
        return result
    
    # Check for manifest
    manifest_url = find_manifest_url(html_content, url)
    if manifest_url:
        result.has_manifest = True
        result.manifest_url = manifest_url
        
        # Fetch and parse manifest
        manifest_data = fetch_manifest(manifest_url)
        if manifest_data:
            result.manifest_data = manifest_data
            
            # Validate manifest
            validation_warnings = validate_manifest(manifest_data)
            result.warnings.extend(validation_warnings)
        else:
            result.errors.append("Failed to parse manifest file")
    else:
        result.errors.append("No web manifest found")
    
    # Check for service worker
    has_sw, sw_url = check_service_worker(html_content, url)
    result.has_service_worker = has_sw
    result.service_worker_url = sw_url
    
    if not has_sw:
        result.errors.append("No service worker registration found")
    
    # Determine if PWA is supported
    # Minimum requirements: manifest + service worker
    # HTTPS is required for production but allow localhost for development
    result.is_pwa_supported = (
        result.has_manifest and 
        result.has_service_worker and
        (result.has_https or is_localhost)
    )
    
    logger.info("PWA check complete. Supported: %s", result.is_pwa_supported)
    
    return result


if __name__ == "__main__":
    """Test the PWA checker."""
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Get URL from command line or use default
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://weatherlite.com"
    
    print(f"Checking PWA support for: {test_url}\n")
    
    result = check_pwa_support(test_url)
    print(result)
