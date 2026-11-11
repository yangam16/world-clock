"""Stable application behavior, without a desktop or GTK import."""
from datetime import datetime, timezone
from pathlib import Path
import unittest

from world_clock.app import clock_values, program_directory


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


if __name__ == '__main__':
    unittest.main()
