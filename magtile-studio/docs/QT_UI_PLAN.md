# MagTile Studio · Qt 6 商用界面迁移计划 (ImGui → Qt/QML)

> 本文规划桌面端 (Windows / macOS / Linux) 商用界面从 **GLFW + Dear ImGui** 向 **Qt 6 + QML** 的迁移：为什么迁、迁什么、分几步迁、两套界面如何并存与退役。界面规范以 [UI_UX_SPEC.md](UI_UX_SPEC.md) 为唯一标准，技术栈总纲见 [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md)。
>
> **状态图例**：`DONE` 已实现 ｜ `IN_PROGRESS` 部分实现 ｜ `PLANNED` 已规划未实现

---

## 1. 为什么迁移：ImGui 是脚手架，Qt 是商品房

当前 GL/ImGui 版（`magtile_app library --gui`）证明了核心引擎与 3D 教程闭环可行，但它是**工程验证外壳**，离商用儿童产品有结构性差距：

| 维度 | GLFW + ImGui（现状） | Qt 6 + QML（目标） |
|------|----------------------|--------------------|
| 视觉表现 | 即时模式控件，圆角/阴影/动效全部手写，难以达到 LEGO Builder 级 polish | 声明式 UI + 属性动画 + Scene Graph，200ms ease-out、胶囊按钮、卡片阴影开箱即得 |
| 中文排版 | 需自带字体图集，字号动态缩放成本高 | 系统字体栈 + HarfBuzz 整形，三档字号缩放（§4.7 阅读友好）零成本 |
| 无障碍 | 无 | Qt Accessibility（屏幕阅读器/系统"减少动态效果"） |
| TTS | 需逐平台手写 SAPI/AVSpeech 绑定 | QtTextToSpeech 统一封装系统引擎（符合"不引入第三方语音 SDK"的隐私要求） |
| 输入法/软键盘 | 家长门中文大写键盘全手绘 | 原生 IME + QML 自绘键盘皆可 |
| 商店打包 | 手工 | windeployqt / macdeployqt + MSIX/DMG 成熟链路 |
| 长期维护 | 每个控件都是自家代码 | 商业公司维护的 UI 框架，LTS 版本保障 |

**保留 ImGui 的理由**：GL 渲染器 + ImGui HUD 继续作为**内容制作与调试工具**（模型质检可视化、冒烟测试截图），不再承载面向家庭用户的商用界面。CLI (`magtile_app`) 完全不受影响。

## 2. 技术选型

- **Qt 6.4+**（Ubuntu 24.04 apt 即 6.4.2；Windows/macOS 建议官方安装器 6.5 LTS+）。CMake 集成用 `find_package(Qt6)`——Qt 体量太大，不适合 FetchContent 每次拉源码编译；构建开关 `MAGTILE_BUILD_QT` 默认 OFF，保证无 Qt 环境（CI、Android 交叉编译）完整构建。
- **QML + Qt Quick Controls (Basic 样式)**：全平台像素一致、控件背景可完全自绘（儿童友好大按钮），设计令牌集中在 `Theme.qml` 单例，与 UI_UX_SPEC §1.2 一一对应。
- **C++ 桥接层** (`apps/desktop_qt/src/`)：QML 不直接碰核心库；`StudioBackend`（QObject）与 `LibraryModel`（QAbstractListModel）是唯一桥，链接静态库 `magtile_core`，核心库**零 Qt 依赖**不变。
- **3D 视口**（QT-3 阶段）：优先 `QQuickFramebufferObject` 复用现有 `magtile_render_gl` 的 GL 4.1 渲染器（改动最小）；若目标平台默认走 RHI/非 GL 后端，则以 `QRhi` 重写渲染器为长期方案。
- **许可合规**：Qt 以 **LGPLv3 动态链接**使用（仅 Essentials 模块），商用闭源应用合规；不静态链接 Qt、不修改 Qt 源码；发布包内附 Qt 许可声明。若后续需要静态链接或商店特殊渠道，再评估 Qt 商业授权。

## 3. 已落地 — DONE

