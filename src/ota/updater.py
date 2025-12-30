"""
OTA Updater - Over-The-Air Update System

Handles checking for, downloading, and installing updates remotely.
Includes automatic rollback on failure and configuration preservation.

Usage:
    from ota.updater import OTAUpdater

    updater = OTAUpdater(
        update_url="https://raw.githubusercontent.com/user/repo/main/version.json"
    )

    # Check for updates
    if updater.check_for_update():
        print(f"Update available: {updater.latest_version}")
        updater.install_update()
"""

import json
import gc
import time

# Try to import MicroPython-specific modules
try:
    import urequests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import os
    OS_AVAILABLE = True
except ImportError:
    OS_AVAILABLE = False

try:
    import hashlib
    HASH_AVAILABLE = True
except ImportError:
    HASH_AVAILABLE = False

try:
    import machine
    MACHINE_AVAILABLE = True
except ImportError:
    MACHINE_AVAILABLE = False


class OTAUpdater:
    """Manages over-the-air software updates."""

    # Version file format
    VERSION_FILE = '/version.json'

    # Update configuration
    UPDATE_CHECK_INTERVAL = 86400  # 24 hours
    MAX_DOWNLOAD_RETRIES = 3
    BACKUP_DIR = '/backups'
    UPDATE_DIR = '/tmp/update'
    BOOT_COUNT_FILE = '/boot_count.txt'
    MAX_BOOT_FAILURES = 3

    def __init__(self, update_url, auto_check=True, proxy_url=None):
        """
        Initialize OTA updater.

        Args:
            update_url: URL to version.json file (or proxy /api/ota/version)
            auto_check: Automatically check for updates daily
            proxy_url: Proxy URL for file-by-file downloads (e.g., https://espn-proxy.vercel.app)
        """
        self.update_url = update_url
        self.proxy_url = proxy_url
        self.auto_check = auto_check
        self.current_version = self._load_current_version()
        self.latest_version = None
        self.update_info = None
        self._last_check = 0

        # Check boot count for rollback detection
        self._check_boot_failures()

    def _load_current_version(self):
        """Load current version from version.json."""
        try:
            with open(self.VERSION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('version', '0.0.0')
        except:
            return '0.0.0'

    def _save_version(self, version):
        """Save version info."""
        data = {
            'version': version,
            'installed': int(time.time()),
            'build': 'prod'
        }
        with open(self.VERSION_FILE, 'w') as f:
            json.dump(data, f)

    def _check_boot_failures(self):
        """Check if we've had multiple boot failures (rollback trigger)."""
        if not OS_AVAILABLE:
            return

        try:
            with open(self.BOOT_COUNT_FILE, 'r') as f:
                count = int(f.read().strip())
        except:
            count = 0

        if count >= self.MAX_BOOT_FAILURES:
            print(f"OTA: Boot failure count: {count}. Triggering rollback...")
            self.rollback()
            return

        # Increment boot count
        count += 1
        with open(self.BOOT_COUNT_FILE, 'w') as f:
            f.write(str(count))

    def mark_boot_successful(self):
        """Mark boot as successful (reset failure counter)."""
        if not OS_AVAILABLE:
            return

        try:
            import os
            os.remove(self.BOOT_COUNT_FILE)
        except:
            pass

    def check_for_update(self):
        """
        Check if update is available.

        Returns:
            bool: True if update available
        """
        if not REQUESTS_AVAILABLE:
            print("OTA: urequests not available")
            return False

        try:
            print(f"OTA: Checking for updates at {self.update_url}")
            response = urequests.get(self.update_url, timeout=10)

            if response.status_code != 200:
                print(f"OTA: Check failed: HTTP {response.status_code}")
                response.close()
                return False

            self.update_info = response.json()
            self.latest_version = self.update_info.get('version', '0.0.0')
            response.close()

            self._last_check = time.time()

            print(f"OTA: Current: {self.current_version}, Latest: {self.latest_version}")

            # Compare versions
            if self._version_greater(self.latest_version, self.current_version):
                print(f"OTA: Update available: v{self.latest_version}")
                return True
            else:
                print("OTA: Already on latest version")
                return False

        except Exception as e:
            print(f"OTA: Update check error: {e}")
            return False
        finally:
            gc.collect()

    def _version_greater(self, v1, v2):
        """Compare semantic versions (MAJOR.MINOR.PATCH)."""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]

            # Pad to 3 parts
            while len(parts1) < 3:
                parts1.append(0)
            while len(parts2) < 3:
                parts2.append(0)

            for i in range(3):
                if parts1[i] > parts2[i]:
                    return True
                elif parts1[i] < parts2[i]:
                    return False

            return False  # Equal
        except:
            return False

    def get_changelog(self):
        """Get changelog for latest version."""
        if self.update_info:
            return self.update_info.get('changelog', 'No changelog available')
        return None

    def is_breaking_change(self):
        """Check if update has breaking changes."""
        if self.update_info:
            return self.update_info.get('breaking_changes', False)
        return False

    def download_update(self, progress_callback=None):
        """
        Download update file.

        Args:
            progress_callback: Function(bytes_downloaded, total_bytes)

        Returns:
            str: Path to downloaded file, or None on failure
        """
        if not REQUESTS_AVAILABLE or not OS_AVAILABLE:
            print("OTA: Required modules not available")
            return None

        if not self.update_info:
            print("OTA: No update info available")
            return None

        download_url = self.update_info.get('download_url')
        if not download_url:
            print("OTA: No download URL in update info")
            return None

        expected_checksum = self.update_info.get('checksum', '')

        # Create temp directory
        try:
            import os
            os.mkdir(self.UPDATE_DIR)
        except:
            pass

        download_path = f"{self.UPDATE_DIR}/update.tar.gz"

        # Download with retries
        for attempt in range(self.MAX_DOWNLOAD_RETRIES):
            try:
                print(f"OTA: Downloading update (attempt {attempt + 1})...")

                response = urequests.get(download_url, timeout=60)

                if response.status_code != 200:
                    print(f"OTA: Download failed: HTTP {response.status_code}")
                    response.close()
                    continue

                # Save to file
                content = response.content
                response.close()

                with open(download_path, 'wb') as f:
                    f.write(content)

                print(f"OTA: Downloaded {len(content)} bytes")

                # Verify checksum
                if expected_checksum and HASH_AVAILABLE:
                    actual_checksum = self._calculate_checksum(download_path)
                    expected_hash = expected_checksum.split(':')[1] if ':' in expected_checksum else expected_checksum

                    if actual_checksum != expected_hash:
                        print(f"OTA: Checksum mismatch!")
                        print(f"  Expected: {expected_hash}")
                        print(f"  Actual: {actual_checksum}")
                        continue

                    print("OTA: Checksum verified")

                gc.collect()
                return download_path

            except Exception as e:
                print(f"OTA: Download error: {e}")
                time.sleep(5)  # Wait before retry
            finally:
                gc.collect()

        print("OTA: Download failed after all retries")
        return None

    def _calculate_checksum(self, filepath):
        """Calculate SHA256 checksum of file."""
        if not HASH_AVAILABLE:
            return ''

        sha = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()

    def backup_current_version(self):
        """Backup current version before update."""
        if not OS_AVAILABLE:
            return False

        try:
            import os
            backup_path = f"{self.BACKUP_DIR}/v{self.current_version}"

            # Create backups directory
            try:
                os.mkdir(self.BACKUP_DIR)
            except:
                pass

            # Create version-specific backup
            try:
                os.mkdir(backup_path)
            except:
                pass

            # Backup main files
            files_to_backup = [
                'main.py',
                'boot.py',
                'config.json',
                self.VERSION_FILE.lstrip('/')
            ]

            for filename in files_to_backup:
                try:
                    self._copy_file(f'/{filename}', f'{backup_path}/{filename}')
                except:
                    pass  # File might not exist

            # Backup src directory
            self._backup_directory('/src', f'{backup_path}/src')

            print(f"OTA: Backup created: {backup_path}")
            return True

        except Exception as e:
            print(f"OTA: Backup error: {e}")
            return False

    def _backup_directory(self, src_dir, dst_dir):
        """Recursively backup directory."""
        import os

        try:
            os.mkdir(dst_dir)
        except:
            pass

        try:
            items = os.listdir(src_dir)
        except:
            return

        for item in items:
            src_path = f"{src_dir}/{item}"
            dst_path = f"{dst_dir}/{item}"

            try:
                # Check if directory
                os.listdir(src_path)
                # It's a directory, recurse
                self._backup_directory(src_path, dst_path)
            except:
                # It's a file, copy it
                try:
                    self._copy_file(src_path, dst_path)
                except:
                    pass

    def _copy_file(self, src, dst):
        """Copy file from src to dst."""
        with open(src, 'rb') as f_src:
            with open(dst, 'wb') as f_dst:
                while True:
                    chunk = f_src.read(1024)
                    if not chunk:
                        break
                    f_dst.write(chunk)

    def install_update(self, update_path=None, progress_callback=None):
        """
        Install update by downloading files from proxy.

        Args:
            update_path: Ignored (kept for API compatibility)
            progress_callback: Function(current_file, total_files, filename)

        Returns:
            bool: True if installation successful
        """
        if not self.proxy_url:
            print("OTA: No proxy URL configured - cannot install")
            return False

        if not self.latest_version:
            print("OTA: No version info - run check_for_update() first")
            return False

        try:
            print(f"OTA: Installing v{self.latest_version} from proxy...")

            # Step 1: Get manifest of files to download
            manifest_url = f"{self.proxy_url}/api/ota/manifest?version={self.latest_version}"
            print(f"OTA: Fetching manifest...")

            response = urequests.get(manifest_url, timeout=30)
            if response.status_code != 200:
                print(f"OTA: Failed to get manifest: HTTP {response.status_code}")
                response.close()
                return False

            manifest = response.json()
            response.close()
            gc.collect()

            files = manifest.get('files', [])
            if not files:
                print("OTA: Empty manifest!")
                return False

            print(f"OTA: {len(files)} files to install")

            # Step 2: Download and install each file
            installed = 0
            for i, file_info in enumerate(files):
                path = file_info['path']
                expected_size = file_info.get('size', 0)
                expected_checksum = file_info.get('checksum', '')

                if progress_callback:
                    progress_callback(i + 1, len(files), path)

                print(f"OTA: [{i+1}/{len(files)}] {path}")

                # Download file
                file_url = f"{self.proxy_url}/api/ota/file?version={self.latest_version}&path={path}"

                for attempt in range(self.MAX_DOWNLOAD_RETRIES):
                    try:
                        response = urequests.get(file_url, timeout=30)

                        if response.status_code != 200:
                            print(f"OTA: Download failed: HTTP {response.status_code}")
                            response.close()
                            continue

                        content = response.content
                        response.close()

                        # Verify size
                        if expected_size and len(content) != expected_size:
                            print(f"OTA: Size mismatch: {len(content)} vs {expected_size}")
                            continue

                        # Verify checksum if available
                        if expected_checksum and HASH_AVAILABLE:
                            actual = hashlib.sha256(content).hexdigest()[:16]
                            if actual != expected_checksum:
                                print(f"OTA: Checksum mismatch!")
                                continue

                        # Ensure directory exists
                        self._ensure_dir('/' + path)

                        # Write file
                        with open('/' + path, 'wb') as f:
                            f.write(content)

                        installed += 1
                        gc.collect()
                        break

                    except Exception as e:
                        print(f"OTA: Error downloading {path}: {e}")
                        gc.collect()
                        time.sleep(1)

            print(f"OTA: Installed {installed}/{len(files)} files")

            if installed < len(files):
                print("OTA: Some files failed to install!")
                self._log_update('partial', f"{installed}/{len(files)} files")
                return False

            # Step 3: Update version file
            self._save_version(self.latest_version)

            print(f"OTA: Update to v{self.latest_version} complete!")
            self._log_update('success')

            return True

        except Exception as e:
            print(f"OTA: Installation error: {e}")
            self._log_update('failed', str(e))
            return False
        finally:
            gc.collect()

    def _ensure_dir(self, filepath):
        """Ensure directory exists for a file path."""
        if not OS_AVAILABLE:
            return

        import os

        # Get directory path
        parts = filepath.split('/')
        if len(parts) <= 2:
            return  # Root level file, no dir needed

        # Build directory path
        dir_path = '/'.join(parts[:-1])

        # Create directories recursively
        current = ''
        for part in parts[:-1]:
            if not part:
                continue
            current += '/' + part
            try:
                os.mkdir(current)
            except OSError:
                pass  # Directory exists

    def _log_update(self, status, error=None):
        """Log update attempt."""
        log_entry = {
            'timestamp': int(time.time()),
            'from_version': self.current_version,
            'to_version': self.latest_version,
            'status': status,
            'error': error
        }

        try:
            # Ensure logs directory exists
            try:
                import os
                os.mkdir('/logs')
            except:
                pass

            # Append to log file
            with open('/logs/ota_update.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass

    def rollback(self):
        """Rollback to previous version."""
        if not OS_AVAILABLE:
            return False

        try:
            import os
            print("OTA: Rolling back to previous version...")

            # Find most recent backup
            try:
                backups = os.listdir(self.BACKUP_DIR)
            except:
                print("OTA: No backups directory!")
                return False

            if not backups:
                print("OTA: No backups available!")
                return False

            # Sort by version (latest first)
            backups.sort(reverse=True)
            latest_backup = backups[0]
            backup_path = f"{self.BACKUP_DIR}/{latest_backup}"

            print(f"OTA: Restoring from: {backup_path}")

            # Restore files
            self._restore_directory(backup_path, '/')

            # Reset boot count
            self.mark_boot_successful()

            print("OTA: Rollback complete")
            self._log_update('rolled_back')

            return True

        except Exception as e:
            print(f"OTA: Rollback error: {e}")
            return False

    def _restore_directory(self, src_dir, dst_dir):
        """Recursively restore directory."""
        import os

        try:
            items = os.listdir(src_dir)
        except:
            return

        for item in items:
            src_path = f"{src_dir}/{item}"
            dst_path = f"{dst_dir}/{item}"

            try:
                # Check if directory
                os.listdir(src_path)
                # It's a directory, recurse
                try:
                    os.mkdir(dst_path)
                except:
                    pass
                self._restore_directory(src_path, dst_path)
            except:
                # It's a file, copy it
                try:
                    self._copy_file(src_path, dst_path)
                except:
                    pass

    def restart_device(self):
        """Restart device after update."""
        print("OTA: Restarting device...")
        time.sleep(2)

        if MACHINE_AVAILABLE:
            import machine
            machine.reset()
        else:
            print("OTA: machine.reset() not available (running on PC)")

    def full_update_flow(self, progress_callback=None):
        """
        Complete update flow: check, backup, install, restart.

        Uses proxy for file-by-file download (no tarball needed).

        Args:
            progress_callback: Function(current_file, total_files, filename)

        Returns:
            bool: True if update completed successfully
        """
        try:
            # 1. Check for update
            if not self.check_for_update():
                return False

            # 2. Backup current version
            if not self.backup_current_version():
                print("OTA: Warning: Backup failed, continuing anyway...")

            # 3. Install update (downloads files from proxy)
            if not self.install_update(progress_callback=progress_callback):
                return False

            # 4. Restart device
            self.restart_device()

            return True

        except Exception as e:
            print(f"OTA: Update flow error: {e}")
            return False

    def get_status(self):
        """Get current OTA status."""
        return {
            'current_version': self.current_version,
            'latest_version': self.latest_version,
            'update_available': self.latest_version and self._version_greater(
                self.latest_version, self.current_version),
            'auto_check': self.auto_check,
            'last_check': self._last_check,
        }


# Convenience function for simple updates
def check_and_update(update_url):
    """Simple one-line update check and install."""
    updater = OTAUpdater(update_url)
    if updater.check_for_update():
        print(f"OTA: Installing update: v{updater.latest_version}")
        print(f"OTA: Changelog: {updater.get_changelog()}")
        return updater.full_update_flow()
    return False


# Singleton instance
_updater = None


def get_updater(update_url=None):
    """Get global OTA updater instance."""
    global _updater
    if _updater is None and update_url:
        _updater = OTAUpdater(update_url)
    return _updater


# Test when run directly
if __name__ == '__main__':
    print("OTA Updater Test")
    print("=" * 50)

    # Example usage
    UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/sports-ticker/main/version.json"

    updater = OTAUpdater(UPDATE_URL, auto_check=False)

    print(f"Current version: {updater.current_version}")
    print(f"Status: {updater.get_status()}")

    # Note: Actual update check requires network
    print("\nOTA updater initialized successfully")
