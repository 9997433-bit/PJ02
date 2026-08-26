# Qt 商用界面 桌面打包指南 (QT-6)

本文是 `magtile_studio_qt` (Qt 6 + QML 商用界面) 从源码到分发物的
操作手册: 构建、CPack 打包形态 (与 `magtile_app` 并存 / Qt-only)、
Qt 运行库部署 (windeployqt / macdeployqt)、starter 模型子集与
LGPL 合规清单。通用打包基座 (NSIS/ZIP/WiX、版本号管理、CI 流水线)
见 `scripts/package_windows.md`, 两文共用同一套 CPack 配置
(`platforms/windows/packaging/CPackWindows.cmake`)。

> 状态: **IN_PROGRESS (脚手架 + 冒烟脚本)**。安装规则、并存/Qt-only
> 两种包形态、starter 子集与许可文件均已就位; Linux 侧验证已脚本化
> 为一键 `scripts/smoke_qt_linux_pack.sh` 并全绿 (三档 TGZ 清单断言 +
> **NSIS 安装器脚本生成/makensis 编译冒烟** + 解包实测 + LGPL 合规
> 自动核对 `scripts/check_lgpl_compliance.sh`, 见第八/九节);
> Windows 实机冒烟已脚本化为
> `scripts/smoke_qt_windows.ps1` (构建→测试→CPack→windeployqt→清单
> 断言→无头启动一条龙, 含 -DryRun 自检, 已在 pwsh 下自检通过);
> macOS 实机冒烟已脚本化为 `scripts/smoke_qt_macos.sh` (构建→测试→
> CPack→合成 .app→macdeployqt→签名→bundle 断言→自足启动→DMG 挂载
> 断言一条龙, 非 macOS 上跑可移植子集并对 macOS 专属环节显式 SKIP,
> Linux 实跑子集 + --dry-run 双失败注入自检已全绿)。
> **windeployqt / macdeployqt 尚未在 Windows / macOS 实机跑过**:
> Windows 构建机上跑第五节脚本 + 第十一节验收清单, macOS 构建机上跑
> `smoke_qt_macos.sh` + 第十二节验收清单 (人工段已展开为可打印勾选表
> `docs/reports/MACOS_ACCEPTANCE_CHECKLIST.md`), 结果回填第十节。

## 一、包形态总览

| 形态 | 配置开关 | 内容 | 产物名 |
| --- | --- | --- | --- |
| 并存包 (默认) | `-DMAGTILE_BUILD_QT=ON` | `magtile_app` + `magtile_studio_qt` 两个主程序 + `data/` + `licenses/` + `README.md` | `MagTileStudio-<版本>-win64.*` |
| Qt-only 包 | 上者 + `-DMAGTILE_PACKAGE_QT_ONLY=ON` | 仅 `magtile_studio_qt` + `data/` + `licenses/` + `README.md` | `MagTileStudio-<版本>-win64-qt.*` |
| CLI/GL 包 | 不开 `MAGTILE_BUILD_QT` | 仅 `magtile_app` (现状默认) | `MagTileStudio-<版本>-win64.*` |

两种 Qt 形态的 `data/` 范围都由 `-DMAGTILE_PACKAGE_MODEL_SET`
(full / starter / 自定义清单) 决定, 见第七节。NSIS 开始菜单快捷方式
随形态自动调整: 并存包主快捷方式直达 `magtile_app library --dev-gui`
(GL 内部工具), Qt 界面另建 "MagTile Studio (Qt)"; Qt-only 包唯一主
快捷方式即 Qt 界面 (商店渠道形态)。

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

> 本节命令尚未在实机验证 (见文首状态)。Windows 侧不必手敲: 一键脚本
> `scripts/smoke_qt_windows.ps1` 已把本节 + 第三/四节 + 清单断言 +
> 无头启动冒烟串成一条命令 (见第十一节); 首跑后逐条回填第十节清单。

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

