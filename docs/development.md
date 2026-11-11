# Development guide / 开发指南

## Setup

Use Ubuntu 22.04 and Python 3.10+. Install the desktop dependencies in the [installation guide](installation.en.md), then run:

```bash
./run.sh --check
./run.sh
```

The primary desktop installation method is `python3 install.py --desktop`. PyGObject/GTK are system dependencies, not pip dependencies.

## Responsibilities

| Path | Responsibility |
|---|---|
| `src/world_clock/app.py` | Clock windows, top-bar menu, settings, layout, instance locks and application lifecycle |
| `src/world_clock/notes.py` | Text editing, gutter input, live-draft autosave and independent snapshot exports |
| `src/world_clock/i18n.py` | Chinese/English UI catalog |
| `src/world_clock/__init__.py` | Package identity and single version definition |
| `scripts/install.py` | Copies an explicit runtime/documentation list and generates local launchers |
| `scripts/build_source.py` | Builds an explicit public-source allowlist with neutral archive metadata |
| `assets/world-clock.desktop` | Portable launcher template; installer supplies the absolute executable path |

The source launcher and per-user desktop installer use the same `src/world_clock/` layout. The application resolves the program root so moving Python files does not move `note.txt` into `src/`. Standard Python package installs use the per-user application-data directory for the draft.

Root `install.py` and `run.sh` remain stable entry points. Old flat Python files may remain after an upgrade; the launcher starts inside `src/` so they cannot shadow the new package. The installer preserves live data and does not delete those old files.

## Checks

Fast checks without opening windows:

```bash
python3 -m compileall -q src scripts tests install.py
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
./run.sh --check
```

Real X11 interaction checks:

```bash
python3 tests/gui_regression.py
```

The GUI checks need a real X11 session and `libXtst.so.6`. They copy the app into a temporary directory, use synthetic text, and restore the pointer. They cover Ctrl+S, snapshot isolation, migration, autosave, errors, language switching and double-click interception. They do not validate Wayland or all hardware/display combinations.

Changing only `XDG_CONFIG_HOME` does not isolate the draft: it belongs to the program directory. Use a disposable source copy for manual experiments. Never use real private notes as test fixtures.

## Packaging

```bash
python3 scripts/build_source.py
```

Version comes from `src/world_clock/__init__.py`. The output is `dist/world-clock-VERSION.tar.gz` plus a SHA-256 file. Only explicitly named public files are included; archive owner names and timestamps are neutralized.

For standard Python build tooling, in a disposable environment:

```bash
python3 -m pip install build
python3 -m build
```

`pyproject.toml` supplies project metadata, a console entry point and setuptools package discovery. `MANIFEST.in` excludes runtime data from the standard source distribution. Python wheels do not install desktop launchers or GTK packages; use the per-user desktop installer for desktop integration.

## Release checklist

1. Update the package version and CHANGELOG.md; keep both READMEs and guides consistent.
2. Run fast checks, installation/update preservation tests and affected GUI checks.
3. Build the source archive and inspect filenames, checksums and privacy exclusions.
4. Commit only intended public paths; never force-push over another contributor's work.
5. Publish a new tag/release and new archive assets. Keep existing released artifacts unchanged.
6. State separately what passed locally, in CI, and on the real desktop.

## 中文提示

修改界面或便签交互时同步中英文文档。单元/安装检查与真实桌面 GUI 验证分开报告；CI 通过不代表 Wayland、多屏缩放或现场验收通过。发布前按白名单检查源码包，真实便签和配置不得作为测试或文档附件上传。
