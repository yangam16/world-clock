#!/usr/bin/env python3
"""Build an allowlisted source archive; never traverse runtime or vendor data."""
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'world_clock.py', 'notes.py', 'i18n.py', 'run.sh', 'install.py', 'world-clock.desktop',
    'README.md', 'README.en.md', 'THIRD_PARTY.md', 'CHANGELOG.md', 'CONTRIBUTING.md',
    '.gitignore', '.gitattributes', 'scripts/build_source.py', 'tests/gui_regression.py', 'LICENSE',
)


def main():
    release = 'world-clock-0.1.2'
    output = ROOT / 'dist' / f'{release}.tar.gz'
    contents = []
    for name in FILES:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f'Missing or symlinked public source: {name}')
        contents.append((name, path.read_bytes()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
                for name, data in contents:
                    info = tarfile.TarInfo(f'{release}/{name}')
                    info.size = len(data)
                    info.mode = 0o755 if name == 'run.sh' else 0o644
                    archive.addfile(info, io.BytesIO(data))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_name(output.name + '.sha256')
    checksum.write_text(f'{digest}  {output.name}\n', encoding='ascii')
    print(f'Built {output} ({len(FILES)} public files)')
    print(f'SHA-256: {digest}')


if __name__ == '__main__':
    main()
