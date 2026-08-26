# Windows 打包资产

本目录承载 Windows 安装器资产。操作手册见 `scripts/package_windows.md`。

## 现有文件

| 文件 | 作用 |
| --- | --- |
| `CPackWindows.cmake` | 安装布局 + CPack 配置 (NSIS 安装器 / 便携 ZIP / WiX 元数据 / 模型子集开关 `MAGTILE_PACKAGE_MODEL_SET` / 许可文件安装), 由根 CMakeLists 在非 Android 平台 include; 版本号取自根 `project(VERSION)` |
| `Product.wxs` | WiX v4 MSI 描述文件: 独立于 CPack 的企业分发路径, 版本号经 `-d Version=` 注入; 收割 data (可指向子集 staging 目录) 与 licenses |
| `License.rtf` | NSIS / MSI 安装向导许可页 + 随包 `licenses/` 的 EULA 文本 (**占位, 发布前须替换为法务审定版本**) |
| `THIRD_PARTY_NOTICES.md` | 随包 `licenses/` 的第三方组件许可声明 (nlohmann/json、SQLite、GLFW、ImGui、stb、MSVC CRT; Qt 版另含 Qt LGPL 条目) |
| `starter_models.txt` | starter 子集清单: 免费层精选 30 模型 (含旗舰球道), 由 `tools/make_data_subset.py` 消费 |

两条打包路径 (CPack WIX 与 Product.wxs) 共用同一 UpgradeCode
`6FE5F9D7-79A7-4829-B13A-8C3B1517CA61`, 保证互相原地升级;
**此 GUID 永久固定, 严禁改动**。

## 计划补入 (发布前, 见 scripts/package_windows.md 第七节清单)

- `icon.ico` / `banner.bmp` / `dialog.bmp` — 安装器图标与界面素材
- `sign.ps1` — signtool 代码签名脚本
