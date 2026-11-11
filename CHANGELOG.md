# Changelog

## 0.1.3

- Added English README, desktop launcher tutorials and LLM-development attribution.
- Organized the app as a `src/world_clock` package, with desktop resources in
  `assets/`, guides in `docs/`, and install/build tooling in `scripts/`.
- Kept `./run.sh` and `python3 install.py --desktop` as stable entry points.
- Preserved the live-draft directory and prevented legacy flat modules from
  shadowing the new package during installation upgrades.
- Added Python project metadata, contribution/security guidance, Issue/PR
  templates and read-only CI for source, installation and archive checks.
- Reworked both READMEs as concise project landing pages linked to full guides.

## 0.1.2

- English and Simplified Chinese UI with persistent, live language switching.
- Ctrl+S opens a nonblocking snapshot save dialog. Choosing a destination exports
  the current text without changing the live autosave target.
- Live drafts autosave to the program directory; legacy config-directory notes
  are migrated when no program-directory draft exists, leaving the old file intact.
- Nonblocking, deduplicated save-error dialogs prevent focus-loss recursion.
- Locked note bodies absorb mouse clicks so double-clicks cannot open files or
  applications behind the note. Clock windows retain click-through behavior.
- X11 regression checks exercise actual shortcuts, double clicks, snapshot
  isolation, migration, autosave, window modes and language changes.

## 0.1.1

- Optional desktop shortcut with desktop-directory detection and launch trust setup.
- App-menu launcher remains available after installation; no terminal is needed for daily use.
- Single-instance protection for each configuration directory.
- Preserve the optional local typelib and its notice during a developer-checkout installation.

## 0.1.0

- Multiple selectable IANA time zones with local date, time and DST abbreviation.
- One system-zone clock by default, compact horizontal windows and bottom layout.
- Ubuntu AppIndicator menu, opacity, always-on-top and click-through controls.
- Optional sticky note, standalone or embedded below the clocks.
- Clickable line numbers, next-line editing, gutter dragging and resizing.
- Autosave, Ctrl+S and explicit note saving with atomic replacement.
- Portable per-user installation and allowlisted source packaging.

Validated on one Ubuntu 22.04 X11 desktop. Cross-desktop and Wayland interaction
have not been accepted. The project's own source uses the MIT license.
