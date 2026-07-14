# 打包为可执行程序（exe）

TypingPlanet 使用 [PyInstaller](https://pyinstaller.org/) 将游戏打包为
Windows 可执行程序（.exe），打包后无需安装 Python 即可双击运行。

## 环境准备

```powershell
uv sync --dev          # 安装开发依赖（含 pyinstaller）
```

或单独安装：

```powershell
uv pip install pyinstaller
```

## 打包（单文件模式，推荐）

项目根目录提供了 `build_exe.py` 一键打包脚本，执行后产出单个 `TypingPlanet.exe`，无需任何其他文件。

```powershell
uv run python build_exe.py
```

产物：`dist/TypingPlanet.exe`（约 38 MB），双击即可运行，拷给别人也只需传这一个文件。

> 单文件模式每次启动时需解压到临时目录，启动比“单文件夹”模式慢 2-3 秒，运行后无区别。

### 手动执行（等价命令）

如果不用脚本，也可直接运行 PyInstaller：

```powershell
pyinstaller --onefile --windowed --name TypingPlanet ^
    --collect-all pygame --collect-all typingplanet ^
    --hidden-import pydantic --hidden-import typer ^
    --exclude-module tkinter --exclude-module unittest ^
    --noconfirm --clean ^
    run.py
```

## 备选：单文件夹模式（启动更快）

如果希望启动更快，可使用 spec 文件打包为文件夹：

```powershell
pyinstaller TypingPlanet.spec --noconfirm --clean
```

产物在 `dist/TypingPlanet/` 文件夹中，入口为 `dist/TypingPlanet/TypingPlanet.exe`，需将整个文件夹一起分发。

## 命令参数说明

| 参数 | 作用 |
|---|---|
| `--onefile` | 打包为单个 exe 文件（不加则为文件夹） |
| `--windowed` / `--noconsole` | 不显示控制台窗口（游戏推荐） |
| `--name TypingPlanet` | 输出文件名 |
| `--collect-all pygame` | 收集 pygame-ce 的全部子模块与数据 |
| `--collect-all typingplanet` | 收集本项目的全部模块 |
| `--hidden-import pydantic` | 确保 pydantic v2 的 Rust 核心被包含 |
| `--noconfirm` | 覆盖已有产物不询问 |
| `--clean` | 清理上次缓存后重新打包 |
| `run.py` | 入口脚本（使用绝对导入，避免相对导入报错） |

## 运行打包后的程序

双击 `TypingPlanet.exe` 即可启动。程序无控制台窗口，日志写入：

```
%LOCALAPPDATA%\TypingPlanet\TypingPlanet\typingplanet.log
```

用户数据（档案、进度、数据库）同样存储在系统用户目录：

```
%LOCALAPPDATA%\TypingPlanet\TypingPlanet\typingplanet.db
```

若该目录不可写，程序会自动回退到 exe 所在目录下的 `.typingplanet/` 文件夹。

## 添加图标

准备一个 `.ico` 图标文件（如 `icon.ico`），在 `build_exe.py` 的 cmd 列表中加入 `"--icon", "icon.ico"`，或命令行追加 `--icon icon.ico`。

## 常见问题

**打包后启动报错 "Failed to execute script"**

使用控制台模式重新打包以查看错误信息：将 `build_exe.py` 中的 `--windowed` 改为 `--console`，或命令行不加 `--windowed`。

**字体显示为方框**

程序使用系统字体（微软雅黑等），Windows 自带这些字体，一般不会出问题。
若在精简版 Windows 上运行，确保系统已安装中文字体。

**杀毒软件误报**

PyInstaller 打包的 exe 可能被部分杀毒软件误报。可将 exe 加入白名单，
或使用代码签名证书对 exe 进行签名。

**打包体积过大**

可在 spec 中增加 `excludes` 排除不需要的模块，或使用 UPX 压缩
（需系统已安装 UPX）。
