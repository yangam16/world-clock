"""Plain-text sticky note with a clickable, scrolling line-number gutter."""
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo


class NoteEditor(Gtk.TextView):
    GUTTER = 44

    def __init__(self, owner, path):
        super().__init__()
        self.owner = owner
        self.path = Path(path)
        self.dirty = False
        self.save_source = None
        self.load_failed = False
        self.gutter_press = None
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
        try:
            text = self.path.read_text(encoding='utf-8')
        except FileNotFoundError:
            text = ''
        except (OSError, UnicodeError) as error:
            text = ''
            self.load_failed = True
            GLib.idle_add(self.report_error, f'便签读取失败，已禁止覆盖原文件：{error}')
        self.buffer.set_text(text)
        self.buffer.connect('changed', self.changed)
        self.connect('button-press-event', self.click_gutter)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect('motion-notify-event', self.move_gutter)
        self.connect('button-release-event', self.release_gutter)
        self.connect('key-press-event', self.key_press)

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
            self.save_now()
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

    def save_now(self):
        if self.save_source:
            GLib.source_remove(self.save_source)
            self.save_source = None
        if self.load_failed:
            self.report_error('便签原文件读取失败，未覆盖保存。请先检查文件权限和编码。')
            return False
        if not self.dirty:
            return True
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(self.buffer.get_text(*self.buffer.get_bounds(), True), encoding='utf-8')
            temporary.replace(self.path)
            self.dirty = False
            return True
        except OSError as error:
            self.report_error(f'便签保存失败：{error}')
            return False

    def report_error(self, message):
        dialog = Gtk.MessageDialog(transient_for=self.get_toplevel() if isinstance(self.get_toplevel(), Gtk.Window) else self.owner,
                                   message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text=message)
        dialog.run()
        dialog.destroy()
        return False
