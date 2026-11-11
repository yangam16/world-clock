# Installation and desktop launchers

[Project home](../README.en.md) · [简体中文](installation.zh-CN.md)

## Requirements and installation

Tested on one Ubuntu 22.04 **X11** desktop. Requires Python 3.10+, GTK 3, and the Ubuntu AppIndicators extension.

Install system dependencies once:

```bash
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 gir1.2-ayatanaappindicator3-0.1 tzdata gnome-shell-extension-appindicator
```

In **Extensions**, enable **Ubuntu AppIndicators**. If the indicator service is unavailable, the app shows an error and exits so a click-through window cannot lose its control menu.

Clone, check dependencies, and install the desktop shortcut:

```bash
git clone https://github.com/yangam16/world-clock.git
cd world-clock
./run.sh --check
python3 install.py --desktop
```

`--check` verifies dependency imports only. It does not validate rendering, the tray service, or pointer interaction. The per-user installer does not require sudo; system dependencies must already be installed.

The installer copies the app to `$XDG_DATA_HOME/world-clock` (normally `~/.local/share/world-clock`), creates an application-menu entry, and installs a `~/.local/bin/world-clock` command. It preserves existing notes and settings. Use `python3 install.py` if you want only the application-menu entry, without a desktop shortcut.

## Using the .desktop file after cloning

### 1. Generate your local desktop shortcut

From the cloned project directory, run once:

```bash
python3 install.py --desktop
```

The installer detects your desktop directory, including localized directory names, and creates launchers pointing to the installed app using an absolute path.

| File | Purpose |
|---|---|
| `assets/world-clock.desktop` in the clone | A template containing `Exec=world-clock`; the installer replaces it with the actual installation path |
| `~/.local/share/applications/world-clock.desktop` | The GNOME application-menu entry |
| `$(xdg-user-dir DESKTOP)/world-clock.desktop` | The double-clickable desktop shortcut |

These locations assume the default XDG data directory. Do not double-click the repository template directly or merely copy that template to your desktop: it has not been configured for your installation, and `world-clock` may not be on PATH. Run the installer instead; no manual `Exec` editing is needed.

### 2. Allow launching and open the app

1. Return to your Ubuntu desktop and find **World Clock**.
2. If it looks like a text file or is marked untrusted, right-click it and select **Allow Launching**.
3. Double-click it to start the app. A terminal is no longer needed for everyday use.
4. Alternatively, press **Super** and search for **World Clock** in the application menu. You can add the application to Favorites for access from the Dock.

The installer sets executable permissions and attempts to mark the shortcut trusted. If **Allow Launching** is unavailable, open the file's **Properties → Permissions** in the file manager and enable **Allow executing file as program**, then return to the desktop. If no file icons appear on the desktop at all, check that **Desktop Icons NG (DING)** is enabled in Extensions.

### 3. Use the control menu

Look for the clock icon in the **top-right Ubuntu system bar**. Its menu provides time zones, notes, language selection, and Quit. Clock windows have no title bar and default to click-through. Repeated shortcut launches do not create another instance.

### Update or recreate shortcuts

Quit the running app from its top-bar menu. In the cloned directory, run:

```bash
git pull --ff-only
python3 install.py --desktop
```

Double-click the desktop shortcut again. Installation updates the app and launchers while preserving the installed draft and user settings. Launchers point to the installed copy and do not depend on the clone's location.

### Optional: run from source

Use `./run.sh` in the clone to run directly from source. Its draft is the clone's `note.txt`; the desktop-installed app uses the installed program directory instead. Quit the old instance and back up the draft before switching between these copies; copy the draft to the target program directory if needed.

