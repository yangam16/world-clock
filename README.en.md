# World Clock and Sticky Note

[简体中文](README.md) | [English](README.en.md)

A lightweight GTK 3 desktop tool for Ubuntu 22.04. Display local dates and times in compact horizontal clock windows and keep a plain-text sticky note nearby. Manage everything from the Ubuntu top-bar icon, with live English and Simplified Chinese UI switching.

This project was developed with the help of an LLM. [Issues](https://github.com/yangam16/world-clock/issues) are welcome.

The project's source is licensed under the [MIT license](LICENSE). Third-party dependencies retain their own licenses.

## Features

- Starts with one clock in the system time zone; search for and add more cities.
- Displays `MM/DD`, 24-hour time, time-zone abbreviations such as PST/PDT, and UTC offsets. Handles DST and date changes automatically.
- Separate, compact clock windows or a combined list.
- Bottom alignment on a selected display, using the desktop work area to avoid the Dock.
- Clock click-through, always-on-top, 30%–100% opacity, and saved positions.
- A sticky note with line numbers, editing, dragging, autosave, and independent snapshot exports.

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
| `world-clock.desktop` in the clone | A template containing `Exec=world-clock`; the installer replaces it with the actual installation path |
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

## Clock controls

- **Add time zone…**: search for a city or IANA zone; double-click to add it. Common cities also support Chinese search terms.
- **Separate clock windows**: switch between separate windows and a combined list.
- **Align along bottom (above Dock)**: select a display and arrange clocks within its work area. Additional cities wrap to another row. Use it again after changing display configuration.
- Uncheck **Clock click-through** to drag clock windows or remove a city with ×.
- **Opacity…** and **Always on top** adjust presentation.
- **Language / 语言 → English / 简体中文** switches UI language immediately and remembers the selection. The initial language follows the environment, defaulting to English outside Chinese locales. System controls inside native file dialogs may follow the desktop's language.
- **Quit World Clock** saves the live draft and exits.

Reset to one clock in the system time zone while preserving other preferences:

```bash
./run.sh --local-only
```

At startup, the system zone is resolved from `TZ`, `/etc/localtime`, or `/etc/timezone`, with UTC as a fallback. Saved city selections remain in effect. Changing the system time zone while the app is running does not replace selected cities.

## Sticky note

Enable **Show note** in the top-bar menu. With separate clock windows enabled, the note has its own window; otherwise it appears below the clocks. Hiding it or switching modes preserves the text.

- With click-through enabled, clocks remain click-through. The locked note body absorbs clicks so double-clicking cannot open a desktop file or WPS behind it. Click and release a line number to edit. Press **Esc** or switch to another window to save the draft and lock the body again.
- With click-through disabled, click the body directly to edit.
- Line numbers include a clickable next blank line. Clicking that number inserts a newline; visual wrapping does not add logical line numbers.
- **Left-drag the line-number gutter** to move the window without altering text. In combined mode, this moves the whole window. Ctrl+left-drag is also supported.
- **Right-drag the gutter** to resize a separate note window. Position and size are saved.
- The live draft autosaves about 0.8 seconds after typing stops. **Ctrl+S** or **Save note snapshot…** opens a save dialog for exporting the current text. Subsequent edits update only the live draft, leaving exported snapshots unchanged.
- The live draft stays at `note.txt` in the program directory. A snapshot cannot overwrite that same file; its suggested name includes a timestamp. Canceling the dialog keeps the text and autosave destination unchanged. Hiding or quitting saves the draft. Save failures show an error and retain the in-memory text.

## Local data

| File | Purpose |
|---|---|
| `$XDG_CONFIG_HOME/world-clock/settings.json` | Cities, language, mode, opacity, positions, note visibility and size; defaults to `~/.config/world-clock/settings.json` |
| `PROGRAM_DIRECTORY/note.txt` | UTF-8 live draft; normally `~/.local/share/world-clock/note.txt` after installation, or the source directory when running from source |
| Your chosen snapshot file | Text at export time, independent of subsequent edits |

When upgrading, a legacy config-directory `note.txt` is migrated only if no program-directory draft exists; the legacy file remains intact. Reinstallation preserves the existing installed draft. Saves use temporary-file replacement, and an unreadable original draft is not overwritten.

The app uses the computer's system clock and provides no cloud sync or network time service. Notes are not encrypted; protect your backups accordingly. Source archives exclude personal notes, snapshots, settings, caches, and locally downloaded dependencies. See [THIRD_PARTY.md](THIRD_PARTY.md).

## Validation and limitations

- Validated on Ubuntu 22.04 X11 with one display and a bottom Dock: time zones, DST, date changes, layout, input regions, note save/reload, actual gutter drag/click, Ctrl+S, snapshot isolation, language switching, and locked-note double-click interception.
- Wayland, other desktops, multiple displays, and mixed scaling have not completed hardware acceptance. Wayland may restrict positioning, opacity, or click-through behavior.
- Only one instance can share a configuration or program directory. The program directory must be writable; per-user installation is recommended.
- No automatic startup, rich text, multiple notes, or version history. Sudden power loss or a forced kill can lose unsaved edits.

## Development and source archives

```bash
python3 -m py_compile world_clock.py notes.py i18n.py install.py scripts/build_source.py
python3 tests/gui_regression.py
python3 scripts/build_source.py
```

GUI checks require X11 and `libXtst.so.6`. They use temporary application copies and synthetic notes, simulate mouse/keyboard events, and restore the pointer afterward. They do not read or write your actual notes.

The allowlisted source packager creates `dist/world-clock-0.1.2.tar.gz` and a SHA-256 checksum. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.
