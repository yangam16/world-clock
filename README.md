# World Clock · 世界时钟与便签

[简体中文](README.md) | [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/yangam16/world-clock/actions/workflows/ci.yml/badge.svg)](https://github.com/yangam16/world-clock/actions/workflows/ci.yml)

面向 Ubuntu 22.04 的轻量 GTK 3 桌面工具。用紧凑横版窗口查看多个时区的日期与时间，通过系统顶栏管理时钟和便签。

本项目基于LLM开发完成，欢迎提出[Issue](https://github.com/yangam16/world-clock/issues)。

## 功能

- **多时区时钟**：默认跟随系统时区，可搜索添加城市，自动处理夏令时和跨日日期。
- **桌面布局**：独立窗口或统一列表，底部横排避开 Dock，支持置顶、透明度和位置保存。
- **便签**：行号、点击编辑、拖动、自动保存原稿；Ctrl+S 导出独立快照。
- **中英文界面**：顶栏菜单即时切换并记住选择。
- **桌面快捷方式**：安装后可双击图标或从应用菜单启动，无需每次打开终端。

## 快速开始

运行环境：**Ubuntu 22.04、Python 3.10+、GTK 3**。已验证 X11 桌面；需要启用 Ubuntu AppIndicators。

```bash
sudo apt update
sudo apt install git python3 python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 gir1.2-ayatanaappindicator3-0.1 tzdata gnome-shell-extension-appindicator

git clone https://github.com/yangam16/world-clock.git
cd world-clock
./run.sh --check
python3 install.py --desktop
```

回到桌面，右键 **World Clock / 世界时钟** 图标选择 **允许启动**，然后双击。也可在应用菜单搜索“世界时钟”。控制菜单位于 Ubuntu **右上角系统顶栏**。

仓库中的 `assets/world-clock.desktop` 是模板，应由安装器生成本机快捷方式。完整步骤和常见问题见[桌面图标教程](docs/installation.zh-CN.md)。

## 文档

| 主题 | 中文 | English |
|---|---|---|
| 安装、桌面图标、升级 | [安装教程](docs/installation.zh-CN.md) | [Installation](docs/installation.en.md) |
| 时钟、便签、快照和数据位置 | [使用指南](docs/usage.zh-CN.md) | [User guide](docs/usage.en.md) |
| 开发、测试和源码打包 | [开发指南](docs/development.md) | [Development](docs/development.md) |

- [贡献指南](CONTRIBUTING.md) · [更新记录](CHANGELOG.md)
- [安全报告](SECURITY.md) · [第三方依赖](THIRD_PARTY.md)
- [版本下载](https://github.com/yangam16/world-clock/releases) · [反馈问题](https://github.com/yangam16/world-clock/issues/new/choose)

## 项目结构

```text
world-clock/
├── src/world_clock/       # 应用包：窗口、便签、中英文界面
├── assets/                # 桌面启动器模板
├── docs/                  # 安装、使用和开发文档
├── scripts/               # 用户安装器与源码打包工具
├── tests/                 # 自动检查与 X11 GUI 回归
├── .github/               # CI、Issue 表单、PR 模板
├── pyproject.toml         # Python 项目元数据
├── run.sh                 # 保留的源码启动入口
├── install.py             # 保留的桌面安装入口
├── README.md / README.en.md
└── LICENSE
```

## 数据与兼容性

原稿始终自动保存到**程序目录的 `note.txt`**，桌面安装后默认是 `~/.local/share/world-clock/note.txt`。Ctrl+S 导出的快照不会随之后的编辑更新。配置位于 `~/.config/world-clock/`，遵循 XDG 设置。安装升级保留已有原稿和配置。

目前已在 Ubuntu 22.04 X11、单屏和底部 Dock 下验证。Wayland、其他桌面及多屏缩放组合尚未验收；没有开机自启、富文本或多便签功能。更多验证边界见[使用指南](docs/usage.zh-CN.md)。

AppImage 制作脚本、工具链和缓存仅在本地保留，不随 Git 源码分发。维护者可将 AppImage 成品手动上传到 Releases，用户可按实际附件情况下载。

## 参与项目

欢迎通过 [Issue](https://github.com/yangam16/world-clock/issues/new/choose) 报告 Bug 或提出功能建议，也欢迎提交 Pull Request。请使用合成文字复现问题，上传前去除便签、账号、凭据和桌面截图中的隐私信息。

安全漏洞请按 [SECURITY.md](SECURITY.md) 私下报告。源码采用 [MIT 许可证](LICENSE)；运行时依赖保留各自许可证。
