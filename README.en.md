# World Clock and Sticky Note

[简体中文](README.md) | [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/yangam16/world-clock/actions/workflows/ci.yml/badge.svg)](https://github.com/yangam16/world-clock/actions/workflows/ci.yml)

A lightweight GTK 3 desktop tool for Ubuntu 22.04. View multiple local dates and times in compact horizontal windows, and manage clocks and a plain-text note from the system top bar.

This project was developed using an LLM. [Issues](https://github.com/yangam16/world-clock/issues) are welcome.

## Features

- **World clocks:** starts with the system time zone; search cities, with automatic DST and date changes.
- **Desktop layout:** separate windows or a combined list, bottom alignment above the Dock, opacity, always-on-top and saved positions.
- **Sticky note:** line numbers, click-to-edit, dragging and draft autosave; Ctrl+S exports an independent snapshot.
- **English and Chinese UI:** switch live from the top-bar menu; your choice is remembered.
- **Desktop launchers:** start by double-clicking a shortcut or using the application menu, without a terminal for daily use.

## Quick start

Requires **Ubuntu 22.04, Python 3.10+ and GTK 3**. Validated on X11; enable Ubuntu AppIndicators in Extensions.

```bash
sudo apt update
sudo apt install git python3 python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 gir1.2-ayatanaappindicator3-0.1 tzdata gnome-shell-extension-appindicator

git clone https://github.com/yangam16/world-clock.git
cd world-clock
./run.sh --check
python3 install.py --desktop
```

Return to the desktop, right-click **World Clock**, select **Allow Launching**, and double-click it. You can also search the application menu. Controls are in the **top-right Ubuntu system bar**.

The repository's `assets/world-clock.desktop` is a template. Generate a local launcher with the installer. See the [desktop launcher tutorial](docs/installation.en.md) for full steps and troubleshooting.

## Documentation

| Topic | English | 中文 |
|---|---|---|
| Installation, desktop shortcuts and updates | [Installation](docs/installation.en.md) | [安装教程](docs/installation.zh-CN.md) |
| Clocks, notes, snapshots and storage | [User guide](docs/usage.en.md) | [使用指南](docs/usage.zh-CN.md) |
| Development, testing and source archives | [Development](docs/development.md) | [开发指南](docs/development.md) |

- [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
- [Security](SECURITY.md) · [Third-party dependencies](THIRD_PARTY.md)
- [Downloads](https://github.com/yangam16/world-clock/releases) · [Report an issue](https://github.com/yangam16/world-clock/issues/new/choose)

## Repository layout

```text
world-clock/
├── src/world_clock/       # Application package: windows, notes and translations
├── assets/                # Desktop launcher template
├── docs/                  # Installation, usage and development guides
├── scripts/               # Per-user installer and source packager
├── tests/                 # Automated checks and X11 GUI regression
├── .github/               # CI, issue forms and pull request template
├── pyproject.toml         # Python project metadata
├── run.sh                 # Stable source launcher
├── install.py             # Stable desktop installation entry point
├── README.md / README.en.md
└── LICENSE
```

## Data and compatibility

The live draft autosaves to **`note.txt` in the program directory**, normally `~/.local/share/world-clock/note.txt` after desktop installation. Exported snapshots remain unchanged by later edits. Settings are in `~/.config/world-clock/`, respecting XDG configuration. Upgrades preserve the draft and settings.

Validated on Ubuntu 22.04 X11 with one display and a bottom Dock. Wayland, other desktops and multi-display scaling combinations remain unverified. AppImage, automatic startup, rich text and multiple notes are not provided. See the [user guide](docs/usage.en.md) for validation boundaries.

## Get involved

[Bug reports and feature requests](https://github.com/yangam16/world-clock/issues/new/choose) and pull requests are welcome. Reproduce issues with synthetic text and remove private notes, account data, credentials and private desktop content before uploading attachments.

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md). The source uses the [MIT license](LICENSE); runtime dependencies retain their own licenses.
