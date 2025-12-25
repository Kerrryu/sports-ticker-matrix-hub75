# OTA Updates - Over-The-Air Update System

## Overview

The Sports Ticker includes a complete Over-The-Air (OTA) update system that allows you to push software updates remotely without physical access to the device.

## Features

### Core Capabilities

✅ **Remote Updates**
- Push updates from GitHub releases
- Automatic daily update checks
- Manual update via web interface
- No physical access required

✅ **Safety & Reliability**
- Automatic backup before updates
- Checksum verification (SHA256)
- Rollback on boot failure
- Crash detection and recovery

✅ **Configuration Management**
- All settings via web interface
- Configuration preserved across updates
- Backup and restore
- Factory reset option

✅ **Monitoring**
- Update history and logs
- System health reporting
- Error tracking
- Version information

## User Guide

### Checking for Updates

**Via Web Interface:**
1. Open `http://DEVICE_IP/`
2. Navigate to "Updates" section
3. Click "Check for Updates"
4. If update available, see changelog

**Automatic Checks:**
- Device checks once per day automatically
- Non-breaking updates may auto-install
- Breaking changes require manual approval

### Installing Updates

**Manual Installation:**
1. Click "Check for Updates"
2. Review changelog
3. Click "Install Update"
4. Confirm installation
5. Device restarts automatically
6. Wait 30 seconds for restart

**What Happens:**
```
1. Backup current version (30 sec)
2. Download update (1-2 min)
3. Verify integrity (10 sec)
4. Install new code (30 sec)
5. Restart device (30 sec)
6. Verify boot success (1 min)
───────────────────────────
Total time: ~4-5 minutes
```

### Rolling Back Updates

If an update causes issues:

1. Open web interface
2. Navigate to "Updates" section
3. Click "Rollback to Previous Version"
4. Confirm rollback
5. Device restarts with previous version

**Automatic Rollback:**
- If device fails to boot 3 times
- Automatic rollback triggered
- Previous version restored
- User notified via display

### Update History

View complete update history:
1. Go to "Updates" section
2. Click "Load History"
3. See all past updates with timestamps

## Developer Guide

### Setting Up Releases

**Prerequisites:**
```bash
# 1. GitHub repository with your code
# 2. GitHub Actions enabled
# 3. Version tagging workflow
```

**Creating a Release:**

```bash
# 1. Make your changes
git add .
git commit -m "Fix: ESPN API parsing bug"

# 2. Update version in code
# Edit version.json or __version__ variable

# 3. Tag the release
git tag v1.2.0 -m "Release 1.2.0 - API fix"

# 4. Push with tags
git push origin main --tags

# 5. GitHub Action automatically:
#    - Creates release package
#    - Generates checksums
#    - Publishes release
```

**Version Numbering:**
```
Format: MAJOR.MINOR.PATCH

MAJOR: Breaking changes (requires manual update)
MINOR: New features (backward compatible)
PATCH: Bug fixes (auto-installable)

Examples:
1.0.0 → 1.0.1  (Bug fix)
1.0.1 → 1.1.0  (New feature: weather display)
1.1.0 → 2.0.0  (Breaking: config format changed)
```

### Release Checklist

Before creating a release:

```
□ All tests passing
□ Changelog updated
□ Version number incremented
□ Breaking changes documented
□ Tested on actual hardware
□ Backup/rollback tested
□ Configuration migration tested (if needed)
□ Update documentation
□ Create git tag
□ Push to GitHub
```

### Update Server Configuration

**GitHub Releases (Recommended):**

```python
# In your code
UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/sports-ticker/main/releases/version.json"

# version.json format:
{
  "version": "1.2.0",
  "released": "2024-12-25T10:00:00Z",
  "changelog": "Fixed ESPN API parsing for playoff games",
  "download_url": "https://github.com/USERNAME/sports-ticker/releases/download/v1.2.0/sports-ticker-v1.2.0.tar.gz",
  "checksum": "sha256:abc123def456...",
  "size_bytes": 45678,
  "breaking_changes": false,
  "min_required": "1.0.0"
}
```

**Custom Server:**

```python
# Simple Flask server
from flask import Flask, jsonify, send_file

app = Flask(__name__)

@app.route('/api/version')
def get_version():
    return jsonify({
        "version": "1.2.0",
        "download_url": "https://yourserver.com/downloads/v1.2.0.tar.gz",
        "changelog": "Bug fixes and improvements"
    })

@app.route('/downloads/<filename>')
def download(filename):
    return send_file(f'releases/{filename}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Testing Updates

**Local Testing:**

```bash
# 1. Start local update server
python update_server.py

