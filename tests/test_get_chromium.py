"""
Tests for the get_chromium module's main entry point.
"""
from pathlib import Path
from unittest.mock import patch
import pytest

from pwa_launcher.get_chromium import (
    get_chromium_install,
    get_chromium_installs,
    ChromiumNotFoundError,
)


class TestGetChromiumInstall:
    """Tests for get_chromium_install function."""
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    def test_default_uses_system_chrome(self, mock_find_system, tmp_path):
        """Test that system Chrome is used by default when available."""
        system_chrome = tmp_path / "chrome.exe"
        mock_find_system.return_value = system_chrome
        
        result = get_chromium_install()
        
        assert result == system_chrome
        mock_find_system.assert_called_once()
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    def test_fallback_to_existing_portable(self, mock_find_existing, mock_find_system, tmp_path):
        """Test fallback to existing portable Chrome when no system browser."""
        mock_find_system.side_effect = FileNotFoundError()
        portable_chrome = tmp_path / "portable" / "chrome.exe"
        mock_find_existing.return_value = portable_chrome
        
        result = get_chromium_install()
        
        assert result == portable_chrome
        mock_find_system.assert_called_once()
        mock_find_existing.assert_called_once()
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium')
    def test_downloads_when_nothing_found(
        self, mock_install, mock_find_existing, mock_find_system, tmp_path
    ):
        """Test downloading when no system or existing portable Chrome found."""
        mock_find_system.side_effect = FileNotFoundError()
        mock_find_existing.return_value = None
        downloaded_chrome = tmp_path / "downloaded" / "chrome.exe"
        mock_install.return_value = downloaded_chrome
        
        result = get_chromium_install()
        
        assert result == downloaded_chrome
        mock_find_system.assert_called_once()
        mock_find_existing.assert_called_once()
        mock_install.assert_called_once_with(
            install_dir=None,
            clean_existing=False,
            force_reinstall=False
        )
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium')
    def test_allow_system_false_skips_system(
        self, mock_install, mock_find_existing, mock_find_system, tmp_path
    ):
        """Test that allow_system=False skips system browser search."""
        mock_find_existing.return_value = None
        downloaded_chrome = tmp_path / "chrome.exe"
        mock_install.return_value = downloaded_chrome
        
        result = get_chromium_install(allow_system=False)
        
        assert result == downloaded_chrome
        mock_find_system.assert_not_called()
        mock_find_existing.assert_called_once()
        mock_install.assert_called_once()
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    def test_allow_download_false_raises_when_no_system(self, mock_find_system):
        """Test that allow_download=False raises error when no system browser."""
        mock_find_system.side_effect = FileNotFoundError()
        
        with pytest.raises(ChromiumNotFoundError, match="No Chromium browser found"):
            get_chromium_install(allow_download=False)
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    def test_allow_download_false_uses_system(self, mock_find_system, tmp_path):
        """Test that allow_download=False works when system browser exists."""
        system_chrome = tmp_path / "chrome.exe"
        mock_find_system.return_value = system_chrome
        
        result = get_chromium_install(allow_download=False)
        
        assert result == system_chrome
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium')
    def test_force_reinstall_skips_existing(
        self, mock_install, mock_find_existing, mock_find_system, tmp_path
    ):
        """Test that force_reinstall=True skips existing portable Chrome."""
        mock_find_system.side_effect = FileNotFoundError()
        downloaded_chrome = tmp_path / "chrome.exe"
        mock_install.return_value = downloaded_chrome
        
        get_chromium_install(force_reinstall=True)
        
        # Should not check for existing when force_reinstall=True
        mock_find_existing.assert_not_called()
        mock_install.assert_called_once_with(
            install_dir=None,
            clean_existing=False,
            force_reinstall=True
        )
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium')
    def test_custom_install_dir_passed_through(
        self, mock_install, mock_find_existing, mock_find_system, tmp_path
    ):
        """Test that custom install_dir is passed to install_chromium."""
        mock_find_system.side_effect = FileNotFoundError()
        mock_find_existing.return_value = None
        custom_dir = tmp_path / "custom"
        downloaded_chrome = custom_dir / "chrome.exe"
        mock_install.return_value = downloaded_chrome
        
        get_chromium_install(install_dir=custom_dir)
        
        mock_find_existing.assert_called_once_with(custom_dir)
        mock_install.assert_called_once_with(
            install_dir=custom_dir,
            clean_existing=False,
            force_reinstall=False
        )
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium')
    def test_download_failure_raises_chromium_not_found(
        self, mock_install, mock_find_existing, mock_find_system
    ):
        """Test that download failure raises ChromiumNotFoundError."""
        mock_find_system.side_effect = FileNotFoundError()
        mock_find_existing.return_value = None
        mock_install.side_effect = Exception("Network error")
        
        with pytest.raises(ChromiumNotFoundError, match="Failed to download Chromium"):
            get_chromium_install()
    
    def test_both_disallowed_raises_error(self):
        """Test that disallowing both system and download raises error."""
        with pytest.raises(ChromiumNotFoundError, match="No Chromium browser found"):
            get_chromium_install(allow_system=False, allow_download=False)
    
    @patch('pwa_launcher.get_chromium.find_system_chromium')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    def test_priority_system_over_portable(
        self, mock_find_existing, mock_find_system, tmp_path
    ):
        """Test that system browser is preferred over portable."""
        system_chrome = tmp_path / "system" / "chrome.exe"
        portable_chrome = tmp_path / "portable" / "chrome.exe"
        
        mock_find_system.return_value = system_chrome
        mock_find_existing.return_value = portable_chrome
        
        result = get_chromium_install()
        
        # Should return system and not even check for existing
        assert result == system_chrome
        mock_find_existing.assert_not_called()


