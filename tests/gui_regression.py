"""X11 integration checks using synthetic notes and actual mouse/key events.

Run from a graphical session: python3 tests/gui_regression.py
Only temporary configuration/note files are used. The pointer is restored on exit.
"""
import ctypes
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import shutil

ROOT = Path(__file__).resolve().parents[1]
TEMP = tempfile.TemporaryDirectory(prefix='world-clock-regression-')
APP_ROOT = Path(TEMP.name) / 'app'
APP_ROOT.mkdir()
shutil.copytree(ROOT / 'src', APP_ROOT / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
shutil.copy2(ROOT / 'run.sh', APP_ROOT / 'run.sh')
for fallback in ROOT.glob('vendor/usr/lib/*/girepository-1.0/AyatanaAppIndicator3-0.1.typelib'):
    target = APP_ROOT / fallback.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fallback, target)
sys.path.insert(0, str(APP_ROOT / 'src'))
os.environ['XDG_CONFIG_HOME'] = TEMP.name
os.environ['LANG'] = 'en_US.UTF-8'
legacy = Path(TEMP.name) / 'world-clock/note.txt'
legacy.parent.mkdir()
legacy.write_text('Legacy synthetic note', encoding='utf-8')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
from gi.repository import Gtk, Gdk, GdkX11, GLib

x11 = ctypes.CDLL('libX11.so.6')
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XFlush.argtypes = [ctypes.c_void_p]
display = x11.XOpenDisplay(None)
if not display:
    raise SystemExit('A running X11 graphical session is required.')
xtst = ctypes.CDLL('libXtst.so.6')
xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x11.XKeysymToKeycode.restype = ctypes.c_uint
pointer = Gdk.Display.get_default().get_default_seat().get_pointer()
_, pointer_x, pointer_y = pointer.get_position()
failures = []
background_clicks = []
app = None
background = None
original_main = Gtk.main


def move(x, y):
    xtst.XTestFakeMotionEvent(display, -1, int(x), int(y), 0)
    x11.XFlush(display)


def click():
    for pressed in (True, False):
        xtst.XTestFakeButtonEvent(display, 1, int(pressed), 0)
    x11.XFlush(display)


def control_s():
    control = x11.XKeysymToKeycode(display, Gdk.KEY_Control_L)
    s = x11.XKeysymToKeycode(display, Gdk.KEY_s)
    for key, pressed in [(control, 1), (s, 1), (s, 0), (control, 0)]:
        xtst.XTestFakeKeyEvent(display, key, pressed, 0)
    x11.XFlush(display)


def later(callback, delay=350):
    def guarded():
        try:
            callback()
        except Exception as error:
            import traceback
            traceback.print_exc()
            failures.append(repr(error))
            finish()
        return False
    GLib.timeout_add(delay, guarded)


def text():
    buffer = app.note_editor.get_buffer()
    return buffer.get_text(*buffer.get_bounds(), True)


def start():
    global app, background
    app = next(w for w in Gtk.Window.list_toplevels() if hasattr(w, 'indicator_menu'))
    assert text() == 'Legacy synthetic note'
    assert (APP_ROOT / 'note.txt').read_text() == 'Legacy synthetic note'
    app.change_language('en')
    app.note_item.set_active(True)
    background = Gtk.Window(title='World Clock synthetic click receiver')
    background.set_default_size(600, 400)
    receiver = Gtk.EventBox()
    receiver.add(Gtk.Label(label='Synthetic test background'))
    receiver.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    receiver.connect('button-press-event', lambda widget, event: background_clicks.append(event.type) or True)
    background.add(receiver)
    background.move(350, 350)
    background.show_all()
    app.note_window.set_keep_above(True)
    app.note_window.move(400, 400)
    app.note_window.present()
    app.note_editor.get_buffer().set_text('Synthetic note\nSecond line')
    later(double_click_locked_body)


def double_click_locked_body():
    assert app.locked and not app.note_editor.get_editable()
    x, y = app.note_window.get_position()
    move(x + 160, y + 45)
    click()
    later(lambda: (click(), later(check_body)), 80)


def check_body():
    assert len(background_clicks) >= 2, background_clicks
    cursor = app.note_editor.get_window(Gtk.TextWindowType.TEXT).get_cursor()
    arrow = Gdk.Cursor.new_from_name(Gdk.Display.get_default(), 'default')
    assert cursor.get_image().get_pixels() == arrow.get_image().get_pixels()
    hit, _, _ = pointer.get_window_at_position()
    assert hit == background.get_child().get_window(), hit
    assert not app.note_editor.get_editable()
    assert text() == 'Synthetic note\nSecond line'
    drag_body_through(lambda: drag_gutter(check_gutter_targets))


