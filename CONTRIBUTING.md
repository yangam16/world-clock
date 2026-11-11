# Contributing

Use Ubuntu 22.04 and Python 3.10+ with the system packages listed in README.md.
Run `./run.sh --check` before starting the graphical application.

Start with the source and installation checks:

```bash
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
```

For desktop changes, run GUI regression checks in an X11 session:

```bash
python3 tests/gui_regression.py
```

The checks copy the program into a temporary directory and use synthetic data.
Changing only XDG_CONFIG_HOME does not isolate notes: the live draft belongs to
the program directory. For a manual isolated run, use a disposable source copy.

For window or note changes, verify both standalone and combined modes, gutter
click versus drag, the final empty-line number, click-through before/after editing,
and snapshot save/cancel, independent autosave, and language changes. Use synthetic
note text in screenshots and bug reports.

Report the Ubuntu version, X11/Wayland session, display scaling, Dock position,
steps to reproduce and expected/actual behavior. Do not attach real note contents,
settings, credentials, or full desktop screenshots containing private information.

Update both READMEs and the relevant guides in `docs/` when changing user-visible
behavior. Keep source archives free of runtime data and locally downloaded
dependencies. See [development.md](docs/development.md) for architecture, packaging
and the release checklist. Use respectful, constructive discussion in Issues/PRs.
