# Shastra Proof Yard - Update System

## Overview

This module implements a professional auto-update system similar to Chrome, Discord, and Steam.

**Supports three update sources (in priority order):**
1. **USB/Pendrive updates** (🥇 Highest priority) - For offline/defence environments
2. **GitHub Releases API** - For production private repository updates
3. **Local/LAN updates** - For testing and development

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UPDATE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  UPDATE SOURCES (checked in priority order):                        │
│                                                                     │
│  1️⃣ USB/PENDRIVE (Highest Priority - NO INTERNET REQUIRED)          │
│     /media/<user>/<USB>/SHASTRA_UPDATE/                            │
│                                                                     │
│  2️⃣ GITHUB RELEASES (Requires Token + Internet)                     │
│     github.com/<owner>/<repo>/releases                              │
│                                                                     │
│  3️⃣ LOCAL/LAN (Development/Testing)                                 │
│     ./version.json + file:// or http://                             │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  USB takes priority over GitHub.                                    │
│  This ensures updates work even in offline/defence environments.    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ USB/Pendrive Updates (Offline Mode)

This is the **preferred method for defence/military environments** where internet access is not available.

### USB Folder Structure (MUST MATCH EXACTLY)

```
USB_DRIVE/
└── SHASTRA_UPDATE/
    ├── version_linux.json      ← Version metadata (Linux)
    ├── version_windows.json    ← Version metadata (Windows)  
    ├── Shastra_App_1.1.0       ← Linux binary (no extension)
    ├── Shastra_App_1.1.0.exe   ← Windows binary
    └── checksum.sha256         ← Optional SHA256 checksum
```

### USB Mount Points Scanned