def drag_body_through(done):
    before = tuple(app.note_window.get_position())
    original = text()
    clicks = len(background_clicks)
    _, x, y = app.note_editor.get_window(Gtk.TextWindowType.TEXT).get_origin()
    move(x + 100, y + 20)
    xtst.XTestFakeButtonEvent(display, 1, 1, 0)
    x11.XFlush(display)
    def release():
        move(x + 140, y + 50)
        xtst.XTestFakeButtonEvent(display, 1, 0, 0)
        x11.XFlush(display)
        later(check)
    def check():
        assert tuple(app.note_window.get_position()) == before
        assert len(background_clicks) > clicks
        assert text() == original
        assert not app.note_editor.get_editable()
        done()
    later(release)


def drag_gutter(done):
    before = tuple(app.note_window.get_position())
    original = text()
    origin = app.note_editor.get_window(Gtk.TextWindowType.LEFT).get_origin()
    x, y = origin[-2:]
    move(x + 20, y + 20)
    xtst.XTestFakeButtonEvent(display, 1, 1, 0); x11.XFlush(display)
    def start_motion():
        move(x + 45, y + 35)
        later(end_motion, 180)
    def end_motion():
        move(x + 100, y + 60)
        later(release, 180)
    def release():
        xtst.XTestFakeButtonEvent(display, 1, 0, 0); x11.XFlush(display)
        later(check_drag)
    def check_drag():
        after = tuple(app.note_window.get_position())
        assert after[0] - before[0] > 50 and after[1] - before[1] > 20, (before, after)
        assert text() == original
        assert not app.note_editor.get_editable()
        done()
    later(start_motion, 150)


def check_gutter_targets():
    # Blank gutter space must not activate editing or append a newline.
    origin = app.note_editor.get_window(Gtk.TextWindowType.LEFT).get_origin()
    x, y = origin[-2:]
    move(x + 20, y + 180); click()
    later(check_row_gap)


def check_row_gap():
    editor = app.note_editor
    assert not editor.get_editable() and text() == 'Synthetic note\nSecond line'
    top, height = editor.get_line_yrange(editor.get_buffer().get_start_iter())
    assert height >= 28, height
    _, wy = editor.buffer_to_window_coords(Gtk.TextWindowType.LEFT, 0, top + 1)
    _, x, y = editor.get_window(Gtk.TextWindowType.LEFT).get_origin()
    move(x + 20, y + wy); click()
    later(select_second_row)