> 冒烟不必手敲: 一键脚本 `scripts/smoke_qt_macos.sh` 已把本节 +
> 第三/四节 + bundle 清单断言 + DMG 挂载断言串成一条命令 (见第十二
> 节)。脚本**不改构建系统** —— 从 CPack 产物合成最小 .app (含
> Info.plist 与 bundle 内 data/) 再跑 macdeployqt; 正式发布路径仍是
> 下面的 MACOSX_BUNDLE 切换。

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

   `-qmldir` 语义同 windeployqt (静态扫描 QML import 决定收集哪些
   QML 模块, **忘带即目标机黑屏**); `-dmg` 直接产出磁盘映像。
   完成后核对 bundle 内新增: `Contents/Frameworks/Qt{Core,Gui,Qml,
   Quick,QuickControls2,OpenGL}.framework`、`Contents/PlugIns/
   platforms/libqcocoa.dylib`、`Contents/Resources/qml/QtQuick/...`
   模块树 (与 Windows 侧 DLL 六件套/qwindows/qml 树逐项对应)。
3. **data/ 必须在 bundle 内** (推荐 `Contents/MacOS/data`, 可执行
   文件向上探测第一跳命中): 用户拖装只把 .app 拖进 /Applications,
   放在 DMG 根部与 .app 并列的 data/ 会在拖装时丢失, 首启即闪退。
4. macdeployqt 改写库路径后原签名即失效, **必须重签**: 冒烟用
   ad-hoc (`codesign --force --deep --sign -`, arm64 无有效签名直接
   拒载); 发布前签名与公证 (Apple Developer ID):
   `codesign --deep --options runtime` → `xcrun notarytool submit` →
   `xcrun stapler staple`; 未签名/未公证的 DMG 会被 Gatekeeper 拦截。
5. 在未装 Qt 的干净 macOS 上拖装验收 (第十二节清单)。

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

> **可自动化项已脚本化** (V1 清单 D6):
> `bash scripts/check_lgpl_compliance.sh <包.tar.gz|解包目录>` 对出包
> 产物自动断言下表标 **[自动]** 的项 —— 动态链接非静态链 (DT_NEEDED/
> ldd 全共享库 + 动态符号表零 Qt 定义符号的静态吸入检测)、仅 LGPL
> 模块白名单 (直接链接 ⊆ 本节第二项 9 模块, 传递闭包 ⊆ Essentials
> 白名单, 白名单外任何 Qt 库当场失败)、必备文件清单
> (THIRD_PARTY_NOTICES.md 含 Qt+LGPL 条目 / License.rtf / README.md)。
> 标 **[自动·发布档]** 的"正式发布前追加"项 (LGPLv3+GPLv3 全文、精确
> 版本+源码地址) 缺省报 WARN 不阻塞冒烟 (缺口在第十节待办), 出正式包
> 前必跑 `--release` 档提升为硬性失败。Linux 冒烟已挂接常跑
> (第九节 `smoke_qt_linux_pack.sh` 第 6 步)。其余标 **[人工]** 的项
> 仍按下表出包时逐项打钩。

- [ ] **仅动态链接** [自动]: Qt 库全部为共享库 (`.dll`/`.dylib`/`.so`),
      不静态链接 Qt。Linux/macOS 核验: `ldd` (或 `otool -L`)
      `magtile_studio_qt` 中 Qt 全部指向共享库 (Linux 侧
      `check_lgpl_compliance.sh` 已断言, 另加 DT_NEEDED 与静态吸入
      符号检测, 随第九节冒烟常跑); Windows 核验包内存在 `Qt6*.dll`
      而非被吸进 exe。
- [ ] **仅 LGPL 模块** [自动]: 当前链接 Core/Gui/Qml/Quick/
      QuickControls2/OpenGL (+ 可选 TextToSpeech), 另有
      qt_add_qml_module/Quick 自动随链的 QML 运行时库 QmlModels/
      Network (Linux 实测 DT_NEEDED 共 9 个 libQt6*.so), 全部
      Essentials/LGPLv3 (`check_lgpl_compliance.sh` 白名单断言:
      直接链接限上述 9 模块, 传递闭包另放行 QuickTemplates2/
      QmlWorkerScript/QmlMeta/DBus)。新增 Qt 模块前先核对许可再扩
      脚本白名单 —— 部分 Add-on (Charts、Data Visualization 等) 是
      GPL-only, 引入即传染整包, 白名单外模块脚本当场失败。
