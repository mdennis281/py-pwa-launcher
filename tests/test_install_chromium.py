"""
Tests for the Chromium installer module.
"""
import json
import platform
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import pytest

from pwa_launcher.get_chromium.install_chromium import (
    get_chrome_for_testing_url,
    download_file,
    extract_archive,
    get_chromium_executable_path,
    install_chromium,
    find_existing_chromium,
)


class TestGetChromeForTestingUrl:
    """Tests for get_chrome_for_testing_url function."""
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock API response from Chrome for Testing."""
        return {
            "channels": {
                "Stable": {
                    "downloads": {
                        "chrome": [
                            {
                                "platform": "win64",
                                "url": "https://example.com/chrome-win64.zip"
                            },
                            {
                                "platform": "win32",
                                "url": "https://example.com/chrome-win32.zip"
                            },
                            {
                                "platform": "mac-x64",
                                "url": "https://example.com/chrome-mac-x64.zip"
                            },
                            {
                                "platform": "mac-arm64",
                                "url": "https://example.com/chrome-mac-arm64.zip"
                            },
                            {
                                "platform": "linux64",
                                "url": "https://example.com/chrome-linux64.zip"
                            }
                        ]
                    }
                }
            }
        }
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_windows_64bit(self, mock_urlopen, mock_machine, mock_system, mock_api_response):
        """Test URL retrieval for Windows 64-bit."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "amd64"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        url, platform_id = get_chrome_for_testing_url()
        
        assert url == "https://example.com/chrome-win64.zip"
        assert platform_id == "win64"
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_windows_32bit(self, mock_urlopen, mock_machine, mock_system, mock_api_response):
        """Test URL retrieval for Windows 32-bit."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "x86"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        url, platform_id = get_chrome_for_testing_url()
        
        assert url == "https://example.com/chrome-win32.zip"
        assert platform_id == "win32"
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_macos_intel(self, mock_urlopen, mock_machine, mock_system, mock_api_response):
        """Test URL retrieval for macOS Intel."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "x86_64"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        url, platform_id = get_chrome_for_testing_url()
        
        assert url == "https://example.com/chrome-mac-x64.zip"
        assert platform_id == "mac-x64"
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_macos_arm(self, mock_urlopen, mock_machine, mock_system, mock_api_response):
        """Test URL retrieval for macOS ARM (Apple Silicon)."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        url, platform_id = get_chrome_for_testing_url()
        
        assert url == "https://example.com/chrome-mac-arm64.zip"
        assert platform_id == "mac-arm64"
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_linux(self, mock_urlopen, mock_machine, mock_system, mock_api_response):
        """Test URL retrieval for Linux."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        url, platform_id = get_chrome_for_testing_url()
        
        assert url == "https://example.com/chrome-linux64.zip"
        assert platform_id == "linux64"
    
    @patch('platform.system')
    def test_unsupported_platform(self, mock_system):
        """Test that unsupported platforms raise an error."""
        mock_system.return_value = "FreeBSD"
        
        with pytest.raises(OSError, match="Unsupported platform"):
            get_chrome_for_testing_url()
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_api_error(self, mock_urlopen, mock_machine, mock_system):
        """Test handling of API request errors."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "amd64"
        mock_urlopen.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to get Chrome for Testing download URL"):
            get_chrome_for_testing_url()
    
    @patch('platform.system')
    @patch('platform.machine')
    @patch('urllib.request.urlopen')
    def test_missing_platform(self, mock_urlopen, mock_machine, mock_system):
        """Test handling when platform is not in API response."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "amd64"
        
        mock_response = MagicMock()
        # Return response without win64 platform
        mock_response.read.return_value = json.dumps({
            "channels": {
                "Stable": {
                    "downloads": {
                        "chrome": [
                            {"platform": "linux64", "url": "https://example.com/chrome-linux64.zip"}
                        ]
                    }
                }
            }
        }).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Failed to get Chrome for Testing download URL"):
            get_chrome_for_testing_url()


