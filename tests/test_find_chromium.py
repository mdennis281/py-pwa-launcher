"""
Tests for the Chromium browser finder module.
"""
import os
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from pwa_launcher.get_chromium import (
    find_chrome,
    find_edge,
    find_system_chromium,
    get_chromium_info,
)


class TestFindChrome:
    """Tests for find_chrome function."""
    
    @patch('pwa_launcher.get_chromium.find_chromium.get_chrome_paths')
    def test_find_chrome_success(self, mock_get_paths, tmp_path):
        """Test finding Chrome when it exists."""
        chrome_exe = tmp_path / "chrome.exe"
        chrome_exe.touch()
        
        mock_get_paths.return_value = [chrome_exe]
        
        result = find_chrome()
        
        assert result == chrome_exe
    
    @patch('pwa_launcher.get_chromium.find_chromium.get_chrome_paths')
    def test_find_chrome_first_match(self, mock_get_paths, tmp_path):
        """Test that first existing path is returned."""
        chrome1 = tmp_path / "chrome1.exe"
        chrome2 = tmp_path / "chrome2.exe"
        chrome2.touch()  # Only second one exists
        
        mock_get_paths.return_value = [chrome1, chrome2]
        
        result = find_chrome()
        
        assert result == chrome2
    
    @patch('pwa_launcher.get_chromium.find_chromium.get_chrome_paths')
    def test_find_chrome_not_found(self, mock_get_paths, tmp_path):
        """Test when Chrome is not found."""
        chrome_exe = tmp_path / "chrome.exe"
        # Don't create the file
        
        mock_get_paths.return_value = [chrome_exe]
        
        result = find_chrome()
        
        assert result is None
    
    @patch('pwa_launcher.get_chromium.find_chromium.get_chrome_paths')
    def test_find_chrome_ignores_directories(self, mock_get_paths, tmp_path):
        """Test that directories are ignored."""
        chrome_dir = tmp_path / "chrome.exe"
        chrome_dir.mkdir()  # Create as directory, not file
        
        mock_get_paths.return_value = [chrome_dir]
        
        result = find_chrome()
        
        assert result is None


class TestFindEdge:
    """Tests for find_edge function."""
    
    @patch('pwa_launcher.get_chromium.find_chromium.get_edge_paths')
    def test_find_edge_success(self, mock_get_paths, tmp_path):
        """Test finding Edge when it exists."""
        edge_exe = tmp_path / "msedge.exe"
        edge_exe.touch()
        
        mock_get_paths.return_value = [edge_exe]
        
        result = find_edge()
        
        assert result == edge_exe
    
    @patch('pwa_launcher.get_chromium.find_chromium.get_edge_paths')
    def test_find_edge_not_found(self, mock_get_paths, tmp_path):
        """Test when Edge is not found."""
        edge_exe = tmp_path / "msedge.exe"
        
        mock_get_paths.return_value = [edge_exe]
        
        result = find_edge()
        
        assert result is None


class TestFindSystemChromium:
    """Tests for find_system_chromium function."""
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_returns_chrome_when_available(self, mock_edge, mock_chrome, tmp_path):
        """Test that Chrome is preferred when both are available."""
        chrome_exe = tmp_path / "chrome.exe"
        edge_exe = tmp_path / "msedge.exe"
        
        mock_chrome.return_value = chrome_exe
        mock_edge.return_value = edge_exe
        
        result = find_system_chromium()
        
        assert result == chrome_exe
        mock_chrome.assert_called_once()
        # Edge shouldn't be called if Chrome is found
        mock_edge.assert_not_called()
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_returns_edge_when_chrome_not_available(self, mock_edge, mock_chrome, tmp_path):
        """Test that Edge is used as fallback when Chrome is not available."""
        edge_exe = tmp_path / "msedge.exe"
        
        mock_chrome.return_value = None
        mock_edge.return_value = edge_exe
        
        result = find_system_chromium()
        
        assert result == edge_exe
        mock_chrome.assert_called_once()
        mock_edge.assert_called_once()
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_returns_none_when_nothing_found(self, mock_edge, mock_chrome):
        """Test that None is returned when no browser is found."""
        mock_chrome.return_value = None
        mock_edge.return_value = None
        
        result = find_system_chromium()
        
        assert result is None
        mock_chrome.assert_called_once()
        mock_edge.assert_called_once()


class TestGetChromiumInfo:
    """Tests for get_chromium_info function."""
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_both_available(self, mock_edge, mock_chrome, tmp_path):
        """Test info when both browsers are available."""
        chrome_exe = tmp_path / "chrome.exe"
        edge_exe = tmp_path / "msedge.exe"
        
        mock_chrome.return_value = chrome_exe
        mock_edge.return_value = edge_exe
        
        info = get_chromium_info()
        
        assert info['chrome']['available'] is True
        assert info['chrome']['path'] == str(chrome_exe)
        assert info['edge']['available'] is True
        assert info['edge']['path'] == str(edge_exe)
        assert info['any_available'] is True
        assert info['preferred'] == str(chrome_exe)
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_only_chrome_available(self, mock_edge, mock_chrome, tmp_path):
        """Test info when only Chrome is available."""
        chrome_exe = tmp_path / "chrome.exe"
        
        mock_chrome.return_value = chrome_exe
        mock_edge.return_value = None
        
        info = get_chromium_info()
        
        assert info['chrome']['available'] is True
        assert info['edge']['available'] is False
        assert info['any_available'] is True
        assert info['preferred'] == str(chrome_exe)
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_only_edge_available(self, mock_edge, mock_chrome, tmp_path):
        """Test info when only Edge is available."""
        edge_exe = tmp_path / "msedge.exe"
        
        mock_chrome.return_value = None
        mock_edge.return_value = edge_exe
        
        info = get_chromium_info()
        
        assert info['chrome']['available'] is False
        assert info['edge']['available'] is True
        assert info['any_available'] is True
        assert info['preferred'] == str(edge_exe)
    
    @patch('pwa_launcher.get_chromium.find_chromium.find_chrome')
    @patch('pwa_launcher.get_chromium.find_chromium.find_edge')
    def test_none_available(self, mock_edge, mock_chrome):
        """Test info when no browsers are available."""
        mock_chrome.return_value = None
        mock_edge.return_value = None
        
        info = get_chromium_info()
        
        assert info['chrome']['available'] is False
        assert info['chrome']['path'] is None
        assert info['edge']['available'] is False
        assert info['edge']['path'] is None
        assert info['any_available'] is False
        assert info['preferred'] is None


class TestRealSystem:
    """Tests that run on the actual system (not mocked)."""
    
    def test_find_chrome_returns_path_or_none(self):
        """Test that find_chrome returns Path or None."""
        result = find_chrome()
        assert result is None or isinstance(result, Path)
    
    def test_find_edge_returns_path_or_none(self):
        """Test that find_edge returns Path or None."""
        result = find_edge()
        assert result is None or isinstance(result, Path)
    
    def test_find_system_chromium_returns_path_or_none(self):
        """Test that find_system_chromium returns Path or None."""
        result = find_system_chromium()
        assert result is None or isinstance(result, Path)
        if result:
            assert result.exists()
            assert result.is_file()
    
    def test_get_chromium_info_returns_dict(self):
        """Test that get_chromium_info returns proper dict structure."""
        info = get_chromium_info()
        assert isinstance(info, dict)
        assert 'chrome' in info
        assert 'edge' in info
        assert 'any_available' in info
        assert 'preferred' in info
        assert isinstance(info['chrome']['available'], bool)
        assert isinstance(info['edge']['available'], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