- [ ] **未修改 Qt 源码** [人工]: 使用官方二进制发行。若将来自编译
      打补丁, 必须随包公开对应源码修改 (LGPLv3 §4)。
- [ ] **随包许可声明** [自动; 追加项为自动·发布档]:
      `licenses/THIRD_PARTY_NOTICES.md` 含 Qt 条目 (已就位, 脚本断言
      在包内且含 Qt+LGPL 条目; License.rtf/README.md 同批断言);
      正式发布前追加 **LGPLv3 与 GPLv3 许可全文副本** (LGPLv3 是
      GPLv3 的补充条款, 两份都要带; 脚本缺省 WARN, `--release` 失败)。
- [ ] **可替换性 (LGPLv3 §4(d))** [人工]: 用户可用自己编译的兼容 Qt
      替换随包 Qt 库 —— 动态链接布局即满足 (库文件在安装目录可见可换);
      安装器/应用不得做"校验 Qt 库指纹、被替换即拒启动"之类的技术
      阻碍。商店渠道 (MSIX / Mac App Store) 的沙箱与签名机制对
      可替换性的影响存在争议, 上架前必须法务评估。
- [ ] **源码获取途径 (LGPLv3 §4(e))** [自动·发布档]: 为随包 Qt 版本
      提供完整对应源码的获取方式 —— 在 THIRD_PARTY_NOTICES.md 注明
      所用 Qt 精确版本号与官方源码地址 (download.qt.io), 自留一份
      源码副本以防上游撤档 (发布归档时一并落实; 脚本核验版本号与
      地址两要素, 缺省 WARN, `--release` 失败)。
- [ ] **界面署名** [人工]: 关于页/文档注明 "基于 Qt (qt.io), LGPLv3"
      —— 非硬性条款但为社区惯例, 家长中心「关于」页落地时带上。
- [ ] **法务终审** [人工]: 商用闭源正式发布前, 由法务确认走 LGPL
      合规或改购 Qt 商业许可 (`scripts/package_windows.md` 第十一节
      发布前清单同款条目)。

## 九、Linux 冒烟验证 (无 Windows/macOS 机器时)

安装规则与文件清单在任何桌面平台可验 (产物 TGZ 仅冒烟, 不分发)。
**一键脚本** (推荐, 自动跑完下面全部手动步骤并逐项断言):

```bash
bash scripts/smoke_qt_linux_pack.sh          # 构建目录默认 build-pack
```

覆盖: 1) 并存包 TGZ 清单 (双主程序/data/licenses/README/无多余 qml/);
2) **NSIS 冒烟**: `cpack -G NSIS` 走完 CPackWindows.cmake 生成
`project.nsi` 并经 makensis 编译出安装器 (装的是 Linux 二进制, 仅验
安装器脚本能过编译, 不可分发), 另断言并存包快捷方式两条 (主快捷方式
`library --dev-gui` + "MagTile Studio (Qt)") 已进脚本 —— 需
`apt install nsis`, 未装时该档跳过; 3) Qt-only 包 (无 magtile_app,
-qt 后缀); 4) starter 子集 (模型恰 30 个 + 目录同步过滤 + 解包后
目录登记一致性复核); 5) offscreen 启动实测吃包内 data/;
6) LGPL 合规自动核对 (委托 `scripts/check_lgpl_compliance.sh` 对
解包产物断言 动态链接非静态链 + 模块白名单 + 必备文件清单, 第八节
可自动化项; "发布前追加"项 WARN 不阻塞冒烟)。任一断言失败退出码非零。

等价手动步骤 (脚本内部即此流程):

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

# 5) LGPL 合规自动核对 (第八节可自动化项; 也可单独对任一产物跑)
bash scripts/check_lgpl_compliance.sh \
    build-pack/MagTileStudio-*-Linux.tar.gz          # 冒烟档 (WARN 不失败)
