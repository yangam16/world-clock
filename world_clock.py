#!/usr/bin/env python3
"""Small GTK world clock for Ubuntu 22.04 (Python 3.10+)."""
import argparse
import fcntl
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, available_timezones
from i18n import Translator

def system_zone():
    """Resolve Ubuntu's IANA zone rather than a fixed current UTC offset."""
    candidates = [os.environ.get('TZ', '').removeprefix(':')]
    try:
        target = str(Path('/etc/localtime').resolve())
        if '/zoneinfo/' in target:
            candidates.append(target.split('/zoneinfo/', 1)[1])
        candidates.append(Path('/etc/timezone').read_text(encoding='utf-8').strip())
    except OSError:
        pass
    valid = available_timezones()
    return next((zone for zone in candidates if zone in valid), 'UTC')


DEFAULT_ZONES = [system_zone()]
LABELS = {
    'America/Los_Angeles': 'Los Angeles · 洛杉矶',
    'America/New_York': 'New York · 纽约',
    'Asia/Shanghai': 'Shanghai · 上海',
    'Asia/Tokyo': 'Tokyo · 东京',
    'Europe/London': 'London · 伦敦',
    'Europe/Paris': 'Paris · 巴黎',
    'Asia/Singapore': 'Singapore · 新加坡',
    'Asia/Hong_Kong': 'Hong Kong · 香港',
    'Australia/Sydney': 'Sydney · 悉尼',
    'UTC': 'UTC · 协调世界时',
}
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'world-clock' / 'settings.json'


def clock_values(zone, instant=None):
    now = (instant or datetime.now(timezone.utc)).astimezone(ZoneInfo(zone))
    offset = now.strftime('%z')
    return now.strftime('%m/%d'), now.strftime('%H:%M:%S'), now.tzname(), f'UTC{offset[:3]}:{offset[3:]}', now.strftime('%Y-%m-%d')


