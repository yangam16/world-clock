# Contributing

Use Ubuntu 22.04 and Python 3.10+ with the system packages listed in README.md.
Run `./run.sh --check` before starting the graphical application.

Before proposing a change, check the affected user behavior in a disposable
configuration directory:

```bash
XDG_CONFIG_HOME="$(mktemp -d)" ./run.sh
```

For window or note changes, verify both standalone and combined modes, gutter
click versus drag, the final empty-line number, click-through before/after editing,
and save/reload. Use synthetic note text in screenshots and bug reports.

Report the Ubuntu version, X11/Wayland session, display scaling, Dock position,
steps to reproduce and expected/actual behavior. Do not attach real note contents,
settings, credentials, or full desktop screenshots containing private information.

Update README.md when changing user-visible behavior. Keep source archives free
of runtime data and locally downloaded dependencies.
