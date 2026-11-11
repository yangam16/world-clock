# User guide

[Project home](../README.en.md) · [简体中文](usage.zh-CN.md)

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

The app uses the computer's system clock and provides no cloud sync or network time service. Notes are not encrypted; protect your backups accordingly. Source archives exclude personal notes, snapshots, settings, caches, and locally downloaded dependencies. See [THIRD_PARTY.md](../THIRD_PARTY.md).

## Validation and limitations

- Validated on Ubuntu 22.04 X11 with one display and a bottom Dock: time zones, DST, date changes, layout, input regions, note save/reload, actual gutter drag/click, Ctrl+S, snapshot isolation, language switching, and locked-note double-click interception.
- Wayland, other desktops, multiple displays, and mixed scaling have not completed hardware acceptance. Wayland may restrict positioning, opacity, or click-through behavior.
- Only one instance can share a configuration or program directory. The program directory must be writable; per-user installation is recommended.
- No automatic startup, rich text, multiple notes, or version history. Sudden power loss or a forced kill can lose unsaved edits.