# 2. Point device to local server
UPDATE_URL = "http://192.168.1.100:5000/api/version"

# 3. Trigger update from web interface

# 4. Verify:
#    - Download works
#    - Installation succeeds
#    - Device boots properly
#    - Configuration preserved
```

**Staged Rollout:**

```python
# Test on one device first
{
  "version": "1.2.0",
  "rollout_percentage": 0  # Deploy to 0% (testing only)
}

# After testing, gradually increase
rollout_percentage: 10  # 10% of devices
rollout_percentage: 50  # 50% of devices  
rollout_percentage: 100 # All devices
```

### Debugging Update Issues

**Common Issues:**

**Update won't download:**
```
Check:
□ Internet connection
□ Update URL accessible
□ Enough free space (need ~500KB)
□ Check logs: /logs/ota_update.log
```

**Checksum verification fails:**
```
Check:
□ Download completed fully
□ Checksum in version.json correct
□ No network interruptions
□ Try re-downloading
```

**Installation fails:**
```
Check:
□ Enough free space
□ File permissions correct
□ No filesystem errors
□ Check error in logs
```

**Device won't boot after update:**
```
Automatic rollback should trigger after 3 failed boots.
If not:
1. Power cycle device
2. Wait 2 minutes
3. Should rollback automatically
4. If still failing, reflash MicroPython
```

**Configuration lost after update:**
```
Check:
□ Backup was created before update
□ Restore function ran after update
□ /backups/user_config.json exists
□ Manually restore from backup if needed
```

### Advanced Features

#### Custom Update Logic

```python
# In src/ota/updater.py

class CustomUpdater(OTAUpdater):
    def should_auto_install(self, update_info):
        """Custom logic for auto-installation."""
        
        # Only auto-install patches
        if update_info['version'].endswith('.1'):
            return True
        
        # Only during maintenance window (2-4 AM)
        hour = time.localtime()[3]
        if 2 <= hour < 4:
            return True
        
        # Only if device has been running stable
        if self.get_uptime() > 86400:  # 24 hours
            return True
        
        return False
```

#### Pre/Post Update Hooks

```python
class UpdateHooks:
    def pre_update(self):
        """Run before update installation."""
        # Stop active tasks
        # Close connections
        # Flush logs
        # Notify monitoring system
        pass
    
    def post_update(self):
        """Run after successful update."""
        # Migrate configuration if needed
        # Restart services
        # Send success notification
        # Clear caches
        pass
    
    def on_rollback(self):
        """Run after rollback."""
        # Log rollback reason
        # Notify developer
        # Restore services
        pass
```

#### Update Notifications

```python
# Notify when update available
def notify_update_available(update_info):
    """Display notification on screen."""
    display.clear()
    draw_text(display, 10, 10, "UPDATE", (255, 255, 0))
    draw_text(display, 10, 20, f"v{update_info['version']}", (255, 255, 255))
    draw_text(display, 10, 30, "available", (200, 200, 200))
    display.show()

# Or send email/SMS notification
def email_notification(update_info):
    """Send email about available update."""
    # Use SMTP or email service API
    pass
```

## Architecture

### Update Flow Diagram

```
┌──────────────────────────────────────────────────────┐
│                  GitHub Release                      │
│                   v1.2.0.tar.gz                      │
│                   version.json                       │
│                   checksum.txt                       │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ HTTPS
                     ▼
┌──────────────────────────────────────────────────────┐
│              Sports Ticker Device                    │
│  ┌────────────────────────────────────────────────┐ │
│  │  1. Check for Update                           │ │
│  │     GET version.json                           │ │
│  │     Compare versions                           │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │  2. Download Update                            │ │
│  │     GET .tar.gz file                           │ │
│  │     Show progress                              │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │  3. Verify Integrity                           │ │
│  │     Calculate SHA256                           │ │
│  │     Compare with checksum.txt                  │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │  4. Backup Current Version                     │ │
│  │     Copy to /backups/vX.X.X/                   │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │  5. Install Update                             │ │
│  │     Extract files                              │ │
│  │     Replace old code                           │ │
│  │     Update version.json                        │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │  6. Restart Device                             │ │
│  │     machine.reset()                            │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │  7. Verify Boot                                │ │
│  │     Increment boot counter                     │ │
│  │     If 3 failures → Rollback                   │ │
│  │     Else → Success, reset counter              │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### File Structure

