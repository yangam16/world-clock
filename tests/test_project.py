"""Installation, documentation and archive behavior using disposable copies."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('source_packager', ROOT / 'scripts/build_source.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='world-clock-project-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        for name in packager.FILES:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

    def install(self):
        subprocess.run([
            '/usr/bin/python3', str(self.source / 'install.py'),
            '--data-dir', str(self.base / 'data with spaces'), '--bin-dir', str(self.base / 'bin'),
            '--desktop-dir', str(self.base / 'Desktop'),
        ], check=True, capture_output=True, text=True)
        return self.base / 'data with spaces/world-clock'

    def test_upgrade_preserves_data_and_cannot_load_legacy_flat_module(self):
        installed = self.base / 'data with spaces/world-clock'
        installed.mkdir(parents=True)
        draft = installed / 'note.txt'
        draft.write_text('Synthetic existing draft\n', encoding='utf-8')
        (installed / 'world_clock.py').write_text("raise RuntimeError('Legacy module loaded')\n", encoding='utf-8')
        self.install()
        result = subprocess.run([str(installed / 'run.sh'), '--version'], check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), f'World Clock {packager.__version__}')
        self.assertEqual(draft.read_text(), 'Synthetic existing draft\n')
        self.install()
        self.assertEqual(draft.read_text(), 'Synthetic existing draft\n')
        self.assertEqual((installed / 'README.en.md').read_bytes(), (ROOT / 'README.en.md').read_bytes())
        launcher = (self.base / 'Desktop/world-clock.desktop').read_text()
        self.assertIn(str(installed / 'run.sh'), launcher)
        self.assertNotIn('Exec=world-clock\n', launcher)
        self.assertTrue((self.base / 'Desktop/world-clock.desktop').stat().st_mode & 0o111)
        if shutil.which('desktop-file-validate'):
            subprocess.run(['desktop-file-validate', str(self.base / 'Desktop/world-clock.desktop')], check=True)

    def test_source_archive_excludes_runtime_data(self):
        (self.source / 'note.txt').write_text('Synthetic private draft')
        (self.source / 'settings.json').write_text('{"synthetic": true}')
        (self.source / 'src/world_clock/note.txt').write_text('Synthetic nested draft')
        subprocess.run(['/usr/bin/python3', str(self.source / 'scripts/build_source.py')], check=True, capture_output=True)
        archive = self.source / f'dist/world-clock-{packager.__version__}.tar.gz'
        with tarfile.open(archive) as source:
            members = source.getmembers()
            names = {m.name.split('/', 1)[1] for m in members}
            self.assertEqual(names, set(packager.FILES))
            for member in members:
                self.assertTrue(member.isfile())
                self.assertFalse(member.uname or member.gname)
                self.assertEqual((member.uid, member.gid, member.mtime), (0, 0, 0))
        self.assertNotIn('note.txt', names)
        self.assertNotIn('settings.json', names)

    def test_markdown_links_and_fences(self):
        for name in packager.FILES:
            if not name.endswith('.md'):
                continue
            path = ROOT / name
            content = path.read_text()
            self.assertEqual(content.count('```') % 2, 0, name)
            for target in re.findall(r'\]\(([^)]+)\)', content):
                if target.startswith(('https://', 'http://', '#')):
                    continue
                self.assertTrue((path.parent / target.split('#', 1)[0]).is_file(), (name, target))


if __name__ == '__main__':
    unittest.main()