class TestGetChromiumInstalls:
    """Tests for get_chromium_installs function."""
    
    @patch('pwa_launcher.get_chromium.find_system_chromiums')
    def test_returns_system_browsers(self, mock_find_systems, tmp_path):
        """Test that system browsers are returned."""
        chrome = tmp_path / "chrome.exe"
        edge = tmp_path / "msedge.exe"
        mock_find_systems.return_value = [chrome, edge]
        
        result = get_chromium_installs()
        
        assert result == [chrome, edge]
        mock_find_systems.assert_called_once()
    
    @patch('pwa_launcher.get_chromium.find_system_chromiums')
    @patch('pwa_launcher.get_chromium.find_existing_chromium')
    def test_includes_portable_when_requested(
        self, mock_find_existing, mock_find_systems, tmp_path
    ):
        """Test that portable Chrome is included when allow_download=True."""
        chrome = tmp_path / "chrome.exe"
        portable = tmp_path / "portable.exe"
        mock_find_systems.return_value = [chrome]
        mock_find_existing.return_value = portable
        
        result = get_chromium_installs(allow_download=True)
        
        assert result == [chrome, portable]
    
    @patch('pwa_launcher.get_chromium.find_system_chromiums')
    def test_allow_system_false_skips_system(self, mock_find_systems):
        """Test that allow_system=False skips system browsers."""
        result = get_chromium_installs(allow_system=False)
        
        assert result == []
        mock_find_systems.assert_not_called()
    
    @patch('pwa_launcher.get_chromium.find_system_chromiums')
    def test_returns_empty_when_none_found(self, mock_find_systems):
        """Test that empty list is returned when no browsers found."""
        mock_find_systems.return_value = []
        
        result = get_chromium_installs()
        
        assert result == []


class TestChromiumNotFoundError:
    """Tests for ChromiumNotFoundError exception."""
    
    def test_is_exception(self):
        """Test that ChromiumNotFoundError is an Exception."""
        assert issubclass(ChromiumNotFoundError, Exception)
    
    def test_can_be_raised_and_caught(self):
        """Test that ChromiumNotFoundError can be raised and caught."""
        with pytest.raises(ChromiumNotFoundError) as exc_info:
            raise ChromiumNotFoundError("Test message")
        
        assert "Test message" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