def read_settings():
    try:
        data = json.loads(CONFIG.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Expected object')
        zones = data.get('zones', DEFAULT_ZONES)
        if not isinstance(zones, list):
            raise ValueError('Expected zone list')
        valid = available_timezones()
        zones = list(dict.fromkeys(z for z in zones if isinstance(z, str) and z in valid))
        opacity = data.get('opacity', 0.85)
        if isinstance(opacity, bool) or not isinstance(opacity, (float, int)):
            opacity = 0.85
        positions = data.get('positions', {})
        if not isinstance(positions, dict):
            positions = {}
        positions = {z: p for z, p in positions.items()
                     if isinstance(p, list) and len(p) == 2
                     and all(type(n) is int for n in p)}
        return zones or DEFAULT_ZONES.copy(), data.get('on_top') is True, max(0.3, min(1.0, opacity)), data.get('separate', True) is not False, positions
    except (OSError, ValueError, TypeError):
        return DEFAULT_ZONES.copy(), False, 0.85, True, {}


def main():
    parser = argparse.ArgumentParser(description='Ubuntu desktop world clock and sticky note')
    parser.add_argument('--local-only', action='store_true', help='Reset cities to the system time zone, preserving other preferences')
    parser.add_argument('--check', action='store_true', help='Check Python/GTK dependencies without opening a window')
    parser.add_argument('--version', action='version', version='World Clock 0.1.2')
    args = parser.parse_args()
    try:
        import gi
        gi.require_version('GIRepository', '2.0')
        from gi.repository import GIRepository
        for directory in (Path(__file__).parent / 'vendor/usr/lib').glob('*/girepository-1.0'):
            GIRepository.Repository.prepend_search_path(str(directory))
        gi.require_version('Gtk', '3.0')
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import Gtk, Gdk, GLib, Gio, AyatanaAppIndicator3
        import cairo
        from notes import NoteEditor
    except (ImportError, ValueError) as error:
        parser.exit(1, f'Desktop dependency unavailable: {error}\nInstall Ubuntu packages listed in README.md, then run ./run.sh --check.\n')
    if args.check:
        print('Python, GTK 3, Cairo and Ayatana AppIndicator imports: OK')
        print('Desktop rendering, tray service and pointer interaction require a graphical session.')
        return
    # Keep the descriptor alive for the entire GUI session. Repeated desktop
    # launches share this lock and cannot race to write the same note/config.
    instance_locks = []
    try:
        directories = {CONFIG.parent.resolve(), Path(__file__).resolve().parent}
        for directory in sorted(directories):
            directory.mkdir(parents=True, exist_ok=True)
            handle = (directory / '.instance.lock').open('a')
            instance_locks.append(handle)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('World Clock is already running. Use its top-bar icon.')
        return
    except OSError as error:
        parser.exit(1, f'Cannot acquire the application lock: {error}\n')

    class WorldClock(Gtk.Window):
        def __init__(self):
            super().__init__(title='World Clock')
            self.zones, self.on_top, self.opacity, self.separate, self.positions = read_settings()
            if args.local_only:
                self.zones, self.positions = DEFAULT_ZONES.copy(), {}
                self.separate = True
            self.clock_windows = {}
            self.position_save_source = None
            self.rebuilding = False
            self.locked = True
            self.note_editing = False
            try:
                note_settings = json.loads(CONFIG.read_text(encoding='utf-8'))
                if not isinstance(note_settings, dict):
                    note_settings = {}
            except (OSError, ValueError):
                note_settings = {}
            self.tr = Translator(note_settings.get('language'))
            self.language = self.tr.language
            self.set_title(self.tr('世界时钟'))
            self.note_enabled = note_settings.get('note_enabled') is True
            geometry = note_settings.get('note_geometry', [100, 100, 480, 260])
            self.note_geometry = geometry if isinstance(geometry, list) and len(geometry) == 4 and all(type(n) is int for n in geometry) else [100, 100, 480, 260]
            self.set_decorated(False)
            self.set_skip_taskbar_hint(True)
            self.set_default_size(660, 430)
            self.set_keep_above(self.on_top)
            self.set_opacity(self.opacity)
            self.connect('destroy', Gtk.main_quit)
            self.connect('size-allocate', self.update_input_region)
            self.connect('map', self.update_input_region)
            self.connect('focus-out-event', self.finish_note_editing)
            css = Gtk.CssProvider()
            css.load_from_data(b'''
                window { background: #f5f3ef; color: #243444; }
                .card { background: #ffffff; border-radius: 12px; padding: 16px; }
                .city { font-size: 17px; font-weight: 600; }
                .time { font-family: monospace; font-size: 25px; font-weight: bold; color: #1b556b; }
                .muted { color: #64747e; font-size: 12px; }
                .date { font-size: 18px; }
                .mini .city { font-size: 15px; }
                .mini .time { font-size: 23px; }
                .note-editor { font-size: 14px; color: #243444; }
                .note-editor text { background: #fffefa; }
                button { padding: 6px 10px; }
            ''')
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=18)
            self.root = root
            self.add(root)
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.cards = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            scroll.add(self.cards)
            root.pack_start(scroll, True, True, 0)
            self.status = Gtk.Label(label=self.tr('24 小时制 · 自动切换夏令时 · 使用系统时钟'), xalign=0)
            self.status.set_line_wrap(True)
            self.status.get_style_context().add_class('muted')
            root.pack_start(self.status, False, False, 0)
            self.note_scroll = Gtk.ScrolledWindow()
            self.note_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.note_scroll.set_size_request(240, 180)
            self.note_editor = NoteEditor(self, Path(__file__).resolve().parent / 'note.txt',
                                          legacy_path=CONFIG.parent / 'note.txt')
            self.note_scroll.add(self.note_editor)
            self.note_window = Gtk.Window(title=self.tr('世界时钟 · 便签'))
            self.note_window.set_decorated(False)
            self.note_window.set_default_size(max(240, self.note_geometry[2]), max(180, self.note_geometry[3]))
            self.note_window.set_skip_taskbar_hint(True)
            self.note_window.set_keep_above(self.on_top)
            self.note_window.set_opacity(self.opacity)
            self.note_window.connect('size-allocate', self.update_input_region)
            self.note_window.connect('map', self.update_input_region)
            self.note_window.connect('focus-out-event', self.finish_note_editing)
            self.note_window.connect('configure-event', self.remember_note_geometry)
            self.note_window.connect('delete-event', lambda *args: True)
            self.create_indicator()
            self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            self.connect('button-press-event', self.drag_window)
            self.rebuild()
            if args.local_only:
                self.save()
            GLib.timeout_add(250, self.tick)

        def show_clocks(self):
            if self.separate:
                self.hide()
            else:
                self.show_all()
            self.attach_note()

        def attach_note(self):
            parent = self.note_scroll.get_parent()
            target = self.note_window if self.separate else self.root
            if parent != target:
                if parent is not None:
                    parent.remove(self.note_scroll)
                if self.separate:
                    target.add(self.note_scroll)
                else:
                    target.pack_start(self.note_scroll, True, True, 0)
                    target.reorder_child(self.note_scroll, 1)
            if self.note_enabled:
                self.note_scroll.show_all()
                if self.separate:
                    self.note_window.show_all()
                    if parent != target:
                        x, y, _, _ = self.note_geometry
                        area = Gdk.Display.get_default().get_monitor_at_point(x, y).get_workarea()
                        width, height = self.note_window.get_size()
                        self.note_window.move(max(area.x, min(x, area.x + area.width - width)), max(area.y, min(y, area.y + area.height - height)))
                else:
                    self.note_window.hide()
            else:
                self.note_scroll.hide()
                self.note_window.hide()
            self.update_input_region()

        def toggle_note(self, item):
            if not item.get_active() and not self.note_editor.save_now():
                item.set_active(True)
                return
            self.note_enabled = item.get_active()
            self.note_editing = False
            self.note_editor.set_editable(not self.locked)
            self.note_editor.set_cursor_visible(not self.locked)
            self.attach_note()
            self.save()

        def remember_note_geometry(self, window, event):
            if self.separate and window.get_visible():
                self.note_geometry = [*window.get_position(), *window.get_size()]
                if self.position_save_source:
                    GLib.source_remove(self.position_save_source)
                self.position_save_source = GLib.timeout_add(500, self.flush_positions)
            return False

        def start_note_editing(self):
            self.note_editing = True
            self.note_editor.set_editable(True)
            self.note_editor.set_cursor_visible(True)
            self.update_input_region()

        def finish_note_editing(self, *args):
            if self.note_editor.has_dialog:
                return False
            self.note_editor.save_now()
            self.note_editing = False
            self.note_editor.set_editable(not self.locked)
            self.note_editor.set_cursor_visible(not self.locked)
            self.update_input_region()
            return False

        def city_label(self, zone):
            label = LABELS.get(zone, zone.split('/')[-1].replace('_', ' '))
            return label.split(' · ', 1)[0] if self.language == 'en' else label

        def request_language(self, item, language):
            if item.get_active() and language != self.language:
                GLib.idle_add(self.change_language, language)

        def change_language(self, language):
            self.tr = Translator(language)
            self.language = self.tr.language
            self.set_title(self.tr('世界时钟'))
            self.note_window.set_title(self.tr('世界时钟 · 便签'))
            self.status.set_text(self.tr('24 小时制 · 自动切换夏令时 · 使用系统时钟'))
            self.create_indicator()
            self.rebuild()
            self.save()
            return False

        def quit(self):
            if not self.note_editor.save_now():
                return
            if self.position_save_source:
                GLib.source_remove(self.position_save_source)
                self.position_save_source = None
            self.save()
            for window in self.clock_windows.values():
                window.destroy()
            self.note_window.destroy()
            self.destroy()

        def create_indicator(self):
            if not hasattr(self, 'indicator'):
                self.indicator = AyatanaAppIndicator3.Indicator.new(
                    'desktop-world-clock', 'preferences-system-time',
                    AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS)
                self.connect('destroy', lambda window: self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.PASSIVE))
            self.indicator.set_title(self.tr('世界时钟'))
            menu = Gtk.Menu()
            self.lock_item = Gtk.CheckMenuItem(label=self.tr('鼠标穿透（取消勾选以操作时钟）'))
            self.lock_item.set_active(self.locked)
            self.lock_item.connect('toggled', self.toggle_lock)
            menu.append(self.lock_item)
            top = Gtk.CheckMenuItem(label=self.tr('窗口置顶'))
            top.set_active(self.on_top)
            top.connect('toggled', self.toggle_top)
            menu.append(top)
            add = Gtk.MenuItem(label=self.tr('添加时区…'))
            add.connect('activate', self.choose_zone)
            menu.append(add)
            appearance = Gtk.MenuItem(label=self.tr('透明度…'))
            appearance.connect('activate', self.choose_opacity)
            menu.append(appearance)
            self.note_item = Gtk.CheckMenuItem(label=self.tr('显示便签'))
            self.note_item.set_active(self.note_enabled)
            self.note_item.connect('toggled', self.toggle_note)
            menu.append(self.note_item)
            save_note = Gtk.MenuItem(label=self.tr('保存便签快照…（Ctrl+S）'))
            save_note.connect('activate', lambda item: self.note_editor.choose_save_location())
            menu.append(save_note)
            menu.append(Gtk.SeparatorMenuItem())
            self.separate_item = Gtk.CheckMenuItem(label=self.tr('每个城市独立窗口'))
            self.separate_item.set_active(self.separate)
            self.separate_item.connect('toggled', self.toggle_separate)
            menu.append(self.separate_item)
            bottom = Gtk.MenuItem(label=self.tr('底部横排（避开 Dock）'))
            monitors = Gtk.Menu()
            display = Gdk.Display.get_default()
            for index in range(display.get_n_monitors()):
                monitor = display.get_monitor(index)
                area = monitor.get_geometry()
                entry = Gtk.MenuItem(label=self.tr('屏幕 {number} · {model} · {width}×{height}', number=index + 1, model=monitor.get_model(), width=area.width, height=area.height))
                entry.connect('activate', lambda item, m=monitor: self.arrange_bottom(m))
                monitors.append(entry)
            bottom.set_submenu(monitors)
            menu.append(bottom)
            language_root = Gtk.MenuItem(label='Language / 语言')
            language_menu = Gtk.Menu()
            group = None
            for code, label in [('en', 'English'), ('zh_CN', '简体中文')]:
                entry = Gtk.RadioMenuItem.new_with_label(group, label)
                group = entry.get_group()
                entry.set_active(self.language == code)
                entry.connect('toggled', self.request_language, code)
                language_menu.append(entry)
            language_root.set_submenu(language_menu)
            menu.append(language_root)
            menu.append(Gtk.SeparatorMenuItem())
            quit_item = Gtk.MenuItem(label=self.tr('退出世界时钟'))
            quit_item.connect('activate', lambda item: self.quit())
            menu.append(quit_item)
            menu.show_all()
            old_menu = getattr(self, 'indicator_menu', None)
            self.indicator_menu = menu
            self.indicator.set_menu(menu)
            self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
            if old_menu is not None:
                old_menu.destroy()

        def choose_opacity(self, item):
            dialog = Gtk.Dialog(title=self.tr('时钟透明度'), transient_for=self, modal=True)
            dialog.add_button(self.tr('完成'), Gtk.ResponseType.CLOSE)
            box = dialog.get_content_area()
            box.set_border_width(18)
            box.add(Gtk.Label(label=self.tr('不透明度（30%–100%）')))
            slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 30, 100, 1)
            slider.set_size_request(300, -1)
            slider.set_digits(0)
            slider.set_value(self.opacity * 100)
            slider.connect('value-changed', self.change_opacity)
            box.add(slider)
            dialog.show_all()
            dialog.run()
            dialog.destroy()

        def drag_window(self, widget, event):
            if not self.locked and event.button == 1:
                widget.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
                return True
            return False

        def save(self):
            try:
                CONFIG.parent.mkdir(parents=True, exist_ok=True)
                temp = CONFIG.with_suffix('.tmp')
                temp.write_text(json.dumps({'zones': self.zones, 'on_top': self.on_top, 'opacity': self.opacity,
                                            'separate': self.separate, 'positions': self.positions,
                                            'note_enabled': self.note_enabled, 'note_geometry': self.note_geometry,
                                            'language': self.language}, ensure_ascii=False, indent=2), encoding='utf-8')
                temp.replace(CONFIG)
            except OSError as error:
                self.status.set_text(self.tr('配置保存失败：{error}', error=error))

        def toggle_top(self, button):
            self.on_top = button.get_active()
            self.set_keep_above(self.on_top)
            for window in self.clock_windows.values():
                window.set_keep_above(self.on_top)
            self.note_window.set_keep_above(self.on_top)
            self.save()

        def change_opacity(self, slider):
            self.opacity = slider.get_value() / 100
            self.set_opacity(self.opacity)
            for window in self.clock_windows.values():
                window.set_opacity(self.opacity)
            self.note_window.set_opacity(self.opacity)
            self.save()

        def toggle_lock(self, button):
            self.locked = button.get_active()
            self.note_editing = False
            self.note_editor.set_editable(not self.locked)
            self.note_editor.set_cursor_visible(not self.locked)
            self.update_input_region()

        def update_input_region(self, *args):
            for widget in [self, self.note_window, *self.clock_windows.values()]:
                window = widget.get_window()
                if window is not None:
                    region = cairo.Region() if self.locked else cairo.Region(cairo.RectangleInt(0, 0, widget.get_allocated_width(), widget.get_allocated_height()))
                    if self.locked and self.note_enabled and widget == (self.note_window if self.separate else self):
                        child = self.note_scroll
                        origin = child.translate_coordinates(widget, 0, 0)
                        if origin is not None:
                            x, y = origin
                            width = child.get_allocated_width()
                            region.union(cairo.Region(cairo.RectangleInt(x, y, width, child.get_allocated_height())))
                    window.input_shape_combine_region(region, 0, 0)

        def toggle_separate(self, item):
            self.separate = item.get_active()
            self.rebuild()
            self.show_clocks()
            self.save()

        def remember_position(self, window, event, zone):
            if not self.rebuilding:
                self.positions[zone] = list(window.get_position())
                if self.position_save_source:
                    GLib.source_remove(self.position_save_source)
                self.position_save_source = GLib.timeout_add(500, self.flush_positions)
            return False

        def flush_positions(self):
            self.position_save_source = None
            self.save()
            return False

        def arrange_bottom(self, monitor=None):
            if not self.separate:
                self.separate_item.set_active(True)
            display = Gdk.Display.get_default()
            monitor = monitor or display.get_primary_monitor() or display.get_monitor(0)
            area = monitor.get_workarea()
            windows = list(self.clock_windows.values())
            if not windows:
                return False
            # Use actual natural widget sizes; wrap additional cities into rows.
            widths = [max(w.get_size()[0], w.get_preferred_width()[1]) for w in windows]
            heights = [max(w.get_size()[1], w.get_preferred_height()[1]) for w in windows]
            gap, margin = 12, 12
            rows, row, used = [], [], 0
            for window, width, height in zip(windows, widths, heights):
                if row and used + gap + width > area.width - margin * 2:
                    rows.append(row)
                    row, used = [], 0
                row.append((window, width, height))
                used += width + (gap if len(row) > 1 else 0)
            if row:
                rows.append(row)
            y = area.y + area.height - margin
            for row in reversed(rows):
                y = max(area.y + margin, y - max(h for _, _, h in row))
                total = sum(w for _, w, _ in row) + gap * (len(row) - 1)
                x = area.x + max(margin, (area.width - total) // 2)
                for window, width, height in row:
                    window.move(x, y)
                    x += width + gap
                y -= gap
            return False

        def remove_zone(self, button, zone):
            self.zones.remove(zone)
            self.save()
            self.rebuild()

        def rebuild(self):
            needs_arrange = self.separate and any(zone not in self.positions for zone in self.zones)
            self.rebuilding = True
            for window in self.clock_windows.values():
                window.destroy()
            self.clock_windows = {}
            for child in self.cards.get_children():
                child.destroy()
            self.rows = []
            for zone in self.zones:
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
                card.get_style_context().add_class('card')
                if self.separate:
                    card.get_style_context().add_class('mini')
                info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                city = Gtk.Label(label=self.city_label(zone), xalign=0)
                city.get_style_context().add_class('city')
                info.pack_start(city, False, False, 0)
                detail = Gtk.Label(xalign=0)
                detail.get_style_context().add_class('muted')
                info.pack_start(detail, False, False, 0)
                card.pack_start(info, True, True, 0)
                date = Gtk.Label()
                date.get_style_context().add_class('date')
                clock_line = Gtk.Box(spacing=10) if self.separate else card
                clock_line.pack_start(date, False, False, 0)
                time = Gtk.Label()
                time.get_style_context().add_class('time')
                clock_line.pack_start(time, False, False, 0)
                if self.separate:
                    card.pack_start(clock_line, False, False, 0)
                remove = Gtk.Button(label='×')
                remove.set_valign(Gtk.Align.CENTER)
                remove.set_tooltip_text(self.tr('移除此时区'))
                remove.connect('clicked', self.remove_zone, zone)
                card.pack_start(remove, False, False, 0)
                if self.separate:
                    window = Gtk.Window(title=f"{self.tr('世界时钟')} · {zone}")
                    window.set_decorated(False)
                    window.set_resizable(False)
                    window.set_skip_taskbar_hint(True)
                    window.set_skip_pager_hint(True)
                    window.set_keep_above(self.on_top)
                    window.set_opacity(self.opacity)
                    window.add(card)
                    self.clock_windows[zone] = window
                    window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
                    window.connect('button-press-event', self.drag_window)
                    window.connect('map', self.update_input_region)
                    window.connect('size-allocate', self.update_input_region)
                    window.connect('configure-event', self.remember_position, zone)
                    window.connect('delete-event', lambda *args: True)
                    window.show_all()
                    if zone in self.positions:
                        x, y = self.positions[zone]
                        display = Gdk.Display.get_default()
                        monitor = display.get_monitor_at_point(x, y)
                        area = monitor.get_workarea()
                        width, height = window.get_size()
                        window.move(max(area.x, min(x, area.x + area.width - width)),
                                    max(area.y, min(y, area.y + area.height - height)))
                else:
                    self.cards.pack_start(card, False, False, 0)
                self.rows.append((zone, date, time, detail))
            if not self.zones:
                self.cards.pack_start(Gtk.Label(label=self.tr('点击“添加时区”选择城市')), False, False, 24)
            self.tick()
            self.cards.show_all()
            self.rebuilding = False
            self.show_clocks()
            if needs_arrange:
                GLib.idle_add(self.arrange_bottom)

        def tick(self):
            instant = datetime.now(timezone.utc)
            for zone, date, time, detail in self.rows:
                day, clock, short, offset, full = clock_values(zone, instant)
                date.set_text(day)
                date.set_tooltip_text(full)
                time.set_text(clock)
                detail.set_text(f'{short}  ·  {offset}')
                detail.set_tooltip_text(zone)
            return True

        def choose_zone(self, button):
            dialog = Gtk.Dialog(title=self.tr('选择时区'), transient_for=self, modal=True)
            dialog.set_default_size(470, 480)
            dialog.add_button(self.tr('取消'), Gtk.ResponseType.CANCEL)
            dialog.add_button(self.tr('添加'), Gtk.ResponseType.OK)
            dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
            content = dialog.get_content_area()
            content.set_spacing(10)
            content.set_border_width(12)
            search = Gtk.SearchEntry(placeholder_text=self.tr('搜索城市或时区，例如 洛杉矶 / New York / Asia'))
            content.pack_start(search, False, False, 0)
            model = Gtk.ListStore(str, str, str)
            for zone in sorted(available_timezones()):
                if zone not in self.zones and not zone.startswith(('posix/', 'right/')):
                    label = self.city_label(zone)
                    search_label = LABELS.get(zone, label)
                    model.append([label, zone, (search_label + ' ' + zone.replace('_', ' ')).casefold()])
            filtered = model.filter_new()
            filtered.set_visible_func(lambda model, row, data: search.get_text().strip().casefold().replace('_', ' ') in model[row][2])
            search.connect('search-changed', lambda entry: filtered.refilter())
            tree = Gtk.TreeView(model=filtered, headers_visible=False)
            tree.append_column(Gtk.TreeViewColumn(self.tr('城市'), Gtk.CellRendererText(), text=0))
            tree.append_column(Gtk.TreeViewColumn(self.tr('时区'), Gtk.CellRendererText(), text=1))
            tree.get_selection().connect('changed', lambda selection: dialog.set_response_sensitive(Gtk.ResponseType.OK, selection.get_selected()[1] is not None))
            tree.connect('row-activated', lambda *args: dialog.response(Gtk.ResponseType.OK))
            scroll = Gtk.ScrolledWindow()
            scroll.add(tree)
            content.pack_start(scroll, True, True, 0)
            dialog.show_all()
            if dialog.run() == Gtk.ResponseType.OK:
                selected_model, row = tree.get_selection().get_selected()
                if row is not None:
                    self.zones.append(selected_model[row][1])
                    self.save()
                    self.rebuild()
            dialog.destroy()

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    watcher = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                           'org.freedesktop.DBus', 'NameHasOwner',
                           GLib.Variant('(s)', ('org.kde.StatusNotifierWatcher',)),
                           GLib.VariantType.new('(b)'), Gio.DBusCallFlags.NONE, 3000, None)
    if not watcher.unpack()[0]:
        dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE,
                                   text=Translator()('Ubuntu 顶栏图标服务未启用'))
        dialog.format_secondary_text(Translator()('请在“扩展”中启用 Ubuntu AppIndicators 后重新运行世界时钟。'))
        dialog.run()
        dialog.destroy()
        return
    window = WorldClock()
    def stop():
        window.quit()
        return True
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, stop)
    window.show_clocks()
    Gtk.main()


if __name__ == '__main__':
    main()
