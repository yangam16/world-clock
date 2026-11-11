# 安装与桌面图标

[项目首页](../README.md) · [English](installation.en.md)

## 环境与安装

已在一台 Ubuntu 22.04 **X11** 桌面验证。需要 Python 3.10+、GTK 3 和启用的 Ubuntu AppIndicators 扩展。

先安装系统依赖：

```bash
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0 gir1.2-pango-1.0 gir1.2-ayatanaappindicator3-0.1 tzdata gnome-shell-extension-appindicator
```

在“扩展”中确认 **Ubuntu AppIndicators** 已启用。如图标服务不存在，程序会提示并退出，避免穿透窗口失去控制入口。

克隆项目，检查依赖，并安装桌面图标：

```bash
git clone https://github.com/yangam16/world-clock.git
cd world-clock
./run.sh --check
python3 install.py --desktop
```

`--check` 仅验证依赖能否导入，不证明桌面显示、系统图标和鼠标交互正常。

安装器无需 sudo。完成后按照下方桌面图标教程启动即可。如果只需要应用菜单入口，不需要桌面图标，可改用：

```bash
python3 install.py
```

安装器将程序复制到 `$XDG_DATA_HOME/world-clock`（默认 `~/.local/share/world-clock`），生成应用菜单入口和 `~/.local/bin/world-clock` 命令。系统依赖仍需先安装，用户配置和便签不会被改写。再次运行安装器可更新程序；更新前先从顶栏菜单退出旧实例。

## 克隆后如何使用 .desktop 文件

### 1. 生成指向安装目录的桌面图标

在克隆得到的 `world-clock` 目录中执行一次：

```bash
python3 install.py --desktop
```

安装器会自动检测桌面目录（包括中文的“桌面”目录），复制程序，并生成使用绝对路径的启动入口：

| 文件 | 用途 |
|---|---|
| 克隆目录中的 `assets/world-clock.desktop` | 启动器模板，`Exec=world-clock`；安装器会替换为实际安装路径 |
| `~/.local/share/applications/world-clock.desktop` | 供 GNOME 应用菜单使用的入口 |
| `$(xdg-user-dir DESKTOP)/world-clock.desktop` | 桌面上的可双击快捷方式 |

表中的安装位置使用默认 XDG 路径。不要直接双击克隆目录中的模板，或只把模板复制到桌面；模板尚未绑定本机安装位置，系统也不一定能在 PATH 中找到 `world-clock`。运行安装器即可生成正确的文件，无需手工修改 `Exec`。

### 2. 允许启动并双击

1. 回到 Ubuntu 桌面，找到 **World Clock / 世界时钟** 图标。
2. 如果它显示为普通文本文件，或提示未受信任，右键该图标，选择 **允许启动 / Allow Launching**。
3. 双击图标启动。日常使用不需要再打开终端。
4. 也可按 **Super** 键，在应用菜单搜索 **World Clock / 世界时钟**；可将应用加入收藏，方便从 Dock 启动。

安装器已设置可执行权限并尝试标记“受信任”。如果右键没有“允许启动”，在文件管理器中打开该文件的 **属性 → 权限**，勾选 **允许将文件作为程序执行**，再回到桌面操作。如果整个桌面都不显示文件图标，在“扩展”中检查 **Desktop Icons NG (DING)** 是否启用。

### 3. 找到控制菜单

程序启动后，在 Ubuntu **右上角系统顶栏**找到时钟图标。添加时区、显示便签、语言切换和退出都在这个菜单中。时钟默认无标题栏并开启穿透，不需要在时钟正文上寻找菜单。重复双击桌面快捷方式不会创建第二个实例。

### 更新或重新生成图标

先在顶栏菜单中退出正在运行的实例，再回到克隆目录执行：

```bash
git pull --ff-only
python3 install.py --desktop
```

随后重新双击桌面图标。安装器会更新程序和两个启动入口，保留安装目录中的便签原稿及个人配置。安装后的图标指向安装副本，不依赖克隆目录的位置。

### 可选：只从源码运行

在克隆目录执行 `./run.sh` 可直接运行源码；这种方式下原稿位于克隆目录的 `note.txt`，而桌面安装副本的原稿位于安装目录。切换运行方式前请退出旧实例并备份原稿，需要时将原稿复制到目标程序目录。