class TestDownloadFile:
    """Tests for download_file function."""
    
    @patch('urllib.request.urlopen')
    def test_download_success(self, mock_urlopen, tmp_path):
        """Test successful file download."""
        test_content = b"test file content"
        dest_path = tmp_path / "test.zip"
        
        mock_response = MagicMock()
        mock_response.read.side_effect = [test_content, b""]
        mock_response.headers.get.return_value = str(len(test_content))
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        download_file("https://example.com/test.zip", dest_path)
        
        assert dest_path.exists()
        assert dest_path.read_bytes() == test_content
    
    @patch('urllib.request.urlopen')
    def test_download_with_callback(self, mock_urlopen, tmp_path):
        """Test download with progress callback."""
        test_content = b"test file content"
        dest_path = tmp_path / "test.zip"
        callback_calls = []
        
        def progress_callback(downloaded, total):
            callback_calls.append((downloaded, total))
        
        mock_response = MagicMock()
        mock_response.read.side_effect = [test_content, b""]
        mock_response.headers.get.return_value = str(len(test_content))
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        download_file("https://example.com/test.zip", dest_path, progress_callback)
        
        assert len(callback_calls) > 0
        assert callback_calls[-1] == (len(test_content), len(test_content))
    
    @patch('urllib.request.urlopen')
    def test_download_no_content_length(self, mock_urlopen, tmp_path):
        """Test download when content-length header is missing."""
        test_content = b"test content"
        dest_path = tmp_path / "test.zip"
        
        mock_response = MagicMock()
        mock_response.read.side_effect = [test_content, b""]
        # Return empty string instead of None
        mock_response.headers.get.return_value = ''
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        download_file("https://example.com/test.zip", dest_path)
        
        assert dest_path.exists()
        assert dest_path.read_bytes() == test_content


class TestExtractArchive:
    """Tests for extract_archive function."""
    
    def test_extract_zip(self, tmp_path):
        """Test extracting a zip archive."""
        # Create a test zip file
        zip_path = tmp_path / "test.zip"
        extract_to = tmp_path / "extracted"
        extract_to.mkdir()
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test_file.txt", "test content")
            zf.writestr("subdir/another.txt", "more content")
        
        extract_archive(zip_path, extract_to)
        
        assert (extract_to / "test_file.txt").exists()
        assert (extract_to / "subdir" / "another.txt").exists()
        assert (extract_to / "test_file.txt").read_text() == "test content"


