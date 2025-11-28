# Upgrade Guide

## Upgrading the Parking Heater Integration

### For HACS Users (When Available)

1. Go to **HACS** → **Integrations**
2. Find "Parking Heater BLE"
3. Click **Update** if available
4. **Restart Home Assistant**
5. Integration will auto-reload with new code

### For Manual Installation Users

#### Method 1: Simple Replace (Recommended)

1. **Download** the latest version from GitHub
2. **Stop Home Assistant** (optional but safer)
3. **Replace** the `custom_components/parking_heater` folder
4. **Restart Home Assistant**
5. Integration will load with updated code

#### Method 2: Git Pull (If You Cloned the Repo)

```bash
cd /path/to/your/custom_components/parking_heater
git pull origin main
```

Then **restart Home Assistant**.

#### Method 3: In-Place Update (Quick Fix Like Now)

For quick bug fixes without full restart:

1. **Replace** only the changed files in `custom_components/parking_heater/`
2. Go to **Settings** → **System** → **Restart**
3. Or reload just the integration:
   - **Settings** → **Devices & Services** → **Parking Heater BLE** → **⋮** → **Reload**

---

## After Upgrading

### Check for Breaking Changes

1. Read the [CHANGELOG.md](CHANGELOG.md) for your version
2. Look for "BREAKING CHANGE" notices
3. Update automations if needed

### Verify Integration Still Works

1. Go to **Settings** → **Devices & Services**
2. Find **Parking Heater BLE**
3. Check device status (should show "Connected" or device info)
4. Test basic controls:
   - Turn on/off
   - Change temperature
   - Adjust fan speed

### If Something Breaks

1. **Check logs**: Settings → System → Logs
2. **Try reloading**: Settings → Devices & Services → ⋮ → Reload
3. **Remove & re-add**: Delete device and add again (settings preserved)
4. **Full reinstall**: Remove integration, delete folder, reinstall

---

## Version Checking

Currently, the integration doesn't have automatic update notifications. You can:

1. **Watch the GitHub repo** for releases
2. **Check manually** periodically
3. **Subscribe to releases** on GitHub

### Check Current Version

Your installed version is in:
```
custom_components/parking_heater/manifest.json
```

Look for the `"version"` field.

---

## Preserving Your Settings

### What's Preserved During Updates

✅ Device configuration (MAC address, name)
✅ Entity IDs
✅ Automations
✅ Dashboard cards
✅ History data

### What Might Need Reconfiguration

⚠️ New features (need to configure)
⚠️ Breaking changes (check changelog)
⚠️ Protocol changes (might need device re-pairing)

---

## Downgrading (If Needed)

If an update causes issues:

1. **Find the previous version** on GitHub releases
2. **Download** that version
3. **Replace** the `custom_components/parking_heater` folder
4. **Restart Home Assistant**

Or use git:
```bash
cd /path/to/parking_heater
git checkout <previous-version-tag>
```

---

## Best Practices

### Before Upgrading

1. ✅ **Backup** your Home Assistant configuration
2. ✅ **Read** the changelog
3. ✅ **Test** on a non-critical time
4. ✅ **Note** current version number

### During Upgrade

1. ✅ **Stop** any running automations (optional)
2. ✅ **Replace** files completely (don't mix versions)
3. ✅ **Restart** Home Assistant fully

### After Upgrade

1. ✅ **Check logs** for errors
2. ✅ **Test** all heaters
3. ✅ **Verify** automations work
4. ✅ **Report** any issues on GitHub

---

## Automatic Updates (Future)

This integration may support automatic updates through:

- **HACS** - Automatic update notifications
- **Home Assistant Cloud** - Update checking (if submitted)
- **GitHub Releases** - Version tracking

---

## Emergency Rollback

If the integration completely breaks:

1. **Remove integration**: Settings → Devices & Services → Delete
2. **Delete folder**: `custom_components/parking_heater/`
3. **Restart Home Assistant**
4. **Install working version**
5. **Re-add devices** (MAC addresses will be remembered)

---

## Getting Help

If you have upgrade issues:

1. Check [CHANGELOG.md](CHANGELOG.md) for breaking changes
2. Review [FAQ.md](FAQ.md) troubleshooting section
3. Enable debug logging (see below)
4. Open GitHub issue with logs

### Debug Logging for Upgrade Issues

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.parking_heater: debug
```

Then restart and check logs.

---

## Version History

See [CHANGELOG.md](CHANGELOG.md) for complete version history and upgrade notes.
