"""
Tests for the get_chromium module.
"""
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
    def test_finds_system_chrome(self, mock_find_system, tmp_path):
        """Test that system Chrome is found and returned."""
        system_chrome = tmp_path / "chrome.exe"
        mock_find_system.return_value = system_chrome

        result = get_chromium_install()

        assert result == system_chrome
        mock_find_system.assert_called_once()

    @patch('pwa_launcher.get_chromium.find_system_chromium')
    def test_raises_error_when_not_found(self, mock_find_system):
        """Test that ChromiumNotFoundError is raised when no browser found."""
        mock_find_system.side_effect = FileNotFoundError()

        with pytest.raises(ChromiumNotFoundError):
            get_chromium_install()


class TestGetChromiumInstalls:
    """Tests for get_chromium_installs function."""

    @patch('pwa_launcher.get_chromium.find_system_chromiums')
    def test_returns_all_found_browsers(self, mock_find_chromiums, tmp_path):
        """Test that all system browsers are returned."""
        browsers = [
            tmp_path / "chrome.exe",
            tmp_path / "edge.exe",
        ]
        mock_find_chromiums.return_value = browsers

        result = get_chromium_installs()

        assert result == browsers
        mock_find_chromiums.assert_called_once()

    @patch('pwa_launcher.get_chromium.find_system_chromiums')
    def test_returns_empty_when_none_found(self, mock_find_chromiums):
        """Test that empty list is returned when no browsers found."""
        mock_find_chromiums.return_value = []

        result = get_chromium_installs()

        assert result == []
        mock_find_chromiums.assert_called_once()


class TestChromiumNotFoundError:
    """Tests for ChromiumNotFoundError exception."""

    def test_is_exception(self):
        """Test that ChromiumNotFoundError is an Exception."""
        assert issubclass(ChromiumNotFoundError, Exception)

    def test_can_be_raised_and_caught(self):
        """Test that ChromiumNotFoundError can be raised and caught."""
        with pytest.raises(ChromiumNotFoundError) as exc_info:
            raise ChromiumNotFoundError("Test error")

        assert "Test error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