class TestGetChromiumExecutablePath:
    """Tests for get_chromium_executable_path function."""
    
    @patch('platform.system')
    def test_windows_executable_path(self, mock_system, tmp_path):
        """Test finding Chrome executable on Windows."""
        mock_system.return_value = "Windows"
        
        chrome_dir = tmp_path / "chrome-win64"
        chrome_dir.mkdir()
        exe_path = chrome_dir / "chrome.exe"
        exe_path.touch()
        
        result = get_chromium_executable_path(tmp_path, "win64")
        
        assert result == exe_path
        assert result.exists()
    
    @patch('platform.system')
    def test_windows_fallback_glob(self, mock_system, tmp_path):
        """Test Windows fallback to glob pattern."""
        mock_system.return_value = "Windows"
        
        chrome_dir = tmp_path / "chrome-win32"
        chrome_dir.mkdir()
        exe_path = chrome_dir / "chrome.exe"
        exe_path.touch()
        
        result = get_chromium_executable_path(tmp_path, "win64")
        
        assert result == exe_path
    
    @patch('platform.system')
    @patch('os.chmod')
    def test_macos_executable_path(self, mock_chmod, mock_system, tmp_path):
        """Test finding Chrome executable on macOS."""
        mock_system.return_value = "Darwin"
        
        chrome_dir = tmp_path / "chrome-mac-x64"
        app_dir = chrome_dir / "Google Chrome for Testing.app" / "Contents" / "MacOS"
        app_dir.mkdir(parents=True)
        exe_path = app_dir / "Google Chrome for Testing"
        exe_path.touch()
        
        result = get_chromium_executable_path(tmp_path, "mac-x64")
        
        assert result == exe_path
        mock_chmod.assert_called_once_with(exe_path, 0o755)
    
    @patch('platform.system')
    @patch('os.chmod')
    def test_linux_executable_path(self, mock_chmod, mock_system, tmp_path):
        """Test finding Chrome executable on Linux."""
        mock_system.return_value = "Linux"
        
        chrome_dir = tmp_path / "chrome-linux64"
        chrome_dir.mkdir()
        exe_path = chrome_dir / "chrome"
        exe_path.touch()
        
        result = get_chromium_executable_path(tmp_path, "linux64")
        
        assert result == exe_path
        mock_chmod.assert_called_once_with(exe_path, 0o755)
    
    @patch('platform.system')
    def test_executable_not_found(self, mock_system, tmp_path):
        """Test error when executable is not found."""
        mock_system.return_value = "Windows"
        
        with pytest.raises(FileNotFoundError, match="Chrome executable not found"):
            get_chromium_executable_path(tmp_path, "win64")
    
    @patch('platform.system')
    def test_unsupported_platform(self, mock_system, tmp_path):
        """Test error for unsupported platform."""
        mock_system.return_value = "FreeBSD"
        
        with pytest.raises(OSError, match="Unsupported platform"):
            get_chromium_executable_path(tmp_path, "freebsd")


class TestFindExistingChromium:
    """Tests for find_existing_chromium function."""
    
    @patch('platform.system')
    def test_find_windows_chromium(self, mock_system, tmp_path):
        """Test finding existing Chrome on Windows."""
        mock_system.return_value = "Windows"
        
        chrome_dir = tmp_path / "chrome-win64"
        chrome_dir.mkdir()
        exe_path = chrome_dir / "chrome.exe"
        exe_path.touch()
        
        result = find_existing_chromium(tmp_path)
        
        assert result == exe_path
    
    @patch('platform.system')
    def test_find_macos_chromium(self, mock_system, tmp_path):
        """Test finding existing Chrome on macOS."""
        mock_system.return_value = "Darwin"
        
        chrome_dir = tmp_path / "chrome-mac-x64"
        app_dir = chrome_dir / "Google Chrome for Testing.app" / "Contents" / "MacOS"
        app_dir.mkdir(parents=True)
        exe_path = app_dir / "Google Chrome for Testing"
        exe_path.touch()
        
        result = find_existing_chromium(tmp_path)
        
        assert result == exe_path
    
    @patch('platform.system')
    def test_find_linux_chromium(self, mock_system, tmp_path):
        """Test finding existing Chrome on Linux."""
        mock_system.return_value = "Linux"
        
        chrome_dir = tmp_path / "chrome-linux64"
        chrome_dir.mkdir()
        exe_path = chrome_dir / "chrome"
        exe_path.touch()
        
        result = find_existing_chromium(tmp_path)
        
        assert result == exe_path
    
    def test_find_nonexistent_directory(self, tmp_path):
        """Test when install directory doesn't exist."""
        nonexistent = tmp_path / "does_not_exist"
        
        result = find_existing_chromium(nonexistent)
        
        assert result is None
    
    @patch('platform.system')
    def test_find_empty_directory(self, mock_system, tmp_path):
        """Test when directory exists but Chrome is not installed."""
        mock_system.return_value = "Windows"
        tmp_path.mkdir(exist_ok=True)
        
        result = find_existing_chromium(tmp_path)
        
        assert result is None
    
    @patch('platform.system')
    @patch('tempfile.gettempdir')
    def test_find_default_location(self, mock_gettempdir, mock_system, tmp_path):
        """Test finding Chrome at default location when no path provided."""
        mock_system.return_value = "Windows"
        mock_gettempdir.return_value = str(tmp_path)
        
        default_dir = tmp_path / "chromium_install"
        chrome_dir = default_dir / "chrome-win64"
        chrome_dir.mkdir(parents=True)
        exe_path = chrome_dir / "chrome.exe"
        exe_path.touch()
        
        result = find_existing_chromium()
        
        assert result == exe_path
    
    @patch('platform.system')
    def test_find_with_exception(self, mock_system, tmp_path):
        """Test that exceptions are handled gracefully."""
        mock_system.return_value = "Windows"
        mock_system.side_effect = Exception("Unexpected error")
        
        result = find_existing_chromium(tmp_path)
        
        assert result is None