# 出正式包前: 追加 --release, "发布前追加"项 (LGPLv3/GPLv3 全文、
# 精确版本+源码地址) 提升为硬性失败
```

本仓库当前状态已按 `smoke_qt_linux_pack.sh` 在 Ubuntu (Qt 6.4.2 /
CMake 3.28 / NSIS 3.10) 全绿: 三档 TGZ 清单断言、NSIS 脚本生成 +
makensis 编译 + 快捷方式断言、starter 解包目录一致性、offscreen
启动、LGPL 合规自动核对 (`check_lgpl_compliance.sh`: 动态链接非
静态链/模块白名单/必备文件清单 9 项 OK + 发布前追加项 3 WARN 属
预期缺口, 第十节待办) 全部通过; `smoke_qt_macos.sh` 的可移植子集
(构建→ctest→CPack TGZ→清单断言→offscreen→ldd) 已在同一 Ubuntu 环境
实跑全绿 (4 过 / 0 失败 / 5 项 macOS 专属 SKIP, 退出码 0 标记
PARTIAL, 见第十/十二节); Windows/macOS 实机项见下节。

## 十、QT-6 待办清单 (实机阶段)

- [ ] Windows 实机: 在构建机上跑 `scripts/smoke_qt_windows.ps1`
      (Qt ≥ 6.5 验证自动部署产物完整 / Qt 6.4 路径自动跑 windeployqt
      并重压 *-deployed.zip, 脚本内清单断言 + 无头启动已自动化);
      再按第十一节人工清单在干净机器双击验收。NSIS 重打 (把部署产物
      纳入安装器) 仍为手动步骤。
- [ ] windeployqt 产物纳入安装规则自动化 (或全面转 Qt ≥ 6.5 部署 API),
      消除"打完再手补"的两段式流程。
- [ ] macOS 实机: 在 macOS 构建机上跑 `scripts/smoke_qt_macos.sh`
      (合成 .app→macdeployqt→ad-hoc 签名→bundle 断言→自足启动→DMG
      挂载断言已自动化, Linux 上仅可移植子集 + SKIP); 再按第十二节
      人工清单在干净机器拖装验收。
  - [x] Linux 可移植子集实跑全绿 (Ubuntu, Qt 6.4.2 / CMake 3.28):
        `bash -n` 语法检查 + `--dry-run` 双失败注入自检通过; 实跑
        构建→ctest 457/457 全过→CPack TGZ→包内清单断言→offscreen
        启动→ldd 动态链接核验 (11 个 libQt6*.so 全为共享库) ——
        4 项通过 / 0 失败 / 5 项 macOS 专属环节逐条 SKIP, 退出码 0,
        按第十二节语义标记 PARTIAL。
  - [ ] macOS 实机零 SKIP 全绿 + 第十二节人工验收 (待 macOS 构建机;
        此两段都过本条才算收口)。人工段用可打印验收单
        `docs/reports/MACOS_ACCEPTANCE_CHECKLIST.md` 逐项签核
        (含签名公证项, 同为 V1 清单 D4 的验收载体)。
- [ ] macOS 正式路径: MACOSX_BUNDLE 切换 + Info.plist/图标资产进
      构建系统 (替代冒烟脚本的合成 bundle) + Developer ID 签名/公证
      全链路 (`--sign-identity` 已预留)。
- [ ] Linux AppImage (linuxdeploy + Qt 插件), 面向用户分发。
- [ ] MSIX (Windows 商店) / Mac App Store 渠道评估 (含 LGPL 可替换性
      法务结论, 见第八节)。商店订阅计费代码侧已就绪 (探测 R11W):
      MSIX 商店包配置时加 `-DMAGTILE_BILLING_WINDOWS_STORE=ON` 即
      编入 WinRT StoreContext 接线 (仅包身份下商店上下文可用; 本地
      开发档保持 OFF 走假计费, 见
      `include/magtile/billing/store_billing_client.hpp`); Partner
      Center 商品配置与沙盒验收步骤见
      [`../docs/WINDOWS_STORE_BILLING_SANDBOX_QA.md`](../docs/WINDOWS_STORE_BILLING_SANDBOX_QA.md)。
- [ ] licenses/ 补 LGPLv3 + GPLv3 许可全文; THIRD_PARTY_NOTICES.md
      注明随包 Qt 精确版本与源码地址。缺口已由
      `scripts/check_lgpl_compliance.sh` 把关: 冒烟档 WARN 提示,
      出正式包 `--release` 档缺则硬性失败 (第八节)。
- [ ] 应用图标/安装器素材 (与 `scripts/package_windows.md` 第十一节
      共用)。
- [ ] 达成 `docs/QT_UI_PLAN.md` §4 退役条件后, 商店渠道只发 Qt 版
      (ImGui 版退役为内部工具)。

## 十一、Windows 实机验收清单

分两段: 自动化冒烟 (脚本代跑, 构建机上) + 人工验收 (干净机器上)。
两段都过才算 QT-6 Windows 档收口; 结果回填第十节第一项。

### 11.1 自动化冒烟 (构建机)

```powershell
# 仓库根目录; PowerShell 5.1 与 pwsh 7 均可
powershell -ExecutionPolicy Bypass -File scripts\smoke_qt_windows.ps1 `
    -QtDir C:\Qt\6.7.2\msvc2022_64            # 并存包 + full
# 变体: -QtOnly (Qt-only 包) / -ModelSet starter (30 模型子集)
# 先看环境报告与执行计划不实跑: 追加 -DryRun
```