```
apps/desktop_qt/
├── CMakeLists.txt          # find_package(Qt6 6.4) + qt_add_qml_module; 未找到 Qt 时报错并给出各平台安装指引
├── src/
│   ├── main.cpp            # 入口: --data-dir/--db 解析, 数据目录向上探测, 存档路径与 CLI 逐字节一致
│   ├── studio_backend.*    # QML 后端桥: 模型库目录 + 进度存档 + BOM/库存对照 (canBuild/缺片/core-9)
│   │                       #   + modelDetail/bomForModel/toggleFavorite + startBuild -> buildRequested 信号
│   ├── library_model.*     # QAbstractListModel: 模型卡片 (名称/难度/片数/步数/主题/进度徽标/收藏
│   │                       #   /core9Only/canBuild/missingTotal)
│   └── library_filter_model.*  # QSortFilterProxyModel: 难度/主题/只用核心9片/我能搭的 四维筛选
└── qml/
    ├── Theme.qml           # 设计令牌单例 (UI_UX_SPEC §1.2: 磁力蓝 #2E7DD1 / 完成绿 #2C9F6B / 琥珀 #E8A13C, 圆角 16/24/20, 200ms ease-out)
    ├── BigButton.qml       # 胶囊大按钮 (高度 >= 64, 字号 22, 按下缩放动效)
    ├── FilterChip.qml      # 筛选胶囊 (高度 48, 选中实心主色, 状态由外部绑定驱动)
    ├── Main.qml            # 主窗口 + StackView 导航 (首页->库->详情->教程) + buildRequested 统一路由 + 底部温和提示
    ├── HomePage.qml        # 首页: 超大主按钮 + "继续上次"卡片 (直达断点模型详情) + 32px 家长区入口 (§5.3)
    ├── LibraryPage.qml     # 模型库: 筛选侧栏 (难度/主题/只用核心9片/我能搭的) + 卡片网格
    │                       #   + ✓/▶ 进度徽标 + "还缺 N 片"琥珀徽标 + 筛选空态 ("换个条件试试")
    ├── DetailPage.qml      # 模型详情 (§5.4): 预览占位 + 难度/片数/步数 + BOM 对照库存缺片提示
    │                       #   + 套装分层标签 + 收藏 + "开始搭建"大按钮 (高 64, 占宽 80%)
    └── TutorialPage.qml    # 教程占位页: QT-3 视口就绪前温和提示, 路由契约与真教程一致
```

已兑现的规范点：主色板与圆角令牌、可点元素 ≥ 48（家长区入口 32px 为规范内唯一例外）、主按钮 ≥ 64 高、状态三重编码（图形+文字+颜色, §4.7 色盲安全）、任意界面 ≤ 2 步回首页、无失败文案（占位功能一律"即将上线"温和提示，缺片用琥珀提示 + 替代建议，不用红色表达"错误"）。

QT-1 补充说明：BOM 与库存对照在 `StudioBackend::reload` 一次性算好（与 GL 版同策略，模型 JSON 仅启动/重载时加载），核心 9 片分层以 `data/tile_catalog.json` 的 `tier` 标注为单一数据源（目录不可用时退回代码内同口径白名单）；「我能搭的」在未登记库存时禁用并温和引导（不显示全空列表）。「开始搭建」统一走 `startBuild -> buildRequested` 信号，Main.qml 据此路由到占位 TutorialPage —— QT-3 视口就绪后只需替换教程页内容，详情页与路由契约不变。

Qt 版与 GL 版**共用同一份进度存档**（默认平台路径与 `magtile_app` 一致，见 docs/PROGRESS.md），家庭用户在两个外壳间切换进度不丢。

### 3.1 构建与运行

```bash
# Ubuntu / Debian 依赖 (Qt >= 6.4)
sudo apt install qt6-base-dev qt6-declarative-dev \
    qml6-module-qtquick qml6-module-qtquick-controls qml6-module-qtquick-layouts \
    qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtqml-workerscript

# 配置 + 构建 (Qt 界面默认 OFF, 需显式开启)
cmake -S . -B build-qt -DMAGTILE_BUILD_QT=ON
cmake --build build-qt --target magtile_studio_qt -j

# 运行 (在仓库内启动会自动向上找到 data/, 也可显式指定)
./build-qt/apps/desktop_qt/magtile_studio_qt
./build-qt/apps/desktop_qt/magtile_studio_qt --data-dir data --db /tmp/test.db
```

- macOS：`brew install qt`，配置时加 `-DCMAKE_PREFIX_PATH=$(brew --prefix qt)`。
- Windows：Qt 官方安装器（MSVC 2022 64-bit + Qt Quick），`-DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64`。
- **不装 Qt 完全不受影响**：`MAGTILE_BUILD_QT` 默认 OFF，`cmake -S . -B build && cmake --build build && ctest` 与从前一致；开了 ON 但没装 Qt，会得到带上述安装命令的明确报错，而不是天书链接错误。

## 4. 迁移路线（按阶段）