class TestInstallChromium:
    """Tests for install_chromium function."""
    
    @patch('pwa_launcher.get_chromium.install_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chrome_for_testing_url')
    @patch('pwa_launcher.get_chromium.install_chromium.download_file')
    @patch('pwa_launcher.get_chromium.install_chromium.extract_archive')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chromium_executable_path')
    def test_install_uses_existing(
        self,
        mock_get_exe,
        mock_extract,
        mock_download,
        mock_get_url,
        mock_find,
        tmp_path
    ):
        """Test that install_chromium uses existing installation by default."""
        existing_path = tmp_path / "chrome-win64" / "chrome.exe"
        mock_find.return_value = existing_path
        
        result = install_chromium(install_dir=tmp_path, clean_existing=False)
        
        assert result == existing_path
        # Should not download when existing Chrome is found
        mock_get_url.assert_not_called()
        mock_download.assert_not_called()
        mock_extract.assert_not_called()
    
    @patch('pwa_launcher.get_chromium.install_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chrome_for_testing_url')
    @patch('pwa_launcher.get_chromium.install_chromium.download_file')
    @patch('pwa_launcher.get_chromium.install_chromium.extract_archive')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chromium_executable_path')
    def test_install_force_reinstall(
        self,
        mock_get_exe,
        mock_extract,
        mock_download,
        mock_get_url,
        mock_find,
        tmp_path
    ):
        """Test that force_reinstall bypasses existing installation check."""
        existing_path = tmp_path / "chrome-win64" / "chrome.exe"
        mock_find.return_value = existing_path
        
        mock_get_url.return_value = ("https://example.com/chrome.zip", "win64")
        new_exe_path = tmp_path / "chrome-win64" / "chrome.exe"
        mock_get_exe.return_value = new_exe_path
        
        # Create the archive file that download_file would create
        archive_path = tmp_path / "chrome.zip"
        archive_path.touch()
        
        result = install_chromium(install_dir=tmp_path, clean_existing=False, force_reinstall=True)
        
        # Should download even though existing Chrome was found
        mock_find.assert_not_called()  # Shouldn't even check for existing
        mock_get_url.assert_called_once()
        mock_download.assert_called_once()


