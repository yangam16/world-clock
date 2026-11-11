"""Plain-text sticky note with a clickable, scrolling line-number gutter."""
from pathlib import Path
import tempfile
from datetime import datetime

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo


class NoteEditor(Gtk.TextView):
    GUTTER = 44

    def __init__(self, owner, path, legacy_path=None):
        super().__init__()
        self.owner = owner
        self.path = Path(path)
        self.dirty = False
        self.save_source = None
        self.load_failed = False
        self.gutter_press = None
        self.save_dialog = None
        self.error_dialog = None
        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.set_left_margin(8)
        self.set_right_margin(10)
        self.set_top_margin(8)
        self.set_bottom_margin(32)
        self.set_border_window_size(Gtk.TextWindowType.LEFT, self.GUTTER)
        self.set_monospace(True)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.get_style_context().add_class('note-editor')
        self.buffer = self.get_buffer()
        source = self.path
        migrate = not source.exists() and legacy_path is not None and Path(legacy_path).is_file()
        if migrate:
            source = Path(legacy_path)
        try:
            text = source.read_text(encoding='utf-8')
        except FileNotFoundError:
            text = ''
        except (OSError, UnicodeError) as error:
            text = ''
            self.load_failed = True
            GLib.idle_add(self.report_error, self.owner.tr('便签读取失败，已禁止覆盖原文件：{error}', error=error))
        self.buffer.set_text(text)
        self.buffer.connect('changed', self.changed)
        self.connect('button-press-event', self.click_gutter)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect('motion-notify-event', self.move_gutter)
        self.connect('button-release-event', self.release_gutter)
        self.connect('key-press-event', self.key_press)
        if migrate and not self.load_failed:
            self.dirty = True
            GLib.idle_add(self.autosave)

    @property
    def has_dialog(self):
        return self.save_dialog is not None or self.error_dialog is not None

    def do_draw(self, cr):
        Gtk.TextView.do_draw(self, cr)
        window = self.get_window(Gtk.TextWindowType.LEFT)
        if window is None or not Gtk.cairo_should_draw_window(cr, window):
            return False
        cr.save()
        Gtk.cairo_transform_to_window(cr, self, window)
        cr.rectangle(0, 0, self.GUTTER, self.get_allocated_height())
        cr.clip()
        cr.set_source_rgb(0.93, 0.93, 0.91)
        cr.paint()
        visible = self.get_visible_rect()
        def draw_number(number, y):
            _, wy = self.buffer_to_window_coords(Gtk.TextWindowType.LEFT, 0, y)
            layout = self.create_pango_layout(str(number))
            layout.set_font_description(Pango.FontDescription('Monospace 10'))
            width, _ = layout.get_pixel_size()
            cr.set_source_rgb(0.43, 0.49, 0.51)
            cr.move_to(self.GUTTER - width - 8, wy)
            PangoCairo.show_layout(cr, layout)
        line, _ = self.get_line_at_y(visible.y)
        # forward_line() returns False when it lands on the buffer end,
        # including a valid final empty line. Draw every logical line explicitly.
        for number in range(line.get_line(), self.buffer.get_line_count()):
            line = self.buffer.get_iter_at_line(number)
            y, height = self.get_line_yrange(line)
            if y > visible.y + visible.height:
                break
            draw_number(line.get_line() + 1, y)
        end = self.buffer.get_end_iter()
        if end.get_line_offset() > 0:
            y, height = self.get_line_yrange(end)
            draw_number(end.get_line() + 2, y + height)
        cr.restore()
        return False

    def click_gutter(self, widget, event):
        if event.window != self.get_window(Gtk.TextWindowType.LEFT):
            if self.owner.locked and not self.owner.note_editing:
                # Read-only note bodies absorb clicks rather than opening a
                # file/shortcut on the desktop behind a translucent note.
                return True
            return False
        if event.button == 1 and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.get_toplevel().begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        if self.owner.separate and event.button == 3:
            self.owner.note_window.begin_resize_drag(Gdk.WindowEdge.SOUTH_EAST, event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        if event.button != 1:
            return False
        # Delay editing until release: a drag must not insert a blank line or
        # move the text cursor before the window manager takes over the pointer.
        self.gutter_press = (event.x_root, event.y_root, event.y, event.time)
        return True

    def move_gutter(self, widget, event):
        if self.gutter_press is None:
            return False
        x, y, _, _ = self.gutter_press
        if self.drag_check_threshold(int(x), int(y), int(event.x_root), int(event.y_root)):
            self.gutter_press = None
            self.get_toplevel().begin_move_drag(1, int(x), int(y), event.time)
        return True

    def release_gutter(self, widget, event):
        if event.button != 1 or self.gutter_press is None:
            return False
        _, _, y, timestamp = self.gutter_press
        self.gutter_press = None
        self.edit_line(y, timestamp)
        return True

    def edit_line(self, gutter_y, timestamp):
        self.owner.start_note_editing()
        _, y = self.window_to_buffer_coords(Gtk.TextWindowType.LEFT, 0, int(gutter_y))
        end = self.buffer.get_end_iter()
        last_y, height = self.get_line_yrange(end)
        if end.get_line_offset() > 0 and y >= last_y + height:
            self.buffer.insert(end, '\n')
            line = self.buffer.get_end_iter()
        else:
            line, _ = self.get_line_at_y(y)
        self.buffer.place_cursor(line)
        self.grab_focus()
        self.get_toplevel().present_with_time(timestamp)

    def key_press(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval in (Gdk.KEY_s, Gdk.KEY_S):
            self.choose_save_location()
            return True
        if event.keyval == Gdk.KEY_Escape:
            self.owner.finish_note_editing()
            return True
        return False

    def changed(self, buffer):
        self.dirty = True
        self.queue_draw()
        if self.save_source:
            GLib.source_remove(self.save_source)
        self.save_source = GLib.timeout_add(800, self.autosave)

    def autosave(self):
        self.save_source = None
        self.save_now()
        return False

    def choose_save_location(self):
        if self.has_dialog:
            return
        tr = self.owner.tr
        self.save_dialog = Gtk.FileChooserNative.new(tr('保存便签快照'), self.get_toplevel(),
                                                    Gtk.FileChooserAction.SAVE, tr('保存'), tr('取消'))
        self.save_dialog.set_modal(True)
        self.save_dialog.set_do_overwrite_confirmation(True)
        self.save_dialog.set_current_folder(str(self.path.parent))
        self.save_dialog.set_current_name(datetime.now().strftime('note-%Y%m%d-%H%M%S.txt'))
        text_filter = Gtk.FileFilter()
        text_filter.set_name(tr('文本文件'))
        text_filter.add_pattern('*.txt')
        self.save_dialog.add_filter(text_filter)
        all_filter = Gtk.FileFilter()
        all_filter.set_name(tr('所有文件'))
        all_filter.add_pattern('*')
        self.save_dialog.add_filter(all_filter)
        self.save_dialog.connect('response', self.save_response)
        # No nested GTK loop: focus changes must not recursively open dialogs.
        self.save_dialog.show()

    def save_response(self, dialog, response):
        filename = dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
        dialog.destroy()
        self.save_dialog = None
        if filename:
            self.save_snapshot(Path(filename))
        if not self.error_dialog and self.owner.note_enabled:
            self.owner.start_note_editing()
            self.grab_focus()
            self.get_toplevel().present()

    def save_now(self):
        if self.save_source:
            GLib.source_remove(self.save_source)
            self.save_source = None
        if self.load_failed:
            self.report_error(self.owner.tr('便签原文件读取失败，未覆盖保存。请先检查文件权限和编码。'))
            return False
        if not self.dirty:
            return True
        if not self._write_text(self.path):
            return False
        self.dirty = False
        return True

    def save_snapshot(self, destination):
        target = Path(destination)
        if target.resolve() == self.path.resolve():
            self.report_error(self.owner.tr('请选择原稿以外的位置或文件名，快照不会用于后续自动保存。'))
            return False
        return self._write_text(target)

    def _write_text(self, target):
        temporary = None
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                             prefix='.' + target.name + '.', suffix='.tmp', delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(self.buffer.get_text(*self.buffer.get_bounds(), True))
            temporary.replace(target)
            return True
        except OSError as error:
            self.report_error(self.owner.tr('便签保存失败：{error}', error=error))
            return False
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def report_error(self, message):
        if self.error_dialog is not None:
            return False
        dialog = Gtk.MessageDialog(transient_for=self.get_toplevel() if isinstance(self.get_toplevel(), Gtk.Window) else self.owner,
                                   message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.NONE, text=message)
        dialog.add_button(self.owner.tr('关闭'), Gtk.ResponseType.CLOSE)
        self.error_dialog = dialog
        def close(dialog, response):
            dialog.destroy()
            self.error_dialog = None
        dialog.connect('response', close)
        dialog.show()
        return False