| 阶段 | 内容 | 依赖 | 状态 |
|------|------|------|------|
| **QT-0 外壳落地** | CMake 可选子项目、Theme 令牌、Home + Library 占位、链接 magtile_core、进度徽标 | — | `DONE` |
| **QT-1 模型库完整** | 筛选器（难度/主题/只用核心 9 片/我能搭）、分龄卡片密度（§2）、"继续上次"直达教程、模型详情页（BOM 缺片提示, §5.4） | QT-0 | `IN_PROGRESS`（筛选器 + 筛选空态 + 详情页 + 收藏 + "继续上次"直达详情 DONE；分龄卡片密度、筛选无结果时推荐 3 个可搭模型、详情页 3D 预览与预计用时 PLANNED） |
| **QT-2 家长门与设置** | `core::ParentGate` 接 QML（算术题 + 中文大写软键盘复刻 GL 版）、家长中心、设置页（字号三档/减少动效/主题） | QT-0 | `PLANNED` |
| **QT-3 3D 教程播放器** | `QQuickFramebufferObject` 集成 `magtile_render_gl`：步骤导航/高亮/ghost/轨道相机上屏；退出自动存档 | QT-1 | `PLANNED`（核心屏 ★，工作量最大） |
| **QT-4 反馈与庆祝** | 每步星星反馈、完成庆祝页、成就墙 GUI、QtTextToSpeech 朗读（§4.2/4.3） | QT-3 | `PLANNED` |
| **QT-5 Onboarding 与订阅** | 年龄段选择、库存录入（大号 −/+ 步进器）、订阅页（家长门后, §11） | QT-2 | `PLANNED` |
| **QT-6 打包发布** | windeployqt/MSIX、macdeployqt/DMG 公证、Linux AppImage；ImGui 版退役为内部工具 | QT-1~5 | `PLANNED` |

**退役条件**：QT-3 完成且教程播放器通过 UI_UX_SPEC §14 验收清单后，`library --gui` 从用户文档移除、降级为 `--dev-gui`（保留冒烟测试）；QT-6 完成后商店渠道只发 Qt 版。

## 5. 屏幕清单（Qt 版覆盖进度）

| 屏幕（UI_UX_SPEC 章节） | GL/ImGui 版 | Qt 版 | 迁移阶段 |
|------------------------|-------------|-------|----------|
| 首页 / 模型库 §5 | 卡片网格 + 进度徽标 | 网格/徽标/继续上次卡片 `DONE`；筛选器（难度/主题/只用核心 9 片/我能搭的）+ 筛选空态 + 缺片徽标 `DONE`；分龄布局 `PLANNED` | QT-0 / QT-1 |
| 模型详情 §5.4 | 无 | `DONE`（BOM 对照库存缺片琥珀提示/套装分层标签/收藏/开始搭建大按钮）；3D 可旋转预览与预计用时 `PLANNED`（QT-3 后接入） | QT-1 |
| 教程播放器 §6 ★ | 步骤导航/高亮/ghost/相机 已可用 | `PLANNED`（占位页已接 buildRequested 路由并温和提示暂用 GL 版, 视口就绪后原位替换） | QT-3 |
| 完成庆祝页 §6.2 | 无 | `PLANNED` | QT-4 |
| 进度与成就 §7 | CLI 有数据 | 首页入口占位 `DONE`；成就墙 `PLANNED` | QT-4 |
| 设置 §8 | 无 | `PLANNED` | QT-2 |
| 家长门 §9 | 算术题门 + 中文大写软键盘 已可用 | 32px 入口占位 `DONE`；门界面 `PLANNED` | QT-2 |
| Onboarding / 库存录入 §10 | 无 | `PLANNED` | QT-5 |
| 订阅页 §11 | 无 | `PLANNED` | QT-5 |

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| Qt 6.4（apt 版）与 6.5+ 行为差异（QML 资源前缀 `/qt/qml`、`loadFromModule` 缺失） | CMake 显式固定 `RESOURCE_PREFIX /qt/qml`，`main.cpp` 显式 `addImportPath`，用 `engine.load(QUrl)` 而非 6.5 专属 API；CI 以 6.4 为兼容下限 |
| 3D 集成：Qt 6 默认 RHI，可能不走 GL 后端 | 桌面端以 `QSG_RHI_BACKEND=opengl` + `QQuickFramebufferObject` 起步；QRhi 重写列为长期项，接口已由 `render/renderer.hpp` 抽象隔离 |
| LGPL 合规被商店/法务挑战 | 只动态链接 Qt Essentials；发布物附许可清单；必要时切换 Qt 商业订阅（预算见 COMMERCIAL_PLAN.md） |
| 双外壳期间功能漂移 | 共用 `magtile_core` 与同一存档路径；UI_UX_SPEC 是唯一验收标准，两版状态都登记在 §15 汇总表 |
| 儿童侧性能（冷启动 ≤ 2s, §14） | 模型库只读目录元数据（已按此设计）；QML 编译缓存（qmlcachegen 随 qt_add_qml_module 默认启用）；预览图懒加载 |
