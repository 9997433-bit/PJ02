# Qt 商用界面 桌面打包指南 (QT-6)

本文是 `magtile_studio_qt` (Qt 6 + QML 商用界面) 从源码到分发物的
操作手册: 构建、CPack 打包形态 (与 `magtile_app` 并存 / Qt-only)、
Qt 运行库部署 (windeployqt / macdeployqt)、starter 模型子集与
LGPL 合规清单。通用打包基座 (NSIS/ZIP/WiX、版本号管理、CI 流水线)
见 `scripts/package_windows.md`, 两文共用同一套 CPack 配置
(`platforms/windows/packaging/CPackWindows.cmake`)。

> 状态: **IN_PROGRESS (脚手架)**。安装规则、并存/Qt-only 两种包形态、
> starter 子集与许可文件均已就位, 并在 Linux 环境冒烟通过 (TGZ 文件
> 清单 + 动态链接核验, 见第九节); **windeployqt / macdeployqt 尚未在
> Windows / macOS 实机跑过**, 实机步骤按第五节执行并回填第十节清单。

## 一、包形态总览

| 形态 | 配置开关 | 内容 | 产物名 |
| --- | --- | --- | --- |
| 并存包 (默认) | `-DMAGTILE_BUILD_QT=ON` | `magtile_app` + `magtile_studio_qt` 两个主程序 + `data/` + `licenses/` + `README.md` | `MagTileStudio-<版本>-win64.*` |
| Qt-only 包 | 上者 + `-DMAGTILE_PACKAGE_QT_ONLY=ON` | 仅 `magtile_studio_qt` + `data/` + `licenses/` + `README.md` | `MagTileStudio-<版本>-win64-qt.*` |
| CLI/GL 包 | 不开 `MAGTILE_BUILD_QT` | 仅 `magtile_app` (现状默认) | `MagTileStudio-<版本>-win64.*` |

两种 Qt 形态的 `data/` 范围都由 `-DMAGTILE_PACKAGE_MODEL_SET`
(full / starter / 自定义清单) 决定, 见第七节。NSIS 开始菜单快捷方式
随形态自动调整: 并存包主快捷方式直达 `magtile_app library --gui`,
Qt 界面另建 "MagTile Studio (Qt)"; Qt-only 包唯一主快捷方式即 Qt 界面。

注意: 并存包与 Qt-only 包共用同一 NSIS 安装目录与 WiX UpgradeCode
语义, **不要**在同一台机器同时安装两种形态; Qt-only 形态当前定位为
分发实验/评审, 正式渠道形态在 V1 发布前敲定。WiX 方式 B
(`Product.wxs` 按固定文件名收割) 不支持 Qt-only 形态。

## 二、前置条件

| 平台 | Qt 要求 | 部署工具 | 说明 |
| --- | --- | --- | --- |
| Windows | ≥ 6.4, 建议 6.5 LTS+ (MSVC 2022 64-bit 套件) | `windeployqt` (随 Qt) | ≥ 6.5 时 CPack 自动部署运行库, 6.4 手动 (第五节) |
| macOS | ≥ 6.4, 建议 6.5+ (`brew install qt` 或官方安装器) | `macdeployqt` (随 Qt) | 出 .app/.dmg 需先切 bundle 模式 (第五节) |
| Linux | ≥ 6.4 (Ubuntu 24.04 apt 即 6.4.2) | 官方部署 API 不支持 | 当前仅 TGZ 冒烟; AppImage 为后续路线 (第十节) |

必装 Qt 模块: Core / Gui / Qml / Quick / QuickControls2 / OpenGL
(Essentials, LGPLv3); 可选 TextToSpeech (步骤朗读, 缺失时静默降级)。
Ubuntu 依赖清单见 `docs/QT_UI_PLAN.md` §3.1。其余前置 (CMake ≥ 3.20、
NSIS、Python3 子集打包) 与 `scripts/package_windows.md` 第一节一致。

## 三、构建

```bat
:: Windows (x64 Native Tools 或普通终端)
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64 ^
    -DMAGTILE_BUILD_QT=ON ^
    -DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64
cmake --build build-win --config Release --parallel
ctest --test-dir build-win -C Release --output-on-failure
```

```bash
# macOS
cmake -S . -B build-mac -DMAGTILE_BUILD_QT=ON \
    -DCMAKE_PREFIX_PATH=$(brew --prefix qt)
cmake --build build-mac --parallel && ctest --test-dir build-mac --output-on-failure

# Linux (打包冒烟)
cmake -S . -B build-pack -DMAGTILE_BUILD_QT=ON
cmake --build build-pack --parallel
```

