#!/usr/bin/env python3
"""Build an allowlisted source archive; never traverse runtime or vendor data."""
import gzip
import hashlib
import io
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from world_clock import __version__

FILES = (
    'src/world_clock/__init__.py', 'src/world_clock/__main__.py',
    'src/world_clock/app.py', 'src/world_clock/notes.py', 'src/world_clock/i18n.py',
    'run.sh', 'install.py', 'assets/world-clock.desktop', 'pyproject.toml', 'MANIFEST.in',
    'README.md', 'README.en.md', 'THIRD_PARTY.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md',
    '.gitignore', '.gitattributes', '.editorconfig',
    'docs/installation.zh-CN.md', 'docs/installation.en.md',
    'docs/usage.zh-CN.md', 'docs/usage.en.md', 'docs/development.md',
    'scripts/build_source.py', 'scripts/install.py',
    'tests/gui_regression.py', 'tests/test_application.py', 'tests/test_project.py',
    '.github/ISSUE_TEMPLATE/bug_report.yml', '.github/ISSUE_TEMPLATE/feature_request.yml',
    '.github/ISSUE_TEMPLATE/config.yml', '.github/pull_request_template.md', '.github/workflows/ci.yml',
    'LICENSE',
)


def main():
    release = f'world-clock-{__version__}'
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