class TestInstallChromiumLegacy:
    """Tests for install_chromium function (legacy tests)."""
    
    @patch('pwa_launcher.get_chromium.install_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chrome_for_testing_url')
    @patch('pwa_launcher.get_chromium.install_chromium.download_file')
    @patch('pwa_launcher.get_chromium.install_chromium.extract_archive')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chromium_executable_path')
    def test_install_chromium_success(
        self, 
        mock_get_exe, 
        mock_extract, 
        mock_download, 
        mock_get_url,
        mock_find,
        tmp_path
    ):
        """Test successful Chromium installation."""
        mock_find.return_value = None  # No existing installation
        mock_get_url.return_value = ("https://example.com/chrome.zip", "win64")
        mock_exe_path = tmp_path / "chrome-win64" / "chrome.exe"
        mock_get_exe.return_value = mock_exe_path
        
        # Create the archive file that download_file would create
        archive_path = tmp_path / "chrome.zip"
        archive_path.touch()
        
        result = install_chromium(install_dir=tmp_path, clean_existing=False)
        
        assert result == mock_exe_path
        mock_get_url.assert_called_once()
        mock_download.assert_called_once()
        mock_extract.assert_called_once()
        mock_get_exe.assert_called_once()
    
    @patch('pwa_launcher.get_chromium.install_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chrome_for_testing_url')
    @patch('pwa_launcher.get_chromium.install_chromium.download_file')
    @patch('pwa_launcher.get_chromium.install_chromium.extract_archive')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chromium_executable_path')
    @patch('shutil.rmtree')
    def test_install_chromium_clean_existing(
        self,
        mock_rmtree,
        mock_get_exe,
        mock_extract,
        mock_download,
        mock_get_url,
        mock_find,
        tmp_path
    ):
        """Test installation with cleaning existing files."""
        mock_find.return_value = None  # No existing installation after cleanup
        
        # Create existing directory
        install_dir = tmp_path / "chrome_install"
        install_dir.mkdir()
        (install_dir / "old_file.txt").touch()
        
        mock_get_url.return_value = ("https://example.com/chrome.zip", "win64")
        mock_exe_path = install_dir / "chrome-win64" / "chrome.exe"
        mock_get_exe.return_value = mock_exe_path
        
        # Create the archive file that download_file would create
        archive_path = install_dir / "chrome.zip"
        archive_path.touch()
        
        install_chromium(install_dir=install_dir, clean_existing=True)
        
        mock_rmtree.assert_called()
    
    @patch('pwa_launcher.get_chromium.install_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chrome_for_testing_url')
    @patch('shutil.rmtree')
    def test_install_chromium_cleanup_on_failure(
        self,
        mock_rmtree,
        mock_get_url,
        mock_find,
        tmp_path
    ):
        """Test cleanup when installation fails."""
        mock_find.return_value = None  # No existing installation
        mock_get_url.side_effect = Exception("Download failed")
        
        with pytest.raises(RuntimeError, match="Failed to install Chrome for Testing"):
            install_chromium(install_dir=tmp_path, clean_existing=False)
        
        # Verify cleanup was attempted
        mock_rmtree.assert_called()
    
    @patch('pwa_launcher.get_chromium.install_chromium.find_existing_chromium')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chrome_for_testing_url')
    @patch('pwa_launcher.get_chromium.install_chromium.download_file')
    @patch('pwa_launcher.get_chromium.install_chromium.extract_archive')
    @patch('pwa_launcher.get_chromium.install_chromium.get_chromium_executable_path')
    @patch('tempfile.gettempdir')
    def test_install_chromium_default_location(
        self,
        mock_gettempdir,
        mock_get_exe,
        mock_extract,
        mock_download,
        mock_get_url,
        mock_find,
        tmp_path
    ):
        """Test installation to default temp directory."""
        mock_find.return_value = None  # No existing installation
        mock_gettempdir.return_value = str(tmp_path)
        mock_get_url.return_value = ("https://example.com/chrome.zip", "win64")
        
        expected_dir = tmp_path / "chromium_install"
        expected_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the archive file that download_file would create
        archive_path = expected_dir / "chrome.zip"
        archive_path.touch()
        
        mock_exe_path = expected_dir / "chrome-win64" / "chrome.exe"
        mock_get_exe.return_value = mock_exe_path
        
        result = install_chromium(clean_existing=False)
        
        assert result == mock_exe_path


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_install_workflow(self, tmp_path):
        """
        Full integration test - downloads real Chrome for Testing.
        This test is marked as slow and integration, so it won't run by default.
        Run with: pytest -m integration
        """
        result = install_chromium(install_dir=tmp_path, clean_existing=True)
        
        assert result.exists()
        assert result.is_file()
        
        # Verify it's actually an executable
        system = platform.system()
        if system == "Windows":
            assert result.suffix == ".exe"
        else:
            # Check if file has executable permission
            assert result.stat().st_mode & 0o111


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
