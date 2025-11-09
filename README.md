# Focus Dock

A powerful Windows application designed to help you stay focused by blocking distracting websites and applications during timed work sessions

## 📥 Quick Start

**Option 1: Download Pre-built Executable** (Recommended)

1. Download FocusDock.zip from [Latest Release](https://github.com/Yang-Raymond/HttpHacks/releases/latest)
2. Unzip it anywhere
3. Run `app.exe`

**Option 2: Run from Source**

1. Install Python 3.8+
2. Run `python -m venv .venv`
3. Run `.venv\Scripts\Activate.ps1`
4. Run `pip install PyQt6 psutil pyinstaller`
5. Run `pyinstaller --onefile --name app --add-data "blocklist.json;." --add-data "tasks.json;." app.py`
6. Run `pyinstaller --onefile --name mvp_blocker --add-data "blocklist.json;." mvp_blocker.py`
7. cd /dist folder
8. Run `app.exe`.

⚠️ **Windows 10/11 Required** - PAC configuration and app blocking only work on Windows

## Features

### Timer

- **Customizable countdown timer** with hours, minutes, and seconds
- **Visual progress indicator** with circular progress arc
- **Click-to-edit time** - Click on the timer to adjust duration

### Website & App Blocking

- **Selective blocking** - Choose which websites and apps to block
- **Toggle all** - Quickly enable/disable all blocks at once
- **HTTP/HTTPS support** - Blocks websites via local proxy (HTTP & SOCKS5)
- **App blocking** - Automatically terminates blocked applications
- **Pattern matching** - Use wildcards to block entire domains (e.g., `*.facebook.com`)

### Task Management

- **Built-in task list** to track your goals
- **Add/complete tasks** with descriptions
- **Auto-delete** - Completed tasks automatically disappear
- **Persistent storage** - Tasks saved to `tasks.json`

### Advanced Blocking System

- **PAC (Proxy Auto-Configuration)** - System-wide blocking via Windows proxy settings
- **Multi-layer blocking** - HTTP proxy (port 3128) + SOCKS5 proxy (port 1080)
- **App termination modes**:
  - **Polite mode**: Graceful termination
  - **Strict mode**: Force kill if app doesn't close
- **Real-time monitoring** - Continuous scanning for blocked apps

## 🚀 Getting Started

### System Requirements

- **Windows 10 or Windows 11** (Required for PAC configuration and app blocking)
- **Administrator privileges** (to modify Windows proxy settings)

---

### Option 1: Run Pre-built Executable (Recommended for Users)

**No installation required!** Just download and run.

1. **Download the application**

   - Get `FocusDock.zip` from [GitHub Releases](https://github.com/Yang-Raymond/HttpHacks/releases/latest)
   - Extract to any folder (e.g., `C:\FocusDock\`)

2. **Verify extracted files**

   ```
   FocusDock/
   ├── app.exe           # Main application
   ├── mvp_blocker.exe   # Blocking engine
   ├── blocklist.json    # Website/app configuration
   └── tasks.json        # Task list
   ```

3. **Launch the app**
   - Double-click `app.exe`
   - Done! Start your first focus session.

---

### Option 2: Run from Source (For Developers)

**What you need to install:**

- **Python 3.8 or higher** ([Download here](https://www.python.org/downloads/))
- **PyQt6** - GUI framework
- **psutil** - Process monitoring library

**Setup steps:**

1. **Install Python**

   - Download from [python.org](https://www.python.org/downloads/)
   - ⚠️ **Important:** Check "Add Python to PATH" during installation

2. **Clone the repository**

   ```bash
   git clone https://github.com/Yang-Raymond/HttpHacks.git
   cd HttpHacks
   ```

3. **Install required packages**

   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   # Use this command:
   ```bash
   pip install PyQt6 psutil pyinstaller
   ```

   # If that doesn't work, try:
   ```bash
   python -m pip install PyQt6 psutil pyinstaller
   ```

4. **Compile the application**
   a. Build the main application:
      ```bash
      pyinstaller --onefile --name app --add-data "blocklist.json;." --add-data "tasks.json;." app.py
      ```
      
   b. Build the blocker engine:
      ```bash
      pyinstaller --onefile --name mvp_blocker --add-data "blocklist.json;." mvp_blocker.py
      ```
      
   > **Troubleshooting:** If `pyinstaller` command is not found, use `python -m PyInstaller` instead

5. **Move to the correct directory**
   ```bash
   cd dist
   ```

6. **Copy and Paste "blocklist.json" and "tasks.json" to dist folder**

7. **Run the application**
   ```bash
   app.exe
   ```
---

## Usage

### Starting a Focus Session

1. **Add websites/apps to block**

   - Click "Add website" or "Add app" in the left panel
   - Enter the website name and URL patterns (e.g., `facebook.com, *.facebook.com`)
   - For apps, enter the executable name (e.g., `discord`, `steam`)

2. **Toggle blocking**

   - Use individual toggles to enable/disable specific blocks
   - Use "Toggle All" to quickly enable/disable everything

3. **Set your timer**

   - Click on the timer display
   - Scroll or type to set hours, minutes, and seconds
   - Click "OK" to confirm

4. **Start focusing**

   - Click the "Focus" button
   - Blocked websites and apps will be inaccessible during the session
   - Click "Stop" to end the session early

5. **Track your tasks**
   - Add tasks using the "+" button in the right panel
   - Check off tasks as you complete them
   - Completed tasks automatically disappear

### Configuration Files

#### `blocklist.json`

Stores website and app blocking configuration:

```json
{
  "websites": {
    "Facebook & Meta": {
      "blocked": true,
      "apps": "",
      "urls": ["*.facebook.com", "facebook.com", "*.instagram.com"]
    },
    "Discord": {
      "blocked": false,
      "apps": "discord*",
      "urls": ["discord.com", "*.discord.com"]
    }
  }
}
```

#### `tasks.json`

Stores your task list:

```json
{
  "tasks": [
    {
      "label": "Complete project documentation",
      "description": "Write comprehensive README",
      "completed": false
    }
  ]
}
```

## How It Works 🔧

### Website Blocking

1. **PAC Server**: Runs on `localhost:18080` serving proxy auto-config
2. **HTTP Proxy**: Listens on `127.0.0.1:3128` for HTTP/HTTPS traffic
3. **SOCKS5 Proxy**: Listens on `127.0.0.1:1080` as fallback
4. **System Integration**: Modifies Windows registry to enable PAC
5. **Request Filtering**: Matches domains against blocklist and blocks/allows accordingly

### App Blocking

1. **Process Scanning**: Scans running processes every 1-2 seconds
2. **Pattern Matching**: Uses wildcards to match process names (e.g., `discord*`)
3. **Termination**:
   - **Polite mode**: Sends SIGTERM and waits
   - **Strict mode**: Sends SIGTERM, waits 2 seconds, then SIGKILL if needed
4. **System Protection**: Never touches critical system processes

### Logging

All blocking activity is logged to `logs/traffic.log`:

```
2025-11-09 14:30:15 CONNECT facebook.com:443 BLOCK
2025-11-09 14:30:20 APP discord.exe TERMINATE rule=discord*
```

## Architecture

```
HTTPHacks/
├── app.py                 # Main entry point
├── mvp_blocker.py         # Core blocking engine (proxy + app blocker)
├── blocklist.json         # Website/app blocking configuration
├── tasks.json             # Task list storage
├── UI/                    # User interface components
│   ├── main_window.py     # Main application window
│   ├── clock_widget.py    # Timer display and controls
│   ├── task_panel.py      # Task management panel
│   ├── blocklist_manager.py  # Blocklist data management
│   ├── toggle_switch.py   # Custom toggle switch widget
│   ├── website_toggle_widget.py  # Website/app toggle row
│   ├── time_edit_dialog.py  # Time picker dialog
│   ├── scroll_number_widget.py  # Scrollable number input
│   ├── add_website_dialog.py  # Add website dialog
│   ├── add_app_dialog.py  # Add app dialog
│   ├── task_input.py      # Task input form
│   └── task_item.py       # Individual task widget
└── logs/                  # Traffic and blocking logs
```

## Troubleshooting 🔧

### Websites still accessible during focus session

- **Check browser**: Close and reopen browser after starting focus session
- **Clear browser cache**: Some browsers cache DNS/connections
- **Verify PAC**: Check Windows proxy settings (`Internet Options > Connections > LAN Settings`)
- **Try incognito mode**: Private browsing doesn't use cached connections

### Apps keep restarting

- **Check app settings**: Some apps have auto-restart features
- **Administrator rights**: Run the app as administrator for better process control

### PAC not clearing after exit

- Run manually: `python mvp_blocker.py --disable-pac-only`
- Check registry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings`

## Command Line Options 🖥️

The `mvp_blocker.py` script can be run standalone with options:

```bash
python mvp_blocker.py [options]
```

Options:

- `--proxy-port PORT` - HTTP proxy port (default: 3128)
- `--socks-port PORT` - SOCKS5 proxy port (default: 1080)
- `--pac-port PORT` - PAC server port (default: 18080)
- `--enable-pac` - Enable system PAC configuration
- `--disable-pac` - Disable PAC configuration on exit
- `--disable-pac-only` - Only disable PAC and exit
- `--blocklist FILE` - Path to blocklist JSON (default: blocklist.json)
- `--log FILE` - Path to log file (default: logs/traffic.log)
- `--app-mode MODE` - App blocking mode: polite or strict (default: strict)
- `--app-grace SECONDS` - Grace period before force kill (default: 2.0)
- `--app-scan SECONDS` - Process scan interval (default: 2.0)
- `--app-dry-run` - Log only, don't terminate apps

## Development 🛠️

### Adding New Features

1. **UI Components**: Add to `UI/` directory following the existing pattern
2. **Blocklist Manager**: Extend `UI/blocklist_manager.py` for new data operations
3. **Blocking Logic**: Modify `mvp_blocker.py` for proxy/app blocking changes

## Security & Privacy 🔒

- **Local only**: All proxies run on localhost (127.0.0.1)
- **No external connections**: Blocking is done locally
- **No data collection**: Nothing is sent to external servers
- **Open source**: Full code transparency
