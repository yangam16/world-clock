#!/usr/bin/env python3
"""Install only public source files and a per-user desktop launcher."""
import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def desktop_quote(value):
    value = str(value)
    if any(c in value for c in '\n\r='):
        raise ValueError('Installation paths cannot contain newlines or equals signs')
    value = value.replace('%', '%%')
    for char in ('\\', '"', '`', '$'):
        value = value.replace(char, '\\' + char)
    # Desktop-entry string escaping is applied before Exec argument parsing.
    return '"' + value.replace('\\', '\\\\') + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))))
    parser.add_argument('--bin-dir', type=Path, default=Path.home() / '.local/bin')
    parser.add_argument('--desktop', action='store_true', help='Also create a desktop shortcut')
    parser.add_argument('--desktop-dir', type=Path, help='Desktop directory override (also enables desktop shortcut)')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    destination = args.data_dir.expanduser().resolve() / 'world-clock'
    binary_dir = args.bin_dir.expanduser().resolve()
    desktop_dir = args.data_dir.expanduser().resolve() / 'applications'
    executable = binary_dir / 'world-clock'
    quoted = desktop_quote(destination / 'run.sh')
    destination.mkdir(parents=True, exist_ok=True)
    binary_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    for name in ('world_clock.py', 'notes.py', 'run.sh', 'README.md', 'THIRD_PARTY.md', 'LICENSE', 'LICENSE.proposed'):
        path = source / name
        if path.is_file() and path.resolve() != (destination / name).resolve():
            shutil.copy2(path, destination / name)
    # A developer checkout may have the Ubuntu typelib fallback. Preserve its
    # notice when installing locally; public source archives do not include it.
    fallback = list(source.glob('vendor/usr/lib/*/girepository-1.0/AyatanaAppIndicator3-0.1.typelib'))
    if fallback:
        notice = source / 'vendor/usr/share/doc/gir1.2-ayatanaappindicator3-0.1/copyright'
        if not notice.is_file():
            raise RuntimeError('Local typelib fallback is missing its license notice')
        for path in [*fallback, notice]:
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.resolve() != target.resolve():
                shutil.copy2(path, target)
    (destination / 'run.sh').chmod(0o755)
    executable.write_text('#!/bin/sh\nexec ' + shlex.quote(str(destination / 'run.sh')) + ' "$@"\n', encoding='utf-8')
    executable.chmod(0o755)
    template = (source / 'world-clock.desktop').read_text(encoding='utf-8')
    desktop = template.replace('Exec=world-clock\n', f'Exec={quoted}\n')
    (desktop_dir / 'world-clock.desktop').write_text(desktop, encoding='utf-8')
    if args.desktop or args.desktop_dir:
        user_desktop = args.desktop_dir
        if user_desktop is None:
            result = subprocess.run(['xdg-user-dir', 'DESKTOP'], check=True, capture_output=True, text=True)
            user_desktop = Path(result.stdout.strip())
        user_desktop = user_desktop.expanduser().resolve()
        if user_desktop == Path.home().resolve():
            raise RuntimeError('Desktop directory is disabled. Set --desktop-dir explicitly.')
        user_desktop.mkdir(parents=True, exist_ok=True)
        shortcut = user_desktop / 'world-clock.desktop'
        shortcut.write_text(desktop, encoding='utf-8')
        shortcut.chmod(0o755)
        trusted = subprocess.run(['gio', 'set', str(shortcut), 'metadata::trusted', 'true'], capture_output=True, text=True)
        print(f'Desktop shortcut: {shortcut}')
        if trusted.returncode:
            print('If prompted, right-click the desktop shortcut and choose Allow Launching.')
    print(f'Installed application: {destination}')
    print(f'Installed command: {executable}')
    print('User settings and note contents were not modified.')


if __name__ == '__main__':
    main()
