"""
Tests for open_pwa module.
"""
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from pwa_launcher.open_pwa import open_pwa
from pwa_launcher.get_chromium import ChromiumNotFoundError


class TestOpenPWA:
    """Tests for open_pwa function."""
    
    def test_basic_launch(self):
        """Test basic PWA launch."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process
                
                process = open_pwa("https://example.com")
                
                assert process.pid == 12345
                mock_popen.assert_called_once()
                
                # Check that --app flag is in the command
                call_args = mock_popen.call_args[0][0]
                assert any('--app=https://example.com' in arg for arg in call_args)
    
    def test_with_chromium_path(self):
        """Test PWA launch with explicit Chromium path."""
        chrome_path = Path("/custom/chrome")
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            process = open_pwa("https://example.com", chromium_path=chrome_path)
            
            assert process.pid == 12345
            
            # Check that custom chrome path is used
            call_args = mock_popen.call_args[0][0]
            assert call_args[0] == str(chrome_path)
    
    def test_normalizes_url(self):
        """Test that URL is normalized with https:// if missing."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                open_pwa("example.com")
                
                # Check that https:// was added
                call_args = mock_popen.call_args[0][0]
                assert any('--app=https://example.com' in arg for arg in call_args)
    
    def test_preserves_http(self):
        """Test that existing http:// scheme is preserved."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                open_pwa("http://localhost:3000")
                
                # Check that http:// was preserved
                call_args = mock_popen.call_args[0][0]
                assert any('--app=http://localhost:3000' in arg for arg in call_args)
    
    def test_with_user_data_dir(self):
        """Test PWA launch with custom user data directory."""
        mock_chrome = Path("/usr/bin/chrome")
        user_data_dir = Path("/tmp/test_profile")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                with patch('pathlib.Path.mkdir'):
                    open_pwa("https://example.com", user_data_dir=user_data_dir)
                
                # Check that user-data-dir flag is present
                call_args = mock_popen.call_args[0][0]
                assert any(f'--user-data-dir={user_data_dir}' in arg for arg in call_args)
    
    def test_with_additional_flags(self):
        """Test PWA launch with additional flags."""
        mock_chrome = Path("/usr/bin/chrome")
        additional_flags = ["--start-maximized", "--incognito"]
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                open_pwa("https://example.com", additional_flags=additional_flags)
                
                # Check that additional flags are present
                call_args = mock_popen.call_args[0][0]
                assert "--start-maximized" in call_args
                assert "--incognito" in call_args
    
    def test_includes_pwa_flags(self):
        """Test that PWA-specific flags are included."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                open_pwa("https://example.com")
                
                # Check for some expected PWA flags
                call_args = mock_popen.call_args[0][0]
                assert any('WebAppInstallation' in arg for arg in call_args)
                assert any('--no-default-browser-check' in arg for arg in call_args)
                assert any('--no-first-run' in arg for arg in call_args)
    
    def test_wait_mode(self):
        """Test PWA launch in wait mode."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.returncode = 0
                mock_popen.return_value = mock_process
                
                open_pwa("https://example.com", wait=True)
                
                # Check that wait was called
                mock_process.wait.assert_called_once()
    
    def test_empty_url_raises(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            open_pwa("")
        
        with pytest.raises(ValueError, match="URL cannot be empty"):
            open_pwa("   ")
    
    def test_chromium_not_found(self):
        """Test that ChromiumNotFoundError is raised when browser not found."""
        with patch('pwa_launcher.open_pwa.get_chromium_install', side_effect=ChromiumNotFoundError("Not found")):
            with pytest.raises(ChromiumNotFoundError):
                open_pwa("https://example.com")
    
    def test_respects_allow_system(self):
        """Test that allow_system parameter is passed through."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome) as mock_get:
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                open_pwa("https://example.com", allow_system=False)
                
                # Check that allow_system was passed
                mock_get.assert_called_once()
                assert mock_get.call_args[1]['allow_system'] is False
    
    def test_respects_allow_download(self):
        """Test that allow_download parameter is passed through."""
        mock_chrome = Path("/usr/bin/chrome")
        
        with patch('pwa_launcher.open_pwa.get_chromium_install', return_value=mock_chrome) as mock_get:
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_popen.return_value = mock_process
                
                open_pwa("https://example.com", allow_download=False)
                
                # Check that allow_download was passed
                mock_get.assert_called_once()
                assert mock_get.call_args[1]['allow_download'] is False