def select_second_row():
    editor = app.note_editor
    assert not editor.get_editable()
    top, height = editor.get_line_yrange(editor.get_buffer().get_iter_at_line(1))
    _, wy = editor.buffer_to_window_coords(Gtk.TextWindowType.LEFT, 0, top + height // 2)
    _, x, y = editor.get_window(Gtk.TextWindowType.LEFT).get_origin()
    move(x + 20, y + wy); click()
    later(check_second_row)


def check_second_row():
    editor = app.note_editor
    assert editor.get_editable()
    assert editor.get_buffer().get_iter_at_mark(editor.get_buffer().get_insert()).get_line() == 1
    drag_body_through(lambda: drag_gutter(select_next_blank_row))


def select_next_blank_row():
    editor = app.note_editor
    top, height = editor.get_line_yrange(editor.get_buffer().get_end_iter())
    _, wy = editor.buffer_to_window_coords(Gtk.TextWindowType.LEFT, 0, top + height + height // 2)
    _, x, y = editor.get_window(Gtk.TextWindowType.LEFT).get_origin()
    move(x + 20, y + wy); click()
    later(check_next_blank_row)


def check_next_blank_row():
    editor = app.note_editor
    assert editor.get_editable() and text() == 'Synthetic note\nSecond line\n'
    assert editor.get_buffer().get_iter_at_mark(editor.get_buffer().get_insert()).get_line() == 2
    app.note_window.get_window().get_display().sync()
    Gdk.pixbuf_get_from_window(app.note_window.get_window(), 0, 0, *app.note_window.get_size()).savev('/tmp/world-clock-note-row-targets.png', 'png', [], [])
    editor.get_buffer().set_text('Synthetic note\nSecond line')
    # Real single click on the gutter enters editing; then real Ctrl+S.
    origin = app.note_editor.get_window(Gtk.TextWindowType.LEFT).get_origin()
    x, y = origin[-2:]
    move(x + 20, y + 12)
    click()
    later(save_shortcut)


def save_shortcut():
    assert app.note_editor.get_editable()
    control_s()
    later(check_chooser, 700)


def check_chooser():
    chooser = app.note_editor.save_dialog
    assert chooser is not None and chooser.get_visible()
    assert chooser.get_title() == 'Save note snapshot'
    # This callback running while the chooser is visible proves the event loop
    # remains live. Repeated save requests must not create another dialog.
    app.note_editor.choose_save_location()
    assert app.note_editor.save_dialog is chooser
    chooser.emit('response', Gtk.ResponseType.CANCEL)
    later(save_to_selected_location)


def save_to_selected_location():
    assert app.note_editor.save_dialog is None
    app.note_editor.choose_save_location()
    chooser = app.note_editor.save_dialog
    chooser.set_current_folder(TEMP.name)
    chooser.set_current_name('chosen-note.txt')
    later(accept_location, 500)


def accept_location():
    chooser = app.note_editor.save_dialog
    assert Path(chooser.get_filename()) == Path(TEMP.name) / 'chosen-note.txt', chooser.get_filename()
    chooser.emit('response', Gtk.ResponseType.ACCEPT)
    later(check_saved)


def check_saved():
    target = Path(TEMP.name) / 'chosen-note.txt'
    assert target.read_text() == 'Synthetic note\nSecond line'
    config = json.loads((Path(TEMP.name) / 'world-clock/settings.json').read_text())
    assert 'note_path' not in config
    assert app.note_editor.path == APP_ROOT / 'note.txt'
    app.note_editor.get_buffer().insert_at_cursor('!')
    later(check_autosave, 1100)


def check_autosave():
    assert (Path(TEMP.name) / 'chosen-note.txt').read_text() == 'Synthetic note\nSecond line'
    assert (APP_ROOT / 'note.txt').read_text() == text()
    assert text() != (Path(TEMP.name) / 'chosen-note.txt').read_text()
    assert legacy.read_text() == 'Legacy synthetic note'
    # Save failure is nonblocking, retains the current file and never recursively
    # creates error dialogs during focus loss.
    current = app.note_editor.path
    assert not app.note_editor.save_snapshot(Path('/proc/world-clock-write-test/note.txt'))
    assert app.note_editor.path == current
    later(check_error)


def check_error():
    dialog = app.note_editor.error_dialog
    assert dialog is not None
    assert len([w for w in Gtk.Window.list_toplevels() if isinstance(w, Gtk.MessageDialog)]) == 1
    dialog.response(Gtk.ResponseType.CLOSE)
    old_editor = app.note_editor
    before = text()
    app.change_language('zh_CN')
    assert app.note_item.get_label() == '显示便签'
    assert app.note_editor is old_editor and text() == before
    app.change_language('en')
    assert app.note_item.get_label() == 'Show note'
    assert app.city_label('America/Los_Angeles') == 'Los Angeles'
    assert app.note_editor is old_editor and text() == before
    app.separate_item.set_active(False)
    assert app.note_scroll.get_parent() == app.root
    app.separate_item.set_active(True)
    assert app.note_scroll.get_parent() == app.note_window
    config = json.loads((Path(TEMP.name) / 'world-clock/settings.json').read_text())
    assert config['language'] == 'en'
    print('PASS: body click/drag pass-through before/after editing, default pointer, gutter drag, exact row targets/gaps/blank line, row spacing, Ctrl+S snapshots, autosave, language switch and window modes', flush=True)
    finish()


def finish():
    if app is not None:
        if app.note_editor.save_dialog:
            app.note_editor.save_dialog.destroy()
            app.note_editor.save_dialog = None
        if app.note_editor.error_dialog:
            app.note_editor.error_dialog.destroy()
            app.note_editor.error_dialog = None
        app.quit()
    if background:
        background.destroy()
    move(pointer_x, pointer_y)
    Gtk.main_quit()


def checked_main():
    later(start, 600)
    original_main()


Gtk.main = checked_main
sys.argv = ['world-clock']
runpy.run_module('world_clock', run_name='__main__', alter_sys=True)
TEMP.cleanup()
if failures:
    raise SystemExit('; '.join(failures))