Qt 侧测试 (`qt_backend_bridges` 后端桥单测 + `qt_gui_smoke` 无头 QML
冒烟) 随 `MAGTILE_BUILD_QT=ON` 自动注册, offscreen 平台无需显示环境;
打包前必须全绿。

## 四、CPack 打包

```bat
cd build-win
cpack -G "NSIS;ZIP" -C Release
```

Linux/macOS 冒烟用 `cpack -G TGZ` (产物非分发物)。QML 界面文件已经
`qt_add_qml_module` 编进可执行体资源, 包内**没有也不需要** qml/ 目录;
`magtile_studio_qt` 启动时从当前目录与可执行文件目录逐级向上探测
`data/`, 安装布局中 `data/` 与主程序并列, 双击即可运行, 无需参数。

Qt 运行库是否已在包内, 取决于构建所用 Qt 版本:

- **Qt ≥ 6.5**: `apps/desktop_qt/CMakeLists.txt` 尾部的官方部署 API
  (`qt_generate_deploy_qml_app_script`) 在 install/cpack 阶段自动把
  Qt 共享库 + 平台插件 + QML 模块收进包 (Windows/macOS; 其余平台
  静默跳过), 打完即自足。
- **Qt 6.4**: 部署 API 尚为技术预览未启用, cpack 产物只含应用本体,
  按第五节手动补运行库后重新压包/重打安装器。

## 五、Qt 运行库部署 (windeployqt / macdeployqt)

> 本节命令尚未在实机验证 (见文首状态), 首跑时逐条核对第十节清单。

### Windows — windeployqt (Qt 6.4 必需; ≥ 6.5 仅核对)

对"解包后的安装目录"运行 (便携 ZIP 先解压, NSIS 则对已安装目录):

```bat
C:\Qt\6.4.x\msvc2022_64\bin\windeployqt.exe ^
    --qmldir apps\desktop_qt\qml ^
    <安装目录>\magtile_studio_qt.exe
```

- `--qmldir` 必须指向仓库的 `apps/desktop_qt/qml` 源码目录 ——
  windeployqt 靠静态扫描 QML import 决定收集哪些 QML 模块, 不给
  该参数会漏掉 QtQuick/Controls 运行时, 目标机上黑屏报错。
- 完成后核对安装目录新增: `Qt6Core/Gui/Qml/Quick/QuickControls2/
  OpenGL(.dll)`、`platforms/qwindows.dll`、`qml/QtQuick/...` 模块树;
  装了 TextToSpeech 还有 `Qt6TextToSpeech.dll` + `texttospeech/` 插件。
- 补完运行库后重新压 ZIP / 重打 NSIS (把部署产物纳入安装规则的
  自动化留待 QT-6 实机阶段收口)。
- 在**未装 Qt 的干净机器**上双击 `magtile_studio_qt.exe` 验收:
  首页可进模型库、教程 3D 视口可旋转、家长门可过。

### macOS — macdeployqt + DMG

当前 CMake 以 `MACOSX_BUNDLE FALSE` 出裸可执行文件 (便于 Linux/CI
冒烟路径统一)。macOS 实机打包时:

1. 把 `apps/desktop_qt/CMakeLists.txt` 中 `set_target_properties`
   的 `MACOSX_BUNDLE` 翻 `TRUE` 重新构建 (安装规则的
   `BUNDLE DESTINATION .` 已就位; Info.plist/图标资产随 QT-6 实机
   阶段补齐), 得到 `magtile_studio_qt.app`。
2. 对安装目录内的 bundle 运行:

   ```bash
   $(brew --prefix qt)/bin/macdeployqt <安装目录>/magtile_studio_qt.app \
       -qmldir=apps/desktop_qt/qml -dmg
   ```

   `-qmldir` 语义同 windeployqt; `-dmg` 直接产出磁盘映像。
3. 发布前签名与公证 (Apple Developer ID):
   `codesign --deep --options runtime` → `xcrun notarytool submit` →
   `xcrun stapler staple`; 未签名/未公证的 DMG 会被 Gatekeeper 拦截。
4. 在未装 Qt 的干净 macOS 上拖装验收 (验收项同 Windows)。

### Linux — 现状与路线

