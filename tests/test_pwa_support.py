"""
Tests for the PWA support checker module.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
import urllib.error

from pwa_launcher.pwa_support import (
    normalize_url,
    is_https,
    find_manifest_url,
    check_service_worker,
    validate_manifest,
    check_pwa_support,
    PWACheckResult,
)


class TestNormalizeUrl:
    """Tests for normalize_url function."""
    
    def test_adds_https_to_bare_domain(self):
        """Test that HTTPS is added to bare domain."""
        assert normalize_url("example.com") == "https://example.com"
    
    def test_adds_https_to_localhost(self):
        """Test that HTTPS is added to localhost."""
        assert normalize_url("localhost:5000") == "https://localhost:5000"
    
    def test_preserves_https(self):
        """Test that existing HTTPS is preserved."""
        assert normalize_url("https://example.com") == "https://example.com"
    
    def test_preserves_http(self):
        """Test that existing HTTP is preserved."""
        assert normalize_url("http://localhost:5000") == "http://localhost:5000"
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        assert normalize_url("  example.com  ") == "https://example.com"


class TestIsHttps:
    """Tests for is_https function."""
    
    def test_https_url(self):
        """Test HTTPS URL detection."""
        assert is_https("https://example.com") is True
    
    def test_http_url(self):
        """Test HTTP URL detection."""
        assert is_https("http://example.com") is False
    
    def test_localhost_http(self):
        """Test localhost HTTP."""
        assert is_https("http://localhost:5000") is False


class TestFindManifestUrl:
    """Tests for find_manifest_url function."""
    
    def test_finds_manifest_rel_first(self):
        """Test finding manifest with rel before href."""
        html = '<link rel="manifest" href="/manifest.json">'
        result = find_manifest_url(html, "https://example.com")
        assert result == "https://example.com/manifest.json"
    
    def test_finds_manifest_href_first(self):
        """Test finding manifest with href before rel."""
        html = '<link href="/manifest.json" rel="manifest">'
        result = find_manifest_url(html, "https://example.com")
        assert result == "https://example.com/manifest.json"
    
    def test_finds_manifest_absolute_url(self):
        """Test finding manifest with absolute URL."""
        html = '<link rel="manifest" href="https://cdn.example.com/manifest.json">'
        result = find_manifest_url(html, "https://example.com")
        assert result == "https://cdn.example.com/manifest.json"
    
    def test_finds_manifest_case_insensitive(self):
        """Test case-insensitive matching."""
        html = '<LINK REL="MANIFEST" HREF="/manifest.json">'
        result = find_manifest_url(html, "https://example.com")
        assert result == "https://example.com/manifest.json"
    
    def test_no_manifest_found(self):
        """Test when no manifest is present."""
        html = '<html><head><title>Test</title></head></html>'
        result = find_manifest_url(html, "https://example.com")
        assert result is None
    
    def test_relative_path_resolution(self):
        """Test relative path resolution."""
        html = '<link rel="manifest" href="./static/manifest.json">'
        result = find_manifest_url(html, "https://example.com/app/")
        assert result == "https://example.com/app/static/manifest.json"


class TestCheckServiceWorker:
    """Tests for check_service_worker function."""
    
    def test_finds_sw_registration(self):
        """Test finding service worker registration."""
        html = '<script>navigator.serviceWorker.register("/sw.js")</script>'
        has_sw, sw_url = check_service_worker(html, "https://example.com")
        assert has_sw is True
        assert sw_url == "https://example.com/sw.js"
    
    def test_finds_sw_short_syntax(self):
        """Test finding service worker with short syntax."""
        html = '<script>serviceWorker.register("/service-worker.js")</script>'
        has_sw, sw_url = check_service_worker(html, "https://example.com")
        assert has_sw is True
        assert sw_url == "https://example.com/service-worker.js"
    
    def test_finds_sw_single_quotes(self):
        """Test finding service worker with single quotes."""
        html = "<script>navigator.serviceWorker.register('/sw.js')</script>"
        has_sw, sw_url = check_service_worker(html, "https://example.com")
        assert has_sw is True
        assert sw_url == "https://example.com/sw.js"
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_finds_common_sw_path(self, mock_fetch):
        """Test finding service worker at common path."""
        html = '<script>// no explicit registration</script>'
        mock_fetch.return_value = ("// service worker code", {})
        
        has_sw, sw_url = check_service_worker(html, "https://example.com")
        assert has_sw is True
        assert sw_url == "https://example.com/sw.js"
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_no_sw_found(self, mock_fetch):
        """Test when no service worker is found."""
        html = '<script>// no service worker</script>'
        mock_fetch.side_effect = urllib.error.HTTPError(None, 404, "Not Found", {}, None)
        
        has_sw, sw_url = check_service_worker(html, "https://example.com")
        assert has_sw is False
        assert sw_url is None


class TestValidateManifest:
    """Tests for validate_manifest function."""
    
    def test_valid_manifest_no_warnings(self):
        """Test valid manifest returns no warnings."""
        manifest = {
            "name": "Test App",
            "short_name": "Test",
            "start_url": "/",
            "display": "standalone",
            "icons": [
                {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ]
        }
        warnings = validate_manifest(manifest)
        assert len(warnings) == 0
    
    def test_missing_name_warning(self):
        """Test warning for missing name."""
        manifest = {"start_url": "/"}
        warnings = validate_manifest(manifest)
        assert any("name" in w.lower() for w in warnings)
    
    def test_missing_start_url_warning(self):
        """Test warning for missing start_url."""
        manifest = {"name": "Test"}
        warnings = validate_manifest(manifest)
        assert any("start_url" in w.lower() for w in warnings)
    
    def test_missing_display_warning(self):
        """Test warning for missing display."""
        manifest = {"name": "Test", "start_url": "/"}
        warnings = validate_manifest(manifest)
        assert any("display" in w.lower() for w in warnings)
    
    def test_missing_icons_warning(self):
        """Test warning for missing icons."""
        manifest = {"name": "Test", "start_url": "/", "display": "standalone"}
        warnings = validate_manifest(manifest)
        assert any("icons" in w.lower() for w in warnings)
    
    def test_missing_icon_sizes_warning(self):
        """Test warning for missing icon sizes."""
        manifest = {
            "name": "Test",
            "start_url": "/",
            "display": "standalone",
            "icons": [{"src": "/icon.png", "sizes": "96x96"}]
        }
        warnings = validate_manifest(manifest)
        assert any("192x192" in w for w in warnings)
        assert any("512x512" in w for w in warnings)


class TestCheckPwaSupport:
    """Tests for check_pwa_support function."""
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_full_pwa_support(self, mock_fetch):
        """Test URL with full PWA support."""
        html = '''
        <html>
        <head>
            <link rel="manifest" href="/manifest.json">
        </head>
        <body>
            <script>navigator.serviceWorker.register('/sw.js')</script>
        </body>
        </html>
        '''
        
        manifest = {
            "name": "Test PWA",
            "short_name": "Test",
            "start_url": "/",
            "display": "standalone",
            "icons": [
                {"src": "/icon-192.png", "sizes": "192x192"},
                {"src": "/icon-512.png", "sizes": "512x512"},
            ]
        }
        
        # First call returns HTML, second returns manifest
        mock_fetch.side_effect = [
            (html, {}),
            (json.dumps(manifest), {})
        ]
        
        result = check_pwa_support("https://example.com")
        
        assert result.is_pwa_supported is True
        assert result.has_https is True
        assert result.has_manifest is True
        assert result.has_service_worker is True
        assert result.manifest_url == "https://example.com/manifest.json"
        assert result.service_worker_url == "https://example.com/sw.js"
        assert len(result.errors) == 0
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_localhost_http_allowed(self, mock_fetch):
        """Test that HTTP is allowed for localhost."""
        html = '''
        <link rel="manifest" href="/manifest.json">
        <script>navigator.serviceWorker.register('/sw.js')</script>
        '''
        
        manifest = {"name": "Test", "start_url": "/", "display": "standalone"}
        
        mock_fetch.side_effect = [
            (html, {}),
            (json.dumps(manifest), {})
        ]
        
        result = check_pwa_support("http://localhost:5000")
        
        assert result.is_pwa_supported is True
        assert result.has_https is False  # HTTP
        assert len([w for w in result.warnings if "HTTPS" in w]) == 0  # No HTTPS warning for localhost
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_no_manifest(self, mock_fetch):
        """Test URL without manifest."""
        html = '<html><head><title>No PWA</title></head></html>'
        mock_fetch.return_value = (html, {})
        
        result = check_pwa_support("https://example.com")
        
        assert result.is_pwa_supported is False
        assert result.has_manifest is False
        assert any("manifest" in e.lower() for e in result.errors)
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_no_service_worker(self, mock_fetch):
        """Test URL without service worker."""
        html = '<link rel="manifest" href="/manifest.json">'
        manifest = {"name": "Test"}
        
        mock_fetch.side_effect = [
            (html, {}),
            (json.dumps(manifest), {}),
            urllib.error.HTTPError(None, 404, "Not Found", {}, None),
            urllib.error.HTTPError(None, 404, "Not Found", {}, None),
            urllib.error.HTTPError(None, 404, "Not Found", {}, None),
        ]
        
        result = check_pwa_support("https://example.com")
        
        assert result.is_pwa_supported is False
        assert result.has_service_worker is False
        assert any("service worker" in e.lower() for e in result.errors)
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_http_error(self, mock_fetch):
        """Test handling of HTTP errors."""
        mock_fetch.side_effect = urllib.error.HTTPError(
            None, 404, "Not Found", {}, None
        )
        
        result = check_pwa_support("https://example.com")
        
        assert result.is_pwa_supported is False
        assert len(result.errors) > 0
        assert any("404" in e for e in result.errors)
    
    @patch('pwa_launcher.pwa_support.fetch_url')
    def test_url_error(self, mock_fetch):
        """Test handling of URL errors."""
        mock_fetch.side_effect = urllib.error.URLError("Connection refused")
        
        result = check_pwa_support("https://example.com")
        
        assert result.is_pwa_supported is False
        assert len(result.errors) > 0
    
    def test_adds_https_to_bare_url(self):
        """Test that HTTPS is added to bare URLs."""
        with patch('pwa_launcher.pwa_support.fetch_url') as mock_fetch:
            mock_fetch.side_effect = urllib.error.URLError("test")
            result = check_pwa_support("example.com")
            assert result.url == "https://example.com"


class TestPWACheckResult:
    """Tests for PWACheckResult dataclass."""
    
    def test_str_representation_full_pwa(self):
        """Test string representation for full PWA."""
        result = PWACheckResult(
            url="https://example.com",
            is_pwa_supported=True,
            has_manifest=True,
            manifest_url="https://example.com/manifest.json",
            manifest_data={"name": "Test App", "short_name": "Test"},
            has_service_worker=True,
            service_worker_url="https://example.com/sw.js",
            has_https=True,
        )
        
        str_repr = str(result)
        assert "PWA Supported" in str_repr
        assert "https://example.com" in str_repr
        assert "Test App" in str_repr
    
    def test_str_representation_not_pwa(self):
        """Test string representation for non-PWA."""
        result = PWACheckResult(
            url="https://example.com",
            is_pwa_supported=False,
            has_manifest=False,
            has_service_worker=False,
            has_https=True,
            errors=["No manifest found"],
        )
        
        str_repr = str(result)
        assert "Not PWA Supported" in str_repr
        assert "No manifest found" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