```
/
├── src/
│   └── ota/
│       ├── updater.py          # Main OTA logic
│       ├── downloader.py       # HTTP download with resume
│       ├── verifier.py         # Checksum validation
│       └── rollback.py         # Rollback mechanism
│
├── backups/                    # Previous versions
│   ├── v1.0.0/
│   ├── v1.1.0/
│   └── user_config.json        # User settings backup
│
├── logs/
│   └── ota_update.log          # Update history
│
├── version.json                # Current version info
└── boot_count.txt              # Boot failure tracking
```

## Security

### Best Practices

**1. Always use HTTPS:**
```python
# ✓ Secure
UPDATE_URL = "https://github.com/user/repo/releases/..."

# ✗ Insecure - can be intercepted
UPDATE_URL = "http://example.com/updates/..."
```

**2. Verify checksums:**
```python
# Always verify before installation
if not verify_checksum(file, expected_checksum):
    raise SecurityError("Checksum mismatch!")
```

**3. Validate version strings:**
```python
# Prevent injection attacks
def validate_version(version):
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        raise ValueError("Invalid version format")
```

**4. Limit update sources:**
```python
# Only allow updates from trusted domains
ALLOWED_DOMAINS = [
    'github.com',
    'yourserver.com'
]

def validate_url(url):
    domain = urlparse(url).netloc
    if domain not in ALLOWED_DOMAINS:
        raise SecurityError("Untrusted update source")
```

### Signed Updates (Advanced)

For production deployments, consider signing updates:

```python
# Server-side: Sign update with private key
openssl dgst -sha256 -sign private.pem -out signature.bin update.tar.gz

# Device-side: Verify with public key
def verify_signature(file, signature, public_key):
    """Verify update was signed by trusted source."""
    # RSA signature verification
    # Prevents unauthorized updates
    pass
```

## Troubleshooting

### FAQ

**Q: How often does it check for updates?**
A: Once per day automatically, or manual via web interface.

**Q: Can I disable automatic updates?**
A: Yes, in config.json set `"auto_updates": false`

**Q: What if an update breaks something?**
A: Automatic rollback after 3 failed boots, or manual rollback via web interface.

**Q: How much space do updates need?**
A: ~500KB for download, plus backup of current version.

**Q: Can I update multiple devices at once?**
A: Yes, all devices check the same update server. Use staged rollout for safety.

**Q: What happens to my configuration?**
A: Automatically backed up before update and restored after.

**Q: Can I see what changed in an update?**
A: Yes, changelog is shown before installation and in update history.

**Q: How do I know if an update installed successfully?**
A: Check version number in web interface, and update history log.

## Best Practices

### For Users

✅ **Do:**
- Check changelog before updating
- Update during low-use times (night)
- Keep device powered during updates
- Verify system works after update
- Keep backup configuration

❌ **Don't:**
- Unplug during update
- Update right before important game
- Skip reading changelog
- Ignore failed update notifications

### For Developers

✅ **Do:**
- Test updates thoroughly before release
- Use semantic versioning
- Write detailed changelogs
- Test rollback functionality
- Use staged rollout for major updates
- Monitor update success rates

❌ **Don't:**
- Push untested updates
- Skip version increments
- Break configuration compatibility without migration
- Force updates without user consent
- Ignore update failures

## Monitoring

### Update Metrics

Track these metrics for update health:

```
- Update check frequency
- Download success rate
- Installation success rate
- Rollback frequency
- Average update time
- Device uptime after update
```

### Logging

```python
# Update log format
{
    "timestamp": "2024-12-25T10:00:00Z",
    "action": "update_installed",
    "from_version": "1.1.0",
    "to_version": "1.2.0",
    "success": true,
    "duration_seconds": 245
}
```

## Future Enhancements

**Planned features:**

- Delta updates (only changed files)
- Compressed updates (smaller downloads)
- Update scheduling (specific times)
- Update channels (stable/beta)
- Remote diagnostics
- A/B partition updates
- Partial rollbacks
- Update analytics dashboard

## Support

**If you need help:**

1. Check logs: `/logs/ota_update.log`
2. Try manual update via web interface
3. Attempt rollback
4. Check GitHub Issues
5. Contact developer

**Include in support request:**
- Current version
- Target version
- Error messages
- Update log
- Device info

## Conclusion

The OTA update system provides:

✅ Safe, reliable remote updates
✅ Automatic recovery from failures
✅ Configuration preservation
✅ Complete update history
✅ User-friendly interface
✅ Developer-friendly release process

Your sports ticker can now be updated and maintained remotely, ensuring it always has the latest features and bug fixes without requiring physical access.