官方部署 API 与 windeployqt 均不覆盖 Linux。当前 Linux TGZ 只含
应用本体, 运行依赖系统 Qt (`sudo apt install qml6-module-qtquick...`,
清单见 `docs/QT_UI_PLAN.md` §3.1); 面向用户的 AppImage
(linuxdeploy + linuxdeploy-plugin-qt) 列入第十节待办。TGZ 的价值是
在任何平台可复验安装规则与文件清单 (第九节)。

## 六、Qt-only 包

```bash
cmake -S . -B build-pack -DMAGTILE_BUILD_QT=ON -DMAGTILE_PACKAGE_QT_ONLY=ON
cmake --build build-pack --parallel
(cd build-pack && cpack)   # Windows: cpack -G "NSIS;ZIP" -C Release
```

- 产物名自动加 `-qt` 后缀 (如 `MagTileStudio-0.1.0-win64-qt.zip`),
  与并存包同目录共存不互覆。
- 包内不含 `magtile_app`; `data/`、`licenses/`、`README.md` 照常。
- `MAGTILE_PACKAGE_QT_ONLY=ON` 而未开 `MAGTILE_BUILD_QT` 时配置期
  即报错 (不会打出空包)。
- 开关只影响**打包内容**, 不影响构建与测试 —— 同一个构建目录改开关
  重新 `cmake` 即可切换形态, 无需重编。

## 七、starter 30 模型子集

与 CLI/GL 包完全同一套机制 (`scripts/package_windows.md` 第二节):

```bash
cmake -S . -B build-pack -DMAGTILE_BUILD_QT=ON \
    -DMAGTILE_PACKAGE_MODEL_SET=starter        # 可与 QT_ONLY 叠加
(cd build-pack && cpack)
```

- 清单 `platforms/windows/packaging/starter_models.txt` = 免费层
  30 模型 (全 core-9), 与模型「免费」标签集合的一致性由
  `tools/verify_free_tier.py` 守卫 (对齐决议 `docs/FREE_TIER_MANIFEST.md`)。
- 打包阶段 `tools/make_data_subset.py` 拷贝清单模型 + 缩略图并
  **同步过滤** `model_catalog.json` (需 Python3) —— 加载器对"目录
  登记但文件缺失"直接报错, 绝不能只删模型不过滤目录。
- Qt 界面的免费层浏览体验 (「🎁 免费模型」筛选、非免费卡片
  「🔒 订阅解锁」角标) 读的是目录 tags: starter 子集包内全部模型
  带「免费」标签, 界面自然全部可搭无锁标, 无需任何专门适配。
- 发布前跑 `python3 tools/verify_free_tier.py` 确认清单未漂移。

## 八、LGPL 合规清单 (Qt 随包分发时逐项核对)

Qt 以 **LGPLv3 动态链接** 使用 (`docs/QT_UI_PLAN.md` §2 既定决策)。
每次分发含 Qt 运行库的包前逐项核对; 任何一项做不到, 停发并走法务
评估 (LGPL 例外条款或 Qt 商业许可, 预算见 `docs/COMMERCIAL_PLAN.md`)。

- [ ] **仅动态链接**: Qt 库全部为共享库 (`.dll`/`.dylib`/`.so`),
      不静态链接 Qt。Linux/macOS 核验: `ldd` (或 `otool -L`)
      `magtile_studio_qt` 中 Qt 全部指向共享库 (第九节已在 Linux
      冒烟此项); Windows 核验包内存在 `Qt6*.dll` 而非被吸进 exe。
- [ ] **仅 LGPL 模块**: 当前链接 Core/Gui/Qml/Quick/QuickControls2/
      OpenGL (+ 可选 TextToSpeech), 全部 Essentials/LGPLv3。新增
      Qt 模块前先核对许可 —— 部分 Add-on (Charts、Data Visualization
      等) 是 GPL-only, 引入即传染整包。
- [ ] **未修改 Qt 源码**: 使用官方二进制发行。若将来自编译打补丁,
      必须随包公开对应源码修改 (LGPLv3 §4)。
- [ ] **随包许可声明**: `licenses/THIRD_PARTY_NOTICES.md` 含 Qt 条目
      (已就位); 正式发布前追加 **LGPLv3 与 GPLv3 许可全文副本**
      (LGPLv3 是 GPLv3 的补充条款, 两份都要带)。
