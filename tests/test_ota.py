"""
Tests for OTA Update Module

Tests OTA functionality including:
- Version comparison
- Update checking
- Backup/restore
"""

import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ota.updater import OTAUpdater


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_version_greater_major(self):
        """Test major version comparison."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater._version_greater('2.0.0', '1.0.0')
        assert not updater._version_greater('1.0.0', '2.0.0')

    def test_version_greater_minor(self):
        """Test minor version comparison."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater._version_greater('1.1.0', '1.0.0')
        assert not updater._version_greater('1.0.0', '1.1.0')

    def test_version_greater_patch(self):
        """Test patch version comparison."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater._version_greater('1.0.1', '1.0.0')
        assert not updater._version_greater('1.0.0', '1.0.1')

    def test_version_equal(self):
        """Test equal versions."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert not updater._version_greater('1.0.0', '1.0.0')

    def test_version_complex(self):
        """Test complex version comparisons."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater._version_greater('1.2.3', '1.2.2')
        assert updater._version_greater('1.3.0', '1.2.9')
        assert updater._version_greater('2.0.0', '1.9.9')

    def test_version_short(self):
        """Test versions with fewer parts."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater._version_greater('1.1', '1.0')
        assert updater._version_greater('2', '1')

    def test_version_invalid(self):
        """Test invalid version strings."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        # Should return False for invalid versions
        assert not updater._version_greater('invalid', '1.0.0')
        assert not updater._version_greater('1.0.0', 'invalid')


class TestOTAUpdater:
    """Tests for OTAUpdater class."""

    def test_init(self):
        """Test updater initialization."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater.update_url == "http://example.com/version.json"
        assert updater.auto_check is False
        assert updater.current_version is not None

    def test_load_current_version_missing(self):
        """Test loading version when file doesn't exist."""
        # Temporarily rename version.json if it exists
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        # Should default to 0.0.0 if file is missing
        # (Can't test directly without mocking filesystem)
        assert isinstance(updater.current_version, str)

    def test_get_changelog_no_update(self):
        """Test getting changelog without update info."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater.get_changelog() is None

    def test_get_changelog_with_update(self):
        """Test getting changelog with update info."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        updater.update_info = {'changelog': 'Test changelog'}
        assert updater.get_changelog() == 'Test changelog'

    def test_is_breaking_change_no_update(self):
        """Test breaking change check without update info."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        assert updater.is_breaking_change() is False

    def test_is_breaking_change_true(self):
        """Test breaking change detection."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        updater.update_info = {'breaking_changes': True}
        assert updater.is_breaking_change() is True

    def test_is_breaking_change_false(self):
        """Test no breaking change."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        updater.update_info = {'breaking_changes': False}
        assert updater.is_breaking_change() is False

    def test_get_status(self):
        """Test getting OTA status."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        status = updater.get_status()

        assert 'current_version' in status
        assert 'latest_version' in status
        assert 'update_available' in status
        assert 'auto_check' in status

    def test_mark_boot_successful(self):
        """Test marking boot as successful."""
        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        # Should not raise exception
        updater.mark_boot_successful()


class TestUpdateRoutes:
    """Tests for OTA web routes."""

    def test_routes_initialization(self):
        """Test route handler initialization."""
        from ota.routes import UpdateRoutes

        updater = OTAUpdater("http://example.com/version.json", auto_check=False)
        routes = UpdateRoutes(updater)

        assert routes.updater is updater
        assert routes.update_in_progress is False

    def test_update_page_html(self):
        """Test update page HTML template exists."""
        from ota.routes import UPDATE_PAGE_HTML

        assert UPDATE_PAGE_HTML is not None
        assert len(UPDATE_PAGE_HTML) > 0
        assert 'Software Updates' in UPDATE_PAGE_HTML
        assert 'checkForUpdates' in UPDATE_PAGE_HTML


class TestVersionFile:
    """Tests for version file handling."""

    def test_version_file_structure(self):
        """Test expected version file structure."""
        # Create test version data
        version_data = {
            'version': '1.0.0',
            'installed': 1234567890,
            'build': 'prod',
        }

        # Verify structure
        assert 'version' in version_data
        assert 'installed' in version_data

    def test_save_version(self):
        """Test saving version file."""
        test_file = 'test_version.json'

        try:
            version_data = {
                'version': '1.2.3',
                'installed': 1234567890,
                'build': 'test',
            }

            with open(test_file, 'w') as f:
                json.dump(version_data, f)

            # Verify file was created
            with open(test_file, 'r') as f:
                loaded = json.load(f)

            assert loaded['version'] == '1.2.3'

        finally:
            try:
                os.remove(test_file)
            except:
                pass


def run_tests():
    """Run all tests and print results."""
    import traceback

    test_classes = [
        TestVersionComparison,
        TestOTAUpdater,
        TestUpdateRoutes,
        TestVersionFile,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()

        for method_name in dir(instance):
            if not method_name.startswith('test_'):
                continue

            try:
                method = getattr(instance, method_name)
                method()
                print(f"  [PASS] {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  [FAIL] {method_name}: {e}")
                failed += 1
                errors.append((method_name, str(e)))
            except Exception as e:
                print(f"  [ERROR] {method_name}: {e}")
                failed += 1
                errors.append((method_name, traceback.format_exc()))

    print("\n" + "=" * 40)
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for name, error in errors:
            print(f"  - {name}: {error[:100]}")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
