# TypingPlanet 打字星球

面向儿童的本地单机打字练习游戏。逐字高亮、虚拟键盘提示下一步按键、星级与
闯关解锁、多用户进度，全部数据存在本地 SQLite，无需联网、无需外部数据库。

## 功能

- 键位练习（主键位行 / 上排 / 下排 / 全字母）与词语、短句练习
- 主题切换：基础训练 / 一年级语文（看汉字打拼音）/ 大小写练习（大写字母与小写字母对应），每个主题即一个内容插件
- 阻塞式逐字输入：按对才前进，即时正误反馈，适合初学
- 虚拟键盘高亮下一个要按的键，主键位 F/J 标记定位凸点
- 实时 WPM / 准确率 / 进度，结算页星级动画
- 关卡顺序解锁：前 3 关默认开放，后续需前一关获得 ≥1 星
- 多用户档案，各自独立进度与最佳成绩
- 合成音效（按键 / 错误 / 完成 / 得星），不依赖任何音频文件
- 可扩展：内容包、游戏模式、奖励策略、主题均以接口契约插件化

## 技术栈

| 层 | 选型 |
|---|---|
| 语言/包管理 | Python 3.13 + uv |
| 游戏引擎 | pygame-ce |
| 存储 | sqlite3（标准库）+ 仓库模式 + 版本化迁移 |
| 建模/配置 | dataclasses + pydantic v2 |
| CLI | typer |
| 日志 | loguru |
| 测试 | pytest |

## 快速开始

```powershell
uv sync                 # 安装依赖（含可编辑安装本包）
uv run typingplanet     # 启动游戏
uv run pytest -q        # 运行测试（53 个）
```

也可用 `python -m typingplanet` 启动。

### 启动参数

```
typingplanet [--profile NAME] [--db PATH] [--fullscreen] [--width N] [--height N] [--fps N] [--debug]
```

- `--profile` 按名称选择用户档案
- `--db` 指定自定义数据库路径（测试/便携用）
- `--debug` 输出详细日志（含每次按键的 key/unicode/推导字符），用于定位输入问题

## 操作

| 按键 | 作用 |
|---|---|
| `↑` `↓` / 鼠标滚轮 | 选择关卡 |
| `Enter` / 鼠标点击 | 开始关卡 |
| `<` `>` `+` | 切换 / 新建用户 |
| `M`(菜单) / `F1`(练习中) | 静音切换 |
| `Esc` | 返回 / 退出 |
| 字母、数字、符号、`空格`、`回车` | 打字 |

结算页：`R` 重试，`Enter` 下一关，`Esc` 返回菜单。

## 故障排查 / 日志

启动时控制台会打印日志，同时写入日志文件（启动日志里含 `log file:` 路径）。
默认在系统用户目录下；若该目录不可写，回退到当前目录 `.typingplanet/data/`。

- 按键没反应？用 `uv run typingplanet --debug` 启动，进关卡按键时看控制台是否出现
  `KEYDOWN key=... unicode=... -> char=...`。出现且有 `char` 说明输入已识别；
  若 `unicode=''` 而 `char` 仍正确，是输入法（IME）拦截了字符——程序已用键码回退处理。
  若按键时完全没有日志行，说明窗口可能没获得焦点，点一下窗口再试。
- 中文输入法（IME）开着也能打字：输入层在 `event.unicode` 为空时按物理键码推导字符，
  并在启动时调用 `pygame.key.stop_text_input()` 抑制 IME 组合。如仍异常，切到英文输入法最稳。
- 想清空进度：删除数据库文件（启动日志里的 `db:` 路径）。

## 架构

分层 + 接口契约，业务逻辑与引擎、存储解耦，便于扩展与单测。

```
src/typingplanet/
  domain/      领域模型（Profile/Lesson/Attempt/Progress）+ 仓储 Protocol
  data/        SQLite：迁移、连接、Repository 实现、DataStore 门面
  services/    TypingSession 评测、星级 Scorer、Progression 解锁
  plugins/     契约（LessonProvider/GameMode/RewardStrategy）+ Registry + 加载器
  content/     内置内容提供者、经典模式、默认奖励策略
  core/        引擎主循环、场景管理、输入（IME 安全）、资源、合成音频、粒子、渲染、主题、星空背景
  ui/          Button / 星级 / 进度条 / 虚拟键盘
  scenes/      主菜单 / 练习 / 结算
  config/      跨平台路径、设置（pydantic + JSON）
  cli.py       typer 入口
```

打字核心 `services/typing.TypingSession` 与输入解析 `core/input.char_from_keydown`
均不依赖显示，可纯单测。

## 扩展

所有可扩展点都是 `typing.Protocol`，注册到 `Registry`：

| 契约 | 作用 | 实现要点 |
|---|---|---|
| `LessonProvider` | 提供关卡内容 | `provider_id`、`lessons()`、`get_lesson(id)` |
| `GameMode` | 定义玩法 | `build_session(lesson)`、`is_finished(session)` |
| `RewardStrategy` | 奖励规则 | `on_key()`、`on_complete()` 返回事件（声音/粒子/浮字） |
| `*Repository` | 数据访问 | 仓储 Protocol，可替换存储后端 |

每个注册的 `LessonProvider` 会作为菜单里的一个主题标签出现，解锁与进度按主题独立计算。

### 新增一个内容包（第三方插件）

创建一个包，暴露 `register(registry)` 函数，并在其 `pyproject.toml` 注册入口点：

```python
# my_pack/plugin.py
from typingplanet.domain.models import Difficulty, Lesson, Segment
from typingplanet.plugins.contracts import LessonProvider

class MyProvider:
    provider_id = "my-pack"
    name = "我的内容包"
    def __init__(self):
        self._lessons = [Lesson(
            id="my-pack:hello", provider_id=self.provider_id,
            title="你好", difficulty=Difficulty.EASY, order=100,
            segments=(Segment(text="hello world"),))]
        self._by_id = {l.id: l for l in self._lessons}
    def lessons(self): return list(self._lessons)
    def get_lesson(self, lid): return self._by_id.get(lid)

def register(registry):
    registry.register_lesson_provider(MyProvider())
```

```toml
# my_pack/pyproject.toml
[project.entry-points."typingplanet.plugins"]
my_pack = "my_pack.plugin"
```

安装该包后，`build_registry()` 会自动发现并通过入口点加载，无需改动主程序。
内置内容同样走这套机制（见 `plugins/loader.load_builtin`）。

## 数据位置

默认使用系统用户目录（`platformdirs`）。若该目录不可写，自动回退到当前工作目录
下的 `.typingplanet/`，确保任何机器都能启动。可用环境变量覆盖：

- `TYPINGPLANET_DATA_DIR`
- `TYPINGPLANET_CONFIG_DIR`

## 打包

使用 PyInstaller 打包为 Windows 可执行程序，无需安装 Python 即可运行。详见 [PACKAGING.md](PACKAGING.md)。

```powershell
uv sync --dev                      # 安装 pyinstaller
uv run python build_exe.py         # 打包为单文件 exe，产物在 dist/TypingPlanet.exe
```

## 后续路线

- 拼音/中文输入模式、更多 GameMode（限时、消字、Boss 战）
- 成就系统界面、统计图表
- 主题皮肤切换、可配置虚拟键盘指法配色