- [ ] **可替换性 (LGPLv3 §4(d))**: 用户可用自己编译的兼容 Qt 替换
      随包 Qt 库 —— 动态链接布局即满足 (库文件在安装目录可见可换);
      安装器/应用不得做"校验 Qt 库指纹、被替换即拒启动"之类的技术
      阻碍。商店渠道 (MSIX / Mac App Store) 的沙箱与签名机制对
      可替换性的影响存在争议, 上架前必须法务评估。
- [ ] **源码获取途径 (LGPLv3 §4(e))**: 为随包 Qt 版本提供完整对应
      源码的获取方式 —— 在 THIRD_PARTY_NOTICES.md 注明所用 Qt 精确
      版本号与官方源码地址 (download.qt.io), 自留一份源码副本以防
      上游撤档 (发布归档时一并落实)。
- [ ] **界面署名**: 关于页/文档注明 "基于 Qt (qt.io), LGPLv3" ——
      非硬性条款但为社区惯例, 家长中心「关于」页落地时带上。
- [ ] **法务终审**: 商用闭源正式发布前, 由法务确认走 LGPL 合规
      或改购 Qt 商业许可 (`scripts/package_windows.md` 第十一节
      发布前清单同款条目)。

## 九、Linux 冒烟验证 (无 Windows/macOS 机器时)

安装规则与文件清单在任何桌面平台可验 (产物 TGZ 仅冒烟, 不分发):

```bash
# 1) 并存包: 两个主程序 + data 全库 + licenses
cmake -S . -B build-pack -DMAGTILE_BUILD_QT=ON
cmake --build build-pack --parallel
(cd build-pack && cpack -G TGZ)
tar tzf build-pack/MagTileStudio-*-Linux.tar.gz | sort   # 核对清单

# 2) Qt-only 包: 无 magtile_app, 包名 -qt 后缀
cmake -S . -B build-pack -DMAGTILE_PACKAGE_QT_ONLY=ON
(cd build-pack && cpack -G TGZ)
tar tzf build-pack/MagTileStudio-*-Linux-qt.tar.gz | grep -c magtile_app  # 应为 0

# 3) starter 子集: data/models 恰 30 个 + 目录同步过滤
cmake -S . -B build-pack -DMAGTILE_PACKAGE_MODEL_SET=starter
(cd build-pack && cpack -G TGZ)
tar tzf build-pack/MagTileStudio-*-Linux-qt.tar.gz | grep -c 'data/models/.*\.json'

# 4) 解包实测: Qt 壳无头冒烟直接吃包内 data/ (系统 Qt 运行)
tar xzf build-pack/MagTileStudio-*-Linux-qt.tar.gz -C /tmp
QT_QPA_PLATFORM=offscreen /tmp/MagTileStudio-*-qt/magtile_studio_qt \
    --data-dir /tmp/MagTileStudio-*-qt/data --db /tmp/qt_pack_smoke.db \
    --smoke-quit-ms 1500

# 5) LGPL 动态链接核验 (第八节第一项)
ldd build-pack/apps/desktop_qt/magtile_studio_qt | grep -i qt   # 应全为 .so
```

本仓库当前状态已按上述流程在 Ubuntu (Qt 6.4.2 / CMake 3.28) 冒烟
通过; Windows/macOS 实机项见下节。

## 十、QT-6 待办清单 (实机阶段)

- [ ] Windows 实机: Qt ≥ 6.5 构建验证自动部署产物完整; Qt 6.4 路径
      跑通 windeployqt 后重打 ZIP/NSIS; 干净机器双击验收。
- [ ] windeployqt 产物纳入安装规则自动化 (或全面转 Qt ≥ 6.5 部署 API),
      消除"打完再手补"的两段式流程。
- [ ] macOS: MACOSX_BUNDLE 切换 + Info.plist/图标资产 + macdeployqt
      -dmg + 签名/公证全链路。
- [ ] Linux AppImage (linuxdeploy + Qt 插件), 面向用户分发。
- [ ] MSIX (Windows 商店) / Mac App Store 渠道评估 (含 LGPL 可替换性
      法务结论, 见第八节)。
- [ ] licenses/ 补 LGPLv3 + GPLv3 许可全文; THIRD_PARTY_NOTICES.md
      注明随包 Qt 精确版本与源码地址。
- [ ] 应用图标/安装器素材 (与 `scripts/package_windows.md` 第十一节
      共用)。
- [ ] 达成 `docs/QT_UI_PLAN.md` §4 退役条件后, 商店渠道只发 Qt 版
      (ImGui 版退役为内部工具)。