脚本流程: 环境检测 (CMake/Qt/windeployqt/NSIS/VS/Python) → 配置构建
→ ctest (自动排除需显示环境的 GL 双 GUI 冒烟) → `cpack -G NSIS;ZIP`
→ 解压 ZIP → Qt 6.4 时对解包目录跑 windeployqt (≥ 6.5 走自动部署仅
核对) → 包内清单断言 (Qt6 DLL 六件套 / `platforms/qwindows.dll` /
`qml/QtQuick` 模块树 / `vcruntime140*.dll` / data 与目录登记一致性 /
licenses) → offscreen 无头启动冒烟 → (6.4) 重压 `*-deployed.zip`。
任一环节失败退出码非零并给出 `FAILED:` 定位行。

### 11.2 人工验收 (干净 Windows 10/11, 未装 Qt/VS 的物理机或虚拟机)

- [ ] **安装**: 双击 NSIS 安装器 → 许可页显示中文 EULA → 默认装入
      `%ProgramFiles%\MagTile Studio\`; 便携档改为解压
      `*-deployed.zip` (Qt 6.4 产物) 或 `*-win64.zip` (≥ 6.5)。
- [ ] **启动**: 开始菜单 "MagTile Studio (Qt)" (Qt-only 包为
      "MagTile Studio") 或双击 `magtile_studio_qt.exe`; 数秒内出
      首页, 无缺 DLL 弹窗、无黑/白屏 (首次启动会先出现年龄段引导
      三卡片, 属预期, 选任一档进首页)。
- [ ] **打开模型库**: 首页「开始搭建」→ 模型卡片网格出现且缩略图
      正常 (starter 档恰 30 张、全部无 🔒 角标); 筛选条可点、
      「🎁 免费模型」筛选生效。
- [ ] **进教程**: 点任意卡片 → 详情页 3D 预览在转 → 「开始搭建」→
      教程页 3D 视口可鼠标拖拽旋转/滚轮缩放, 「下一步」步进有星星
      反馈, 步骤朗读按钮 🔊 不报错 (无 TTS 引擎时静默)。
- [ ] **退出**: 直接关窗 (无确认框, 预期行为) → 再次启动 → 详情页
      显示「继续搭建 第 N 步」(进度存档写在用户目录, 与安装目录
      分离)。
- [ ] **卸载** (NSIS 档): 设置/控制面板卸载 → `%ProgramFiles%\
      MagTile Studio\` 无残留; 用户存档 (进度库) 保留属预期。

### 11.3 常见失败排查

| 症状 | 原因 | 处置 |
| --- | --- | --- |
| 启动弹窗 "找不到 VCRUNTIME140.dll / MSVCP140.dll" | 干净机器无 VC++ 运行库, 且包内 CRT DLL 缺失 | 核对安装目录有 `vcruntime140*.dll` (CPack 经 InstallRequiredSystemLibraries 收入, MSVC /MD 构建必带); 应急可装官方 [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe), 但正式包必须自带 |
| 启动弹窗 "no Qt platform plugin could be initialized" | `platforms\qwindows.dll` 未拷贝 —— windeployqt 没跑、对错误的 exe 跑、或打包时漏掉 platforms/ 子目录 | 对安装目录重跑 windeployqt (第五节); 核对 `platforms\qwindows.dll` 与 exe 同级的 `platforms\` 子目录里 |
| 窗口出现但黑/白屏, 控制台版报 `module "QtQuick" is not installed` | QML 运行时模块未拷贝 —— windeployqt **忘带 `--qmldir`** (静态扫描不到 import) | 带 `--qmldir apps\desktop_qt\qml` 重跑; 核对 `qml\QtQuick\...` 模块树在安装目录; 这是第五节标注的头号事故 |
| 启动弹窗 "找不到 Qt6Core.dll" (或 Qt6Qml/Quick) | Qt 共享库六件套未拷贝 (windeployqt 未跑), 或构建机 PATH 里的 Qt 掩盖了问题、到干净机才暴露 | 重跑 windeployqt; 用 `scripts/smoke_qt_windows.ps1` 的清单断言在构建机上提前拦截 |
| 启动即闪退、无任何弹窗 | 包内 `data/` 缺失或目录登记与模型文件不一致 (加载器对"登记但缺文件"直接报错) | 核对安装目录 `data\model_catalog.json` 与 `data\models\`; 子集包必须由 make_data_subset.py 装配 (第七节), 严禁手删模型 |
| 教程页 3D 视口空白/花屏 | 远程桌面 / 无 GPU 虚拟机的 OpenGL 能力不足 (视口需 OpenGL 场景图, main.cpp 已固定 `QSG_RHI_BACKEND=opengl`) | 换物理机或开虚拟机 3D 加速; 排查时可设 `QSG_INFO=1` 看场景图后端日志 |
| 朗读按钮无声 | 干净机器缺 TTS 引擎, 或包内缺 `Qt6TextToSpeech.dll` + `texttospeech\` 插件 | 预期为静默降级不报错; 要启用则核对上述两件随包且系统装有中文语音包 |
| 安装器被 SmartScreen 拦截 | 未签名 | 内测阶段"更多信息 → 仍要运行"; 发布前按 `scripts/package_windows.md` 第十一节签名 |
| `smoke_qt_windows.ps1` 中文输出乱码 | 控制台代码页非 UTF-8 | `chcp 65001` 后重跑; 脚本文件本身已带 UTF-8 BOM, PowerShell 5.1 可直接解析 |

## 十二、macOS 实机验收清单

分两段: 自动化冒烟 (脚本代跑, 构建机上) + 人工验收 (干净机器上),
与第十一节 Windows 清单同款结构、同一断言口径 (Qt DLL 六件套 <->
Qt 六框架, qwindows.dll <-> libqcocoa.dylib, qml/QtQuick 树 <->
Resources/qml/QtQuick 树)。两段都过才算 QT-6 macOS 档收口;
结果回填第十节 macOS 实机项。

### 12.1 自动化冒烟 (构建机)

```bash
# 仓库根目录; 需 Qt >= 6.4 (brew install qt 或官方安装器) + Xcode CLT
bash scripts/smoke_qt_macos.sh                       # 并存包 + full
# 变体: --qt-only (Qt-only 包) / --model-set starter (30 模型子集)
#       --qt-dir ~/Qt/6.7.2/macos (显式指定 Qt 套件)
#       --sign-identity "Developer ID Application: ..." (真实签名)
# 先看环境报告与执行计划不实跑: 追加 --dry-run (任何平台可跑,
# 含清单断言逻辑自检 + 双失败注入)
```

脚本流程: 环境检测 (CMake/Qt/macdeployqt/python3/hdiutil/codesign)
→ 配置构建 → ctest (排除需显示环境的 GL 双 GUI 冒烟) → `cpack -G
TGZ` → 解包 → 包内清单断言 (双主程序或 Qt-only / data 目录登记一致
性 / licenses / 无多余 qml/) → offscreen 启动 → **合成最小 .app**
(Contents/MacOS + Info.plist + PkgInfo + bundle 内 data/; 不改构建
系统) → `macdeployqt -qmldir=apps/desktop_qt/qml` → 重签 (缺省
ad-hoc, macdeployqt 改写库路径后原签名必失效) → bundle 清单断言
(Qt 六框架 / libqcocoa.dylib / Resources/qml/QtQuick 树 / bundle 内
data / otool 动态链接) → bundle 自足启动 (cd /tmp 无 --data-dir,
模拟拖装后双击) → `hdiutil create` DMG (.app + Applications 软链)
→ 挂载断言。任一环节失败退出码非零并给出 `FAILED:`/`[!!]` 定位行。

**SKIP 语义**: 非 macOS (如 Linux CI) 上脚本照跑可移植子集 (构建→
测试→CPack→清单断言→offscreen→ldd), macdeployqt/签名/bundle/DMG
各环节逐条打印 `[--] SKIP: <原因>` 且**不算失败** (退出码 0), 末尾
标记 `PARTIAL`; macOS 上装了 Qt 但缺 macdeployqt 同理。PARTIAL
只证明打包机制与清单口径自洽, **不等于 macOS 档收口** —— 必须在
macOS 实机跑到零 SKIP 全绿。

### 12.2 DMG 结构与安装布局

```text
MagTileStudio-<版本>-macos[-qt].dmg   (UDZO 压缩映像)
├── magtile_studio_qt.app/            拖进 Applications 即安装
│   └── Contents/
│       ├── Info.plist                CFBundleExecutable/Identifier/版本
│       ├── PkgInfo
│       ├── MacOS/
│       │   ├── magtile_studio_qt     主程序
│       │   └── data/                 磁力片目录 + 模型库 (bundle 内!)
│       ├── Frameworks/               Qt{Core,Gui,Qml,Quick,
│       │                             QuickControls2,OpenGL}.framework
│       ├── PlugIns/
│       │   └── platforms/libqcocoa.dylib   (+ imageformats/ 等)
│       └── Resources/
│           ├── qml/QtQuick/...       QML 运行时模块树 (-qmldir 产物)
│           ├── licenses/             EULA + THIRD_PARTY_NOTICES
│           └── README.md
└── Applications -> /Applications     拖装引导软链
```

- **data/ 必须在 bundle 内** (Contents/MacOS/data): 拖装只带走
  .app, 与 .app 并列放 DMG 根部的数据在拖装后即丢失。
- 界面 QML (MagTile.Studio 模块) 已编进可执行体资源, 与
  Resources/qml/ 下的 **Qt 运行时模块** (QtQuick/Controls 等) 是
  两回事 —— 前者天然随包, 后者靠 macdeployqt `-qmldir` 收集。
- 进度存档不在包内: 写在用户目录 (与 CLI/GL 版共用同一路径, 见
  docs/PROGRESS.md), 重装/升级不丢档。

### 12.3 人工验收 (干净 macOS 12+, 未装 Qt/Xcode 的物理机或虚拟机)

> 本节为速览版; 实机验收请打印逐项展开的
> [`docs/reports/MACOS_ACCEPTANCE_CHECKLIST.md`](../docs/reports/MACOS_ACCEPTANCE_CHECKLIST.md)
> 填写签核 (环境登记 + 安装/启动/教程/家长门/订阅/签名公证/卸载
> 36 项勾选表 + 失败登记与签核栏), 结论按其 §9 回填第十节与
> V1 清单 D4。

- [ ] **挂载**: 双击 DMG → Finder 出现 `magtile_studio_qt.app` +
      `Applications` 软链, 无"映像损坏"报错。
- [ ] **安装**: 拖 .app 到 Applications → 复制完成; 弹出 DMG。
- [ ] **Gatekeeper 放行**: 首次启动 —— 已签名+公证的包直接开;
      内测 ad-hoc 包会被拦 ("无法打开/来自身份不明的开发者"),
      右键 → 打开 → 再点"打开" (或 系统设置 → 隐私与安全性 →
      "仍要打开"); arm64 机器上**完全无签名**的包连右键打开都不行
      (脚本已确保至少 ad-hoc)。
- [ ] **启动**: 数秒内出首页, 无缺库崩溃、无黑/白屏 (首次启动先出
      年龄段引导三卡片属预期, 选任一档进首页)。
- [ ] **打开模型库**: 首页「开始搭建」→ 模型卡片网格出现且缩略图
      正常 (starter 档恰 30 张、全部无 🔒 角标); 筛选条可点、
      「🎁 免费模型」筛选生效。
- [ ] **进教程**: 点任意卡片 → 详情页 3D 预览在转 → 「开始搭建」→
      教程页 3D 视口可拖拽旋转/滚轮缩放 (触控板双指手势同款),
      「下一步」步进有星星反馈, 步骤朗读 🔊 不报错 (系统自带 TTS,
      通常有声)。
- [ ] **退出**: ⌘Q 或关窗 → 再次启动 → 详情页显示「继续搭建 第 N
      步」(进度存档写在用户目录, 与 .app 分离)。
- [ ] **卸载**: .app 拖入废纸篓 → 无残留服务/登录项; 用户存档
      (进度库) 保留属预期。

### 12.4 常见失败排查

| 症状 | 原因 | 处置 |
| --- | --- | --- |
| 打开报 "已损坏, 应移到废纸篓" | 从网络下载带 quarantine 属性 + 无有效签名 (arm64 尤甚) | 正式包必须 Developer ID 签名 + 公证 + stapler; 内测应急 `xattr -dr com.apple.quarantine <app>` 后右键打开 (仅限自己人, 不得教给用户) |
| 打开报 "无法打开, 来自身份不明的开发者" | 未公证 (ad-hoc 或仅签名未公证) | 内测: 右键 → 打开; 发布前走公证全链路 (第五节第 4 步) |
| 启动即崩溃, 崩溃报告见 `Library not loaded: @rpath/QtCore...` | Qt 框架未随包 —— macdeployqt 没跑或对错误的 .app 跑 | 对 bundle 重跑 macdeployqt; 核对 `Contents/Frameworks/Qt*.framework` 齐全 (脚本 bundle 断言在构建机上提前拦截) |
| 启动报 "no Qt platform plugin could be initialized" | `Contents/PlugIns/platforms/libqcocoa.dylib` 未拷贝 | 重跑 macdeployqt; 核对 PlugIns/platforms/ 在 bundle 内 |
| 窗口出现但黑/白屏, 控制台报 `module "QtQuick" is not installed` | macdeployqt **忘带 `-qmldir`** (静态扫描不到 import) | 带 `-qmldir=apps/desktop_qt/qml` 重跑; 核对 `Contents/Resources/qml/QtQuick/...` 在 bundle 内; 与 Windows 侧同为头号事故 |
| 启动即闪退、无窗口 | bundle 内 `Contents/MacOS/data/` 缺失 (数据被放在 DMG 根部, 拖装丢失) 或目录登记与模型文件不一致 | 数据必须打进 bundle (12.2); 子集包必须由 make_data_subset.py 装配 (第七节), 严禁手删模型 |
| macdeployqt 后应用反而起不来 (arm64) | 库路径被改写导致原签名失效, 未重签 | `codesign --force --deep --sign - <app>` (脚本已内置); 发布用真实身份重签 |
| 教程页 3D 视口空白 | 远程桌面/虚拟机 OpenGL 能力不足 (视口需 OpenGL 场景图) | 换物理机或开虚拟机 3D 加速; `QSG_INFO=1` 看场景图后端日志 |
| 朗读按钮无声 | 系统语音包缺中文声音 | 系统设置 → 辅助功能 → 朗读内容 → 添加中文声音; 应用侧静默降级属预期 |
