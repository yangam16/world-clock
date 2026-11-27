"""Stable application behavior, without a desktop or GTK import."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from world_clock.app import DEFAULT_ZONES, clock_values, program_directory, read_settings


class ClockTests(unittest.TestCase):
    def test_time_zones_and_dst(self):
        cases = [
            ('2026-11-11T08:03:00', 'America/Los_Angeles', ('11/11', '00:03:00', 'PST')),
            ('2026-11-11T08:03:00', 'America/New_York', ('11/11', '03:03:00', 'EST')),
            ('2026-07-11T08:03:00', 'America/Los_Angeles', ('07/11', '01:03:00', 'PDT')),
            ('2026-07-11T08:03:00', 'America/New_York', ('07/11', '04:03:00', 'EDT')),
            ('2026-11-11T01:03:00', 'America/Los_Angeles', ('11/10', '17:03:00', 'PST')),
        ]
        for timestamp, zone, expected in cases:
            with self.subTest(zone=zone, timestamp=timestamp):
                instant = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
                self.assertEqual(clock_values(zone, instant)[:3], expected)

    def test_source_layout_keeps_draft_at_project_root(self):
        self.assertEqual(program_directory(), Path(__file__).resolve().parents[1])


class SettingsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.settings = Path(directory.name) / 'settings.json'
        config = patch('world_clock.app.CONFIG', self.settings)
        config.start()
        self.addCleanup(config.stop)

    def test_missing_settings_use_system_zone(self):
        self.assertEqual(read_settings()['zones'], DEFAULT_ZONES)

    def test_saved_zones_survive_missing_time_zone_data(self):
        self.settings.write_text('{"zones": ["UTC", "Test/Unavailable", "Asia/Tokyo", "UTC"], "language": "en"}',
                                 encoding='utf-8')
        self.assertEqual(read_settings(), {'zones': ['UTC', 'Test/Unavailable', 'Asia/Tokyo'], 'language': 'en'})

    def test_invalid_settings_are_distinguished_from_missing_settings(self):
        for contents in ('{"zones":', '[]', '{"zones": "UTC"}'):
            with self.subTest(contents=contents):
                self.settings.write_text(contents, encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_settings()

    def test_permission_error_is_distinguished_from_missing_settings(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                read_settings()


if __name__ == '__main__':
    unittest.main()
