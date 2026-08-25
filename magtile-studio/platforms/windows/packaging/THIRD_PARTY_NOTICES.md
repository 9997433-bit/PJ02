# MagTile Studio — 第三方组件许可声明

本文件随安装包分发 (`licenses/THIRD_PARTY_NOTICES.md`), 列出
MagTile Studio 二进制分发物中包含或静态链接的第三方组件及其许可。
MagTile Studio 本体为专有商业软件, 最终用户许可协议见同目录
`License.rtf` (正式发布前替换为法务审定版本)。

| 组件 | 版本 | 许可 | 用途 |
| --- | --- | --- | --- |
| [nlohmann/json](https://github.com/nlohmann/json) | 3.x (third_party 内嵌) | MIT | JSON 解析 (模型/目录/配置) |
| [SQLite](https://sqlite.org/) | 3.x (third_party amalgamation) | Public Domain | 进度存档 / 设置 / 库存 |
| [GLFW](https://www.glfw.org/) | 3.4 (FetchContent, 静态链接) | zlib/libpng | 窗口与 OpenGL 上下文 (GUI 模式) |
| [Dear ImGui](https://github.com/ocornut/imgui) | 1.91.x (FetchContent, 静态链接) | MIT | 教程 HUD / 模型库界面 |
| [stb_image](https://github.com/nothings/stb) | third_party 内嵌 | MIT / Public Domain 双许可 | 缩略图 PNG 解码 |
| MSVC CRT 运行库 (`vcruntime140*.dll` 等) | 随构建工具链 | [Microsoft 可分发代码条款](https://learn.microsoft.com/visualstudio/releases/2022/redistribution) | C/C++ 运行时 |

仅当以 `-DMAGTILE_BUILD_QT=ON` 构建并打包 Qt 界面 (`magtile_studio_qt.exe`)
时, 分发物额外包含:

| 组件 | 版本 | 许可 | 说明 |
| --- | --- | --- | --- |
| [Qt](https://www.qt.io/) (Core/Gui/Qml/Quick/QuickControls2/OpenGL/QmlModels/Network + 可选 TextToSpeech; 均为 Essentials/LGPLv3 模块) | ≥ 6.4, 动态链接 | LGPLv3 (或商业许可) | LGPL 分发要求: 动态链接、随包提供本声明、允许用户替换 Qt 库; 商用闭源分发前由法务确认走 LGPL 合规或购买 Qt 商业许可 (逐项核对 `scripts/package_qt_desktop.md` 第八节, 自动核对 `scripts/check_lgpl_compliance.sh`) |

各组件完整许可文本以其官方仓库/发行物为准。本文件为声明索引;
若正式发布要求捆绑完整许可文本副本, 在发布前清单
(`scripts/package_windows.md` 第八节) 中一并落实。