| Platform | Locations Checked |
|----------|-------------------|
| **Linux** | `/media/<username>/*`, `/mnt/*`, `/run/media/<username>/*` |
| **Windows** | `D:\` through `Z:\` (removable drives only) |
| **macOS** | `/Volumes/*` (excluding Macintosh HD) |

### USB Update Flow

```
User inserts USB with SHASTRA_UPDATE folder
              ↓
User launches Shastra app
              ↓
App auto-scans USB mount points
              ↓
Found SHASTRA_UPDATE? → Load version_linux.json
              ↓
Version > current? → Show Update Dialog
              ↓
┌──────────────────────────────────────┐
│ 🚀 A New Version is Available!       │
│                                      │
│ Current: v1.0.0 → New: v1.1.0        │
│ 💾 Update source: USB Drive (Offline)│
│ 📍 Drive: SHASTRA_USB               │
│                                      │
│         [Skip] [Update Now]          │
└──────────────────────────────────────┘
              ↓
User clicks "Update Now"
              ↓
App copies binary from USB → temp/
              ↓
updater replaces app → restarts
              ↓
✅ Done! USB can be removed
```

### Preparing a USB Update (Developer Guide)

```bash
# 1. Build the new binary
pyinstaller --onefile --name "Shastra_App_1.1.0" main.py

# 2. Create update folder on USB
mkdir -p /media/$USER/MY_USB/SHASTRA_UPDATE

# 3. Copy binary
cp dist/Shastra_App_1.1.0 /media/$USER/MY_USB/SHASTRA_UPDATE/

# 4. Copy version file
cp version_linux.json /media/$USER/MY_USB/SHASTRA_UPDATE/

# 5. Optional: Generate checksum for integrity verification
cd /media/$USER/MY_USB/SHASTRA_UPDATE
sha256sum Shastra_App_1.1.0 > checksum.sha256
```

### version_linux.json (USB)

```json
{
    "version": "1.1.0",
    "channel": "stable",
    "mandatory": false,
    "min_supported_version": "1.0.0",
    "release_date": "2025-12-26",
    "download": {
        "asset_name": "Shastra_App_1.1.0",
        "sha256": ""
    },
    "changelog": [
        "Added USB offline update support",
        "Bug fixes and improvements"
    ],
    "update_notes": "This update can be installed offline via USB."
}
```

---

## 2️⃣ GitHub Releases Updates (Online Mode)

```
│                                                                     │
│  Production machines never see source code.                        │
└─────────────────────────────────────────────────────────────────────┘
```

User clicks "Help" → "Check for Updates..."
                ↓
┌─────────────────────────────────────────────────────┐
│  Is token saved in OS Keyring/Credential Manager?   │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
       YES                        NO
        ↓                          ↓
  Use saved token        ┌─────────────────────────┐
        ↓                │  GitHubTokenDialog      │
        │                │  ┌───────────────────┐  │
        │                │  │ 🔐 Token Required │  │
        │                │  │ [ghp_xxxxxxxx   ] │  │
        │                │  │ ☑ Remember token  │  │
        │                │  │ [Validate & Go]   │  │
        │                │  └───────────────────┘  │
        │                └────────────┬────────────┘
        │                             ↓
        │                 Token valid? (API check)
        │                      │
        │           ┌──────────┴──────────┐
        │          YES                    NO
        │           ↓                      ↓
        │     Save to Keyring       Show error ❌
        │           ↓                "Invalid token"
        └─────→ Check GitHub API for updates
                        ↓
              Update available?
                   │
         ┌─────────┴─────────┐
        YES                  NO
         ↓                    ↓
  ┌──────────────────┐   Show "You're up to date"
  │  UpdateDialog    │
  │  v1.2.0 → v1.3.0 │
  │  [Update Now]    │
  └──────────────────┘

```
### Local Update Flow

```
User opens Shastra.exe
      ↓
Shastra checks local version.json
      ↓
New version available?
      ↓
User clicks "Update"
      ↓
Shastra downloads new exe from file:// or http://
      ↓
Shastra launches updater.exe → Shastra exits
      ↓
updater.exe replaces Shastra.exe → restarts
```

### GitHub Releases Update Flow

```
User opens Shastra.exe
      ↓
GitHub token required? → Prompt user for token
      ↓
Fetch latest release via GitHub API
      ↓
Download version.json from release assets
      ↓
New version available?
      ↓
User clicks "Update"
      ↓
Download exe asset (authenticated)
      ↓
Shastra launches updater.exe → Shastra exits
      ↓
updater.exe replaces Shastra.exe → restarts
```

## Files

| File | Purpose |
|------|---------|
| `update_checker.py` | Core update logic - version checking, GitHub API, downloading |
| `update_dialog.py` | PyQt5 dialogs for updates and token input |
| `updater.py` | External updater - compiled to `updater.exe` |
| `__init__.py` | Module exports |

## GitHub Releases Setup

### 1. Create Release-Only Private Repo

On GitHub:
- **Repo name**: `shastra-releases`
- **Visibility**: Private
- **Contains**: NOTHING except Releases (no code)

### 2. Create Fine-Grained Personal Access Token

1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Create new token:
   - **Name**: `Shastra Update Token`
   - **Repository access**: Only select `shastra-releases`
   - **Permissions**: Contents → Read
3. Copy the token (starts with `ghp_` or `github_pat_`)

### 3. Release Asset Layout

For each release (e.g., v1.1.0), upload these assets:
- `Shastra_1.1.0.exe` - The application executable
- `version.json` - Version metadata

### 4. version.json for GitHub Releases

```json
{
  "version": "1.1.0",
  "channel": "stable",
  "mandatory": false,
  "min_supported_version": "1.0.0",
  "download": {
    "asset_name": "Shastra_1.1.0.exe",
    "sha256": "abc123..."
  },
  "changelog": [
    "Improved detection stability",
    "Bug fixes"
  ]
}
```

> ⚠️ **Note**: No hardcoded URL needed! URLs are resolved dynamically via GitHub API.

## Configuration

Update these values in `update_checker.py`:

```python
GITHUB_OWNER = "army-shastra"      # Your GitHub org/user
GITHUB_REPO = "shastra-releases"   # Your releases repo name
```

## version.json Structure (Local Updates)

```json
{
  "app_name": "Shastra Proof Yard",
  "version": "1.1.0",
  "build_number": 110,
  "release_date": "2025-12-25",
  "release_channel": "stable",
  "mandatory": false,
  "min_supported_version": "1.0.0",
  "download": {
    "url": "file:///path/to/Shastra_1.1.0.exe",
    "size_bytes": 52428800,
    "sha256": "abc123..."
  },
  "changelog": [
    {
      "version": "1.1.0",
      "date": "2025-12-25",
      "changes": [
        "New feature: ...",
        "Bug fix: ..."
      ]
    }
  ]
}
```

## Building

### Build the main application

```bash
pyinstaller --onefile --windowed --name "Shastra_App" \
  --add-data "version.json;." \
  --add-data "assets;assets" \
  main.py
```

### Build the updater

```bash
cd update_system
pyinstaller --onefile --noconsole --name "updater" updater.py
```

### Final distribution folder

```
Shastra/
├── Shastra_App.exe    # Main application
├── updater.exe        # External updater
├── version.json       # Version metadata (for local updates)
├── assets/            # Application assets
└── temp/              # Created during updates (auto-cleaned)
```

## Usage in PyQt5 App

### GitHub Releases (Production)

```python
from update_system import check_update_on_startup, show_update_dialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... setup UI ...
        
        # Check for updates from GitHub (silent on startup)
        check_update_on_startup(self, use_github=True, silent=True)
    
    def manual_update_check(self):
        # Manual check - will prompt for token if needed
        check_update_on_startup(self, use_github=True, silent=False)
```

### Local Updates (Testing/Offline)

```python
from update_system import check_update_on_startup

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Check for updates from local version.json
        check_update_on_startup(self, silent=True)
```

### Advanced Usage - GitHub Token Management

```python
from update_system import (
    UpdateChecker, UpdateDialog, GitHubTokenDialog,
    set_github_token, is_github_token_set, validate_github_token
)

# Prompt for token
def setup_github_auth(parent):
    dialog = GitHubTokenDialog(parent)
    if dialog.exec_() == QDialog.Accepted:
        print("Token validated and saved!")
        return True
    return False

# Check for updates with GitHub
def check_github_updates(parent):
    if not is_github_token_set():
        if not setup_github_auth(parent):
            return
    
    checker = UpdateChecker(use_github=True)
    update_info = checker.check()
    
    if update_info:
        dialog = UpdateDialog(update_info, parent=parent)
        dialog.exec_()
    else:
        print("No updates available")

# Validate a token programmatically
is_valid, message = validate_github_token("ghp_your_token_here")
if is_valid:
    set_github_token("ghp_your_token_here")
```

### Environment Variable (Alternative Token Storage)

Instead of prompting for token, you can set it via environment variable:

```bash
# Linux/macOS
export SHASTRA_GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Windows
set SHASTRA_GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

The system will automatically use this token if available.
```

## Update Hosting Options

| Option | Use Case | Token Required |
|--------|----------|----------------|
| Local `file://` | Testing/Air-gapped systems | No |
| Internal LAN `http://` | Corporate/Defence networks | No |
| GitHub Releases (Private) | Production releases | Yes |
| HTTPS cloud (S3, Azure) | Public releases | No |

## Security Features

- **SHA256 verification**: Downloaded files are verified against hash
- **Backup before replace**: Original exe backed up before update
- **Automatic rollback**: Restores backup if update fails
- **Logging**: All operations logged to `updater.log`
- **Token validation**: GitHub tokens validated before use
- **Optional token storage**: Users can choose to remember tokens

## Token Security Best Practices

1. **Fine-grained tokens only**: Only grant read access to the releases repo
2. **No source access**: Token should NOT have access to source code repo
3. **Expiration**: Set token expiration (recommended: 90 days)
4. **User choice**: Let users decide if they want to save the token
5. **Environment variable**: For automated systems, use `SHASTRA_GITHUB_TOKEN`

## Troubleshooting

### GitHub token validation fails

- Check token hasn't expired
- Verify token has "Contents: Read" permission for the releases repo
- Ensure the repo name matches `GITHUB_REPO` in code

### "Repository not found" error

- Verify `GITHUB_OWNER` and `GITHUB_REPO` are correct
- Check token has access to the repository
- Ensure the repository exists

### "No releases found" error

- Create at least one release in the releases repo
- Upload `version.json` and the exe as release assets

### Update fails with "file locked"

The main application must exit completely before the updater can replace the exe. Increase `MAX_WAIT_SECONDS` in `updater.py` if needed.

### Antivirus blocks update

Some antivirus software may block the updater. Add an exception for:
- `Shastra_App.exe`
- `updater.exe`
- The installation folder

### Download fails

Check:
1. Network connectivity
2. GitHub API is accessible (not blocked by firewall)
3. Token is valid and has correct permissions
4. Release assets exist and are named correctly
