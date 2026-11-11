"""Small runtime-switchable Chinese/English UI catalog."""
import os

EN = {
    '世界时钟': 'World Clock',
    '世界时钟 · 便签': 'World Clock · Note',
    '24 小时制 · 自动切换夏令时 · 使用系统时钟': '24-hour time · Automatic DST · System clock',
    '鼠标穿透（取消勾选以操作时钟）': 'Clock click-through (uncheck to interact)',
    '窗口置顶': 'Always on top', '添加时区…': 'Add time zone…',
    '透明度…': 'Opacity…', '显示便签': 'Show note',
    '保存便签快照…（Ctrl+S）': 'Save note snapshot… (Ctrl+S)',
    '每个城市独立窗口': 'Separate clock windows',
    '底部横排（避开 Dock）': 'Align along bottom (above Dock)',
    '屏幕 {number} · {model} · {width}×{height}': 'Display {number} · {model} · {width}×{height}',
    '退出世界时钟': 'Quit World Clock', '时钟透明度': 'Clock opacity',
    '完成': 'Done', '不透明度（30%–100%）': 'Opacity (30%–100%)',
    '配置保存失败：{error}': 'Could not save preferences: {error}',
    '移除此时区': 'Remove this time zone',
    '点击“添加时区”选择城市': 'Choose a city using “Add time zone”',
    '选择时区': 'Choose a time zone', '取消': 'Cancel', '添加': 'Add',
    '搜索城市或时区，例如 洛杉矶 / New York / Asia': 'Search a city or zone, e.g. Los Angeles / New York / Asia',
    '城市': 'City', '时区': 'Time zone',
    'Ubuntu 顶栏图标服务未启用': 'Ubuntu top-bar indicator service is unavailable',
    '请在“扩展”中启用 Ubuntu AppIndicators 后重新运行世界时钟。': 'Enable Ubuntu AppIndicators in Extensions, then start World Clock again.',
    '便签读取失败，已禁止覆盖原文件：{error}': 'Could not read the note; the original file will not be overwritten: {error}',
    '便签原文件读取失败，未覆盖保存。请先检查文件权限和编码。': 'The original note could not be read. Check its permissions and encoding before overwriting it.',
    '便签保存失败：{error}': 'Could not save the note: {error}',
    '保存便签快照': 'Save note snapshot', '保存': 'Save',
    '请选择原稿以外的位置或文件名，快照不会用于后续自动保存。': 'Choose a different file from the live draft. Snapshots are not used for subsequent autosaves.',
    '文本文件': 'Text files', '所有文件': 'All files', '关闭': 'Close',
}


class Translator:
    def __init__(self, language=None):
        if language not in ('en', 'zh_CN'):
            locale = os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES') or os.environ.get('LANG', '')
            language = 'zh_CN' if locale.lower().startswith('zh') else 'en'
        self.language = language

    def __call__(self, text, **values):
        return (EN.get(text, text) if self.language == 'en' else text).format(**values)
