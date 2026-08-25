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
│                           #   + Qt 侧测试注册 (qt_backend_bridges 后端桥单测 / qt_gui_smoke QML 冒烟)
├── src/
│   ├── main.cpp            # 入口: --data-dir/--db 解析, 数据目录向上探测, 存档路径与 CLI 逐字节一致
│   │                       #   + --parent-gate 深链 / --smoke-quit-ms + --smoke-parent-flow
│   │                       #   / --smoke-age-onboarding (QT-5 首启引导) 无头冒烟
│   ├── studio_backend.*    # QML 后端桥: 模型库目录 + 进度存档 + BOM/库存对照 (canBuild/缺片/core-9)
│   │                       #   + modelDetail/bomForModel/toggleFavorite + startBuild -> buildRequested 信号
│   │                       #   + freeModelCount (QT-5: 目录「免费」标签计数, 订阅页对比数据源)
│   ├── library_model.*     # QAbstractListModel: 模型卡片 (名称/难度/片数/步数/主题/进度徽标/收藏
│   │                       #   /core9Only/canBuild/missingTotal)
│   ├── library_filter_model.*  # QSortFilterProxyModel: 难度/主题/只用核心9片/我能搭的 四维筛选
│   │                           #   + recommendBuildable 空态推荐 (canBuild 难度升序挑 3 个)
│   ├── inventory_backend.*     # 库存录入桥: tile_inventory 表读写 (与 CLI / GL 版共库)
│   ├── parent_gate_backend.*   # 家长门桥 (QT-2): core::ParentGate 包装 (题目/验证/3 次错冷却/15 分钟
│   │                           #   内存会话, 与 GL 版同一状态机) + 秒级倒计时通知, 不接触存档
│   ├── settings_backend.*      # 设置桥 (QT-2): 字号三档/减少动效 (progress/ui_settings) + 年龄段
│   │                           #   (progress/age_settings), 与 GL 版 / CLI 共用 SQLite 键名契约
│   │                           #   + 首启年龄段引导判定/落盘 (QT-5: ageOnboardingPending
│   │                           #   / completeAgeOnboarding, ui_settings "onboarding_age_done")
│   ├── tts_backend.*           # 步骤朗读桥 (QT-4, §4.2): QtTextToSpeech 系统引擎封装 (可选依赖,
│   │                           #   缺模块/缺引擎静默降级), 开关经 progress/ui_settings "tts_enabled" 持久化 (设置页开关同键)
│   └── tutorial_viewport.*     # 3D 教程视口 (QT-3): QQuickFramebufferObject + 共用 GlSceneRenderer,
│                               #   教程引擎/轨道相机/进度自动存档全在 C++ 侧, QML 只读状态属性
└── qml/
    ├── Theme.qml           # 设计令牌单例 (UI_UX_SPEC §1.2: 磁力蓝 #2E7DD1 / 完成绿 #2C9F6B / 琥珀 #E8A13C, 圆角 16/24/20, 200ms ease-out)
    │                       #   + fontScale/reduceMotion 无障碍属性 (§4.7 字号三档全应用即时缩放, 减少动效时长归零)
    ├── BigButton.qml       # 胶囊大按钮 (高度 >= 64, 字号 22, 按下缩放动效)
    ├── FilterChip.qml      # 筛选胶囊 (高度 48, 选中实心主色, 状态由外部绑定驱动)
    ├── Main.qml            # 主窗口 + StackView 导航 (首页->库->详情->教程 / 首页->家长门|家长中心->设置|订阅)
    │                       #   + buildRequested 统一路由 + 家长会话守卫 (到期/锁定自动退回首页) + 底部温和提示
    │                       #   + openSubscriptionZone 订阅统一路由 (QT-5: 任意入口先过家长门, 深度保持 1)
    ├── HomePage.qml        # 首页: 超大主按钮 + "继续上次"卡片 (直达断点模型详情) + 32px 家长区入口 (§5.3)
    │                       #   + 儿童侧订阅温和入口 (QT-5, §12.2: 只说"请家长来解锁", 无价格无催促)
    ├── AgeOnboardingPage.qml # 首启年龄段引导 (QT-5, §10.1): 盖在首页上的温和全屏引导, 三档大卡片
    │                       #   (4-6/7-9/10+) 选完即落盘 (age_mode + onboarding_age_done) 只出现一次
    ├── LibraryPage.qml     # 模型库: 筛选侧栏 (难度/主题/只用核心9片/我能搭的) + 卡片网格
    │                       #   + 分龄三档 (4-6 超大卡无筛选/7-9 难度+主题/10+ 全量+紧凑)
    │                       #   + 我能搭的空态推荐 3 个可搭模型 (难度升序, 点击直达详情)
    │                       #   + ✓/▶ 进度徽标 + "还缺 N 片"琥珀徽标 + 筛选空态 ("换个条件试试")
    ├── DetailPage.qml      # 模型详情 (§5.4): 3D 可旋转成品预览 (复用教程视口只读 previewMode)
    │                       #   + 难度/片数/步数 + BOM 对照库存缺片提示
    │                       #   + 套装分层标签 + 收藏 + "开始搭建"大按钮 (高 64, 占宽 80%)
    ├── InventoryPage.qml   # 磁力片库存图形录入 (§10.2): 大号 −/+ 步进器 + 直接输入, 保存与 CLI 共库
    ├── ParentGatePage.qml  # 家长门 (§9, QT-2): 乘法题 + 中文大写数字软键盘 + 答错温和提示
    │                       #   + 3 次错 60 秒冷却 "休息一下" (复刻 GL 版交互, 无任何价格信息)
    ├── ParentAreaPage.qml  # 家长中心 (§9.2, QT-2): 会话剩余倒计时 + 订阅/设置入口 + 隐私说明 + 锁定家长区
    ├── SettingsPage.qml    # 设置 (§8, QT-2): 字号三档 (100/125/150%, 即时生效) + 减少动效 + 年龄段三档
    │                       #   + 订阅入口 (QT-5, 本页已在门后, 原位替换进订阅页)
    ├── SubscriptionPage.qml # 订阅页脚手架 (§11, QT-5): 家长门后温和说明订阅解锁全库 + 「免费 vs 全库」
    │                       #   对比实时读目录 + 「即将上线」占位 CTA + mailto; 无 IAP/倒计时/催促/索取信息
    ├── TutorialPage.qml    # 教程播放器 (§6, QT-3): 3D 视口 + 步骤导航 (上一步/下一步/从头再来)
    │                       #   + 步骤说明与提示卡 + 进度条; 键盘左右键可翻步, 详见 QT-3 补充说明
    │                       #   + 🔊 步骤朗读按钮与 4-6 岁自动朗读 + 完成触发庆祝页 (QT-4)
    ├── CelebrationPage.qml # 完成庆祝页 (§6.2/§4.3, QT-4): 彩带 + 大星星 + 温和文案 + 成就卡
    │                       #   + 「再搭一次」「回模型库」大按钮; 减少动效时降级为静态展示
    ├── ProgressPage.qml    # 进度页「我的作品」(§7, QT-4): 三格温和统计 (已完成/进行中/收藏)
    │                       #   + 成就墙条带 + 进行中 (进度条+继续搭建) / 已完成 (日期+用时+再搭一次)
    │                       #   / 我的收藏列表, 行点击直达详情; 空态温和引导去模型库
    └── AchievementsPage.qml # 成就墙全览 (§7.1, QT-4): 徽章卡片网格, 已点亮 = 完成绿+✓+解锁日期,
                            #   未点亮 = 灰色剪影 + 一句话达成条件 (不显示进度百分比, 防焦虑)
```

已兑现的规范点：主色板与圆角令牌、可点元素 ≥ 48（家长区入口 32px 为规范内唯一例外）、主按钮 ≥ 64 高、状态三重编码（图形+文字+颜色, §4.7 色盲安全）、任意界面 ≤ 2 步回首页、无失败文案（占位功能一律"即将上线"温和提示，缺片用琥珀提示 + 替代建议，不用红色表达"错误"）。

QT-1 补充说明：BOM 与库存对照在 `StudioBackend::reload` 一次性算好（与 GL 版同策略，模型 JSON 仅启动/重载时加载），核心 9 片分层以 `data/tile_catalog.json` 的 `tier` 标注为单一数据源（目录不可用时退回代码内同口径白名单）；「我能搭的」在未登记库存时禁用并温和引导（不显示全空列表）。「开始搭建」统一走 `startBuild -> buildRequested` 信号，Main.qml 据此路由到占位 TutorialPage —— QT-3 视口就绪后只需替换教程页内容，详情页与路由契约不变。分龄三档（§2）读 `appSettings.ageModeId`（家长区改档即时生效）：4–6 收起整个筛选栏只留超大主题入口胶囊（高 64/大字号）+ 每行 2 张超大卡片；7–9 只留难度/主题；10+ 全量筛选 + 每行 4–5 张紧凑卡片；被收起的筛选维度在 `collapseHiddenFilters` 里同步清零（防"看不见的筛选"）。「我能搭的」空态由 `LibraryFilterModel::recommendBuildable` 无视其他筛选按难度升序（同难度片数少者优先）推荐 3 个可搭模型（`qt_backend_bridges` 有单测），GL 版 `submitLibrary` 改收 `core::AgeMode` 同口径收放（含空态推荐），两端读同一年龄段设置键。详情页 3D 可旋转预览**零重复实现**——直接复用 QT-3 的 `TutorialViewport`，新增只读 `previewMode`：加载模型最终态展示成品全貌（无 ghost/步骤高亮/呼吸动画，步骤一致性问题也不阻断成品展示），不设 `dbFile` 且预览模式强制跳过 `ProgressStore`（纯看不写，浏览详情不建档）；轨道相机交互（拖动旋转/滚轮缩放/右键平移/「回到最佳视角」）与教程一致，视口未就绪时温和降级回名称卡片占位。

QT-2 补充说明：家长门/冷却/会话逻辑**零重复实现**——Qt 版与 GL 版链接同一个 `core::ParentGate`（纯逻辑层，单测 `parent_gate` 不变），`ParentGateBackend` 只做属性包装与秒级倒计时通知；会话与冷却只存内存、永不落盘（SECURITY_AND_PRIVACY.md §6.2）。路由为 首页 32px 入口 → 无会话先进家长门（过门后**原位替换**为家长中心，导航深度保持 1）→ 设置/订阅在门后第 2 层；Main.qml 有统一的会话守卫，会话到期或点「锁定家长区」时自动退回首页并温和提示。设置三项（字号三档/减少动效/年龄段）经 `SettingsBackend` 写 `ProgressStore` settings 表：年龄段沿用 `age_settings` 键（CLI `settings set-age` / GL 版启蒙布局读同一键），字号与减少动效的键名契约新增在核心层 `progress/ui_settings`（GL/移动端外壳可直接复用，核心库依旧零 Qt 依赖）；字号与动效经 Theme 单例绑定即时全应用生效。订阅页已由 QT-5 升级为脚手架（见下方 QT-5 补充说明）。测试：后端桥单测 `qt_backend_bridges`（含与 GL/CLI 的共库契约双向验证）+ 无头 QML 冒烟 `qt_gui_smoke`（offscreen 三连跑：首页 / `--parent-gate` 深链 / `--smoke-parent-flow` 自动驾驶走完 门→家长中心→设置→订阅）。

QT-3 补充说明（3D 教程播放器）：3D 绘制**零重复实现**——把原 GLFW/ImGui 渲染器中"画场景"的部分（地面网格 + 半透明彩色薄板 + 高亮描边 + 呼吸动画）抽成无窗口的 `render::GlSceneRenderer`（新静态库 `magtile_render_scene`，不含 GLFW/ImGui/Qt，GL 入口经调用方回调在运行时解析），GLFW 版 `GlRenderer` 与 Qt 版视口链接同一份实现，两个外壳画面口径一致。Qt 侧 `TutorialViewport`（`QQuickFramebufferObject`，多重采样 + 深度缓冲）在渲染线程画进场景图分配的 FBO，GUI 线程持有 `tutorial::TutorialEngine` / `render::OrbitCamera` / `progress::ProgressStore`，经 `synchronize()` 拷贝相机与本帧片集合跨线程；alpha 通道用 `glBlendFuncSeparate` 强制写不透明，避免 FBO 在场景图合成阶段透底发白。交互与 GL 版对齐：左键拖动转圈、滚轮缩放、右键平移、「回到最佳视角」按钮，键盘 ←/→ 翻步；当前步新增片橙色描边呼吸提示、未放置片褪色 ghost 只显轮廓。触屏手势已接（多点触控直入 `TutorialViewport::touchEvent`，QML 零改动）：单指拖动 = 轨道旋转（与左键拖动同口径同灵敏度）、双指捏合 = 缩放（指距比经对数换算成等效滚轮格数，与滚轮共用 `OrbitCamera::kZoomStepFactor`（12%/格）单一常量——指距张大一倍成品视觉恰好放大一倍，跟手不窜）、双指同向滑动 = 平移（中点位移，与右键拖动同口径）；手指数变化（落下/抬起第二指）的当帧只重定基准不产生位移，画面不跳变；视口接管触点后 Qt 不再为其合成鼠标事件，触屏与鼠标两套输入并存互不干扰、桌面操作不变；手势直接改相机并请求重绘、不经动画系统，「减少动态效果」开启时照常可用（手势是输入不是装饰动画，UI_UX_SPEC §4.7）；详情页只读 previewMode 复用同一视口，手势自动同样生效。触屏验证步骤：真机（Windows 触屏本 / Linux 触屏设备）直接跑教程页与详情页预览，逐条过上述手势并确认鼠标三键 + 滚轮不受影响；无真机时的触摸模拟——进程内用 `QTest::QTouchEventSequence` 走真实投递管线（含触点抓取/本地化）驱动视口并断言相机数值（本次交付即以该方式在 xvfb 下全量验证：旋转同口径、指距翻倍距离精确减半且捏回还原、中点平移、1↔2 指切换零跳变、TouchCancel 清态），或 Linux 下以内核 uinput 造虚拟多点触屏（evemu / python3-evdev 注入 ABS_MT 双指轨迹，X11 经 XInput2 送达 Qt）；注意 QtQuick 对触摸移动按帧同步压缩（`compressTouchEvent`），offscreen 无帧平台不投递 TouchUpdate，触摸模拟须在真渲染窗口（如 xcb + xvfb）下进行；`--smoke-open-model` 冒烟与手势无关（手势只改输入层），照常通过。存档与 GL 版/CLI 共库：进教程即建档（模型库立刻显示"进行中"），切步/退出/应用退出均落 `ProgressStore`（含用时累计），再次进入自动回到断点步。因 `QQuickFramebufferObject` 依赖 GL 后端，`main.cpp` 默认把场景图钉在 OpenGL（`QSG_RHI_BACKEND` 环境变量可覆盖）；若未来需要 Metal/D3D 原生后端，按 §2 的既定路线以 `QRhi` 重写场景层。无头冒烟：`--smoke-open-model <id>` 启动直进该模型教程（走与用户一致的 `buildRequested` 路由），配合 `--smoke-screenshot <png>` 抓屏自动退出。详情页 3D 预览已复用本视口（只读 `previewMode`，见 QT-1 补充说明）。已知缺口：大模型 ghost 轮廓因多层薄板叠加视觉上偏实（与 GL 版同口径）。

QT-5 补充说明（订阅页脚手架，家长门后）：文案按 UI_UX_SPEC §11 与 COMMERCIAL_PLAN 口径 —— 页首明示免费额度（反套路即信任），温和说明「订阅解锁全库 + 每周上新；免费层永久免费、只锁内容不锁功能」，全页无倒计时/无催促/无羞辱话术/不索取信息、不用红色。「免费 30 vs 全库」对比数字**实时读模型目录**：`StudioBackend::reload` 统计 tags 含「免费」的条目（与 `tools/check_core5_usage.py` 的 `FREE_TAG` 同一口径）暴露为 `freeModelCount`，全库数即既有 `modelCount` —— 选品或库容变化零代码同步。主 CTA 为「订阅即将上线」占位（点按只弹温和 toast），次级 CTA 为 mailto 联系通道（占位邮箱 `hello@magtile.example`，RFC 2606 保留域，上线前替换）；**不接任何 IAP/支付 SDK**，正式三卡定价（月/年/家庭年）、透明条款与「恢复购买」随 V1 付费闭环替换占位区。入口共三处且全部过同一道门：首页儿童侧温和入口（只说「请家长来解锁」，无价格，§12.2）、家长中心「订阅管理」、设置页「查看订阅说明」—— 统一走 Main.qml `openSubscriptionZone`（无会话先进家长门，过门后原位替换为订阅页；设置页进入用 `stack.replace`），订阅页导航深度恒为 1~2，满足「≤ 2 步回首页」与「订阅页只在家长门后可见」两条铁律；会话到期由既有守卫统一退回首页。

QT-5 补充说明（首启年龄段引导，§10.1/§2）：首次启动（存档从未写过 `age_mode` 键且无 `onboarding_age_done` 完成标记，两者任一存在都视作"选过了"）时在首页之上弹出温和全屏引导：三档大卡片（4-6 🐣 启蒙 / 7-9 🦖 标准 / 10+ 🚀 进阶），文案儿童友好只描述体验，无对错无催促也无跳过焦虑——默认档就在三张卡里，选任何一档都对；选完经 `SettingsBackend::completeAgeOnboarding` 一次落盘 `age_mode` + `onboarding_age_done`（后者为 `progress/ui_settings` 新增键契约，与「`age_mode` 非空」互为双保险——CLI/GL 已设过年龄段的存量存档不再打扰）并淡出露出首页。分龄与 LibraryPage 现有口径**同源**：卡片标识就是 `age_4_6/age_7_9/age_10_12` 那组共库键值，选完模型库分龄布局即刻生效；家长之后随时在设置页改档（§8），引导只出现一次不再回弹。入场整页淡入 + 内容轻微上浮、退场淡出，时长全走 `Theme.animMs`——「减少动态效果」开启时归零降级为静态直出直收（§4.7）；引导期间全屏拦截指针事件（选档前下层首页不可点）；存档不可用时不弹引导（不打扰，默认 7-9 档直接可用，P3 零挫败）。测试：`qt_backend_bridges` 新增第 6 节（全新存档待引导 / 选档落盘且只出现一次 / 选默认 7-9 档同样落盘 / CLI-GL 已设年龄段或只有完成标记都不再弹），`onboarding_age_done` 键往返入 `age_tts` 单测；`qt_gui_smoke` 扩为 6 步——`--smoke-age-onboarding` 自动驾驶首启断言引导出现并走与卡片点击同一条 choose 路径选 4-6 档，同库二次启动断言引导不再出现，随后 sqlite 直读校验 `age_mode`/`onboarding_age_done` 确已落盘。

QT-4 补充说明（完成庆祝 + 步骤朗读骨架）：**完成链路单点收口**——`StudioBackend::completeBuild` 是唯一完成写入口（进度推到最后一步 + `markCompleted`（首次完成时刻只增不减）+ 首次完成成就，与 GL 版 `src/app/main.cpp` 同一口径），随后刷新模型库徽标并发 `buildCompleted` 信号，Main.qml 把教程页**原位替换**为 `CelebrationPage`（返回不会退回已完成的教程；「再搭一次」走既有 `startBuild -> buildRequested` 路由再原位替换回教程页，导航深度不增长；已完成模型重开自动从第 0 步开始）。教程内由视口 `finished` 状态触发（最后一片落位停留 0.9s 再庆祝，期间「上一步/从头再来」可自然取消）。庆祝页彩带/星星弹跳在「减少动态效果」开启时整体降级为静态展示（§4.7），页面上无分数无评价（§4.3 只有正向与中性）。朗读走 `TtsBackend`：QtTextToSpeech 封装系统引擎（不引入第三方语音 SDK），构建时 `Qt6TextToSpeech` 为**可选组件**、运行时无引擎则 `available=false` 静默降级；speak 先停旧朗读、切步/离开教程自动停（无叠音 §4.2）；总开关经 `progress/ui_settings` 的 `tts_enabled` 键持久化（默认开、脏值按开兜底，与字号/减少动效同一契约模式），设置页「步骤朗读」大开关直绑 `tts.enabled`（`enabledChanged` 教程页 🔊/自动朗读即时生效，引擎缺失时温和说明、开关照常可调）；4-6 岁启蒙模式（读共库 `age_mode` 键）进入步骤自动朗读，其余年龄段用教程页眉 🔊 按钮（≥48, 朗读中主色高亮）。无头冒烟：`--smoke-complete-model <id>` 走真实完成信号链直达庆祝页，`qt_gui_smoke` 第 4 步跑通后校验存档 `completed_at` 确已写入，并收集五链路全程输出扫描 QML 运行时错误（ReferenceError/TypeError 一票否决，防 tts 类上下文漏接线再犯）；朗读桥开关持久化/与 ui_settings 共键双向契约/无引擎静默降级入 `qt_backend_bridges` 单测，`tts_enabled` 键往返入 `age_tts` 单测。庆祝页「再搭一个」推荐（§6.2）：`LibraryFilterModel::recommendSimilar(modelId, max)` 桥单点承载业务逻辑（排除刚完成模型自身；只挑 canBuild **且免费层**——庆祝页点卡直接 `startBuild` 开搭、无订阅拦截，订阅内容进推荐会绕过 §11「订阅教程只在解锁后可开」故在桥内拦下；同难度最先、±1 次之、候选不足时放宽难度，同距离取更轻松一档、再按片数少者优先），QML 只消费快照；点卡与「再搭一次」同走 `startBuild -> buildRequested`，Main.qml 检测 `isCelebrationPage` 原位替换本页，导航深度不增长；4-6 岁启蒙模式推荐卡每行 1 张更大（读 `appSettings.ageModeId`）；无推荐时整块隐藏不显示空态文案；排序契约入 `qt_backend_bridges` 单测（同难度优先/排除自身/放宽难度/订阅与缺片排除/无库存为空）。尚未落地：🔊 波形动画。

QT-4 补充说明（进度页 + 成就墙）：首页「我的进度」大按钮与**温和统计卡片**（有作品后儿童侧可见，"已完成 N 个模型 · 点亮 N 枚徽章"，只报喜不催促 §4.3）同路由直达 `ProgressPage`「我的作品」（§5.3 儿童可达，无家长门）：三格统计（已完成/进行中/收藏）+ 成就墙条带 + 进行中（进度条 + 第 x/y 步 + 用时）/ 已完成（完成日期 + 用时 + 片数）/ 我的收藏三个列表，任意行点击直达模型详情（继续搭建/再搭一次都走详情页既有大按钮 → `startBuild` 统一路由，深度恒 ≤ 3 且教程页有回首页捷径）；空态温和引导「去模型库挑一个」（`stack.pop(null)` 后落 首页→模型库）。`AchievementsPage` 成就墙全览：徽章卡片网格，已点亮 = 完成绿卡 + ✓ + 解锁日期，未点亮 = **灰色剪影 + 一句话达成条件**（§7.1 防焦虑：不显示进度百分比）。数据经 `StudioBackend` 新增的 `achievementsList / inProgressList / completedList / favoritesList` 四个只读快照与 `favoriteCount / achievementCount` 属性读进度存档（与 CLI `progress list` 同一份 SQLite，`catalogChanged` 时页面自动刷新；收藏切换即时增量维护）。徽章档位只与搭建行为挂钩（§4.5，按完成模型数 1/3/10/30 分档）：`first_model_completed` 与完成链路写档的成就 id 同名，其余档位按完成数在展示层判定达成（不新增写库触发点，成就触发统一收口留待成就系统完整落地）；存档中额外解锁的成就 id 以通用徽章补列，永不缺席。无头冒烟：`--smoke-open-progress` 启动直开进度页（评审/截图深链），`--smoke-parent-flow` 自动驾驶已扩为 进度页→成就墙→门→家长中心→设置→订阅。

QT-6 补充说明（打包脚手架，Linux 可验部分）：安装规则在 `apps/desktop_qt/CMakeLists.txt` 尾部——可执行体落安装根与 `magtile_app` 并列（`RUNTIME`/未来 macOS bundle 的 `BUNDLE` 目的地均已就位），QML 界面已经 `qt_add_qml_module` 编进可执行体资源、包内无需 qml/ 目录，数据目录靠既有的"从可执行文件目录向上探测"命中包内 `data/`（双击即用零参数）。Qt 运行库部署按版本分流：Qt ≥ 6.5 用官方部署 API（`qt_generate_deploy_qml_app_script`）在 install/cpack 阶段自动收集（Windows/macOS；其余平台静默跳过）；Qt 6.4（apt 版兼容下限）部署 API 不启用，打包后手动 `windeployqt --qmldir apps/desktop_qt/qml` / `macdeployqt -qmldir=... [-dmg]`，完整步骤、macOS bundle 切换与签名公证、AppImage 路线见 `scripts/package_qt_desktop.md` 第五节。包形态由 `platforms/windows/packaging/CPackWindows.cmake` 的 `MAGTILE_PACKAGE_QT_ONLY` 控制：默认与 `magtile_app` 并存一包（NSIS 主快捷方式直达 GL 版模型库、Qt 界面另建 "(Qt)" 快捷方式），ON 时产出 Qt-only 包（省略 `magtile_app`，包名加 `-qt` 后缀，Qt 界面即唯一主快捷方式；未开 `MAGTILE_BUILD_QT` 时配置期即报错不出空包）；starter 30 模型子集（`MAGTILE_PACKAGE_MODEL_SET=starter`，免费层清单同一机制）可与任意形态叠加，子集内全部为「免费」标签模型，Qt 界面的免费层角标/筛选零适配。LGPL 合规收敛为随包 `THIRD_PARTY_NOTICES.md` + 发布前八项核对清单（仅动态链接、仅 LGPL 模块、许可全文、可替换性、源码获取途径等，见手册第八节）。Linux 已冒烟且脚本化（一键 `scripts/smoke_qt_linux_pack.sh`）：并存/Qt-only/starter 三档 TGZ 文件清单逐项断言、`cpack -G NSIS` 生成 project.nsi 经 makensis 编译 + 并存包双快捷方式断言（安装器脚本本身过编译，产物装 Linux 二进制仅冒烟）、starter 解包后目录登记一致性复核、offscreen 冒烟直接吃包内 data/、`ldd` 核验 Qt 全部动态链接、`qt_backend_bridges`/`qt_gui_smoke` 全绿。Windows 实机冒烟已备好一键脚本 `scripts/smoke_qt_windows.ps1`（检测 Qt/CMake/NSIS/VS → 构建 → ctest → CPack → Qt6.4 自动 windeployqt / ≥6.5 核对自动部署 → Qt DLL/qwindows/qml 树/CRT/数据一致性清单断言 → offscreen 启动 → 重压自足 `*-deployed.zip`；`-DryRun` 在任意平台输出环境报告+断言逻辑自检），干净机人工验收六步与常见失败排查表（缺 VC++ 运行库/QML 插件未拷/qwindows 缺失等）见手册第十一节。实机待办（windeployqt/macdeployqt 实机运行/MSIX/DMG 公证/AppImage）登记在手册第十节。

Qt 版与 GL 版**共用同一份进度存档**（默认平台路径与 `magtile_app` 一致，见 docs/PROGRESS.md），家庭用户在两个外壳间切换进度不丢。

### 3.1 构建与运行

```bash
# Ubuntu / Debian 依赖 (Qt >= 6.4)
sudo apt install qt6-base-dev qt6-declarative-dev \
    qml6-module-qtquick qml6-module-qtquick-controls qml6-module-qtquick-layouts \
    qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtqml-workerscript

# 可选: 步骤朗读 (QT-4, §4.2) —— 不装也能完整构建, 朗读静默降级
sudo apt install qt6-speech-dev qt6-speech-speechd-plugin

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
| **QT-1 模型库完整** | 筛选器（难度/主题/只用核心 9 片/我能搭）、分龄卡片密度（§2）、"继续上次"直达教程、模型详情页（BOM 缺片提示, §5.4） | QT-0 | `IN_PROGRESS`（筛选器 + 筛选空态 + 详情页 + 收藏 + "继续上次"直达详情 + 详情页 3D 可旋转预览（复用教程视口只读 previewMode）+ 分龄卡片密度与筛选器收放（§2 三档）+「我能搭的」空态推荐 3 个可搭模型 + 详情页预计用时（纯函数档位估算 `build_time_estimate.hpp`：步数 ×1.5 分钟 + 片数 ×0.1 分钟归整到 5/10/15/20/30/45 分钟档、平票取小档，界面只说「🕒 大约 N 分钟」不假精确，4-6 岁更大字，与缺片状态无关照常显示；单测 `qt_build_time_estimate`）DONE） |
| **QT-2 家长门与设置** | `core::ParentGate` 接 QML（算术题 + 中文大写软键盘复刻 GL 版）、家长中心、设置页（字号三档/减少动效/主题） | QT-0 | `IN_PROGRESS`（家长门 QML + 家长中心 + 设置页字号三档/减少动效/年龄段 + 订阅温和占位页（门后）+ 会话守卫 + 后端桥单测/QML 冒烟 DONE；主题亮暗切换、PIN、家长中心完整功能 PLANNED） |
| **QT-3 3D 教程播放器** | `QQuickFramebufferObject` 集成 `magtile_render_gl`：步骤导航/高亮/ghost/轨道相机上屏；退出自动存档 | QT-1 | `DONE`（核心屏 ★：场景绘制抽成 GL/Qt 共用的 `GlSceneRenderer`，视口/导航/高亮/ghost/轨道相机/自动存档 + `--smoke-open-model` 无头冒烟已落地；详情页 3D 预览已以只读 previewMode 复用本视口（QT-1）；触屏手势 DONE（单指旋转 / 双指捏合缩放 / 双指平移，与鼠标并存同口径，previewMode 同享，减少动效下照常可用）） |
| **QT-4 反馈与庆祝** | 每步星星反馈、完成庆祝页、成就墙 GUI、QtTextToSpeech 朗读（§4.2/4.3） | QT-3 | `IN_PROGRESS`（完成庆祝页（彩带/星星/成就卡/再搭一次/回模型库, 减少动效降级）+ 完成链路 `completeBuild -> buildCompleted`（写存档完成 + 首次完成成就, 与 GL 版同口径）+ QtTextToSpeech 步骤朗读（🔊 按钮 + 4-6 岁自动朗读 + 设置页「步骤朗读」开关, `tts_enabled` 契约收口 progress/ui_settings, 可选依赖静默降级）+ `--smoke-complete-model` 冒烟 DONE；进度页「我的作品」（三格统计 + 进行中/已完成/收藏列表, 行点击直达详情）+ 成就墙（首页温和统计卡片入口 + 徽章墙全览, 未解锁灰色剪影 + 达成条件, 按完成数 1/3/10/30 分档）+ `--smoke-open-progress` 冒烟 DONE；每步星星反馈 + 进度条 10% 里程碑小星 DONE（步骤前进落位成功后视口顶部弹出 1~3 颗小星（颗数 = 本步落位片数, ≤1s OutBack）, 快速连点 restart 合并不堆积、不阻塞交互, 减少动效降级为静态「好棒！」；进度条每 10% 一颗小星共 10 颗, 按会话内最高进度点亮,「上一步/从头再来」不回收, 分龄 4-6 更大 / 10+ 更克制, 无分数无惩罚 §4.3；教程视口不进无头冒烟（offscreen 无 GL）, 手动验证: `magtile_studio_qt --smoke-open-model castle_foundation_01` 连点「下一步」看弹星与小星逐颗点亮, 再开「减少动态效果」复验静态降级）；庆祝页「再搭一个」推荐 DONE（`LibraryFilterModel::recommendSimilar` 桥: 同难度 ±1 优先、canBuild 且免费层、排除刚完成模型, 不足时放宽难度；点卡走既有 `startBuild` 原位替换庆祝页深度不增长；4-6 岁每行 1 张大卡；无推荐整块隐藏 + `qt_backend_bridges` 单测）；🔊 波形动画 PLANNED） |
| **QT-5 Onboarding 与订阅** | 年龄段选择、库存录入（大号 −/+ 步进器）、订阅页（家长门后, §11） | QT-2 | `IN_PROGRESS`（订阅页脚手架 DONE：温和文案 + 免费 30 vs 全库对比读目录 + 「即将上线」CTA/mailto 占位 + 首页儿童侧/家长中心/设置页三入口全过家长门，无 IAP；库存录入已随 QT-1 落地；首启年龄段引导 DONE：首页上温和全屏三档大卡片（4-6/7-9/10+, 与 LibraryPage 分龄同一组 age_mode 键值），选完落盘 `age_mode` + `onboarding_age_done` 只出现一次、家长可在设置改档、减少动效降级静态、`--smoke-age-onboarding` 冒烟 + 桥单测；订阅/IAP 适配层骨架 DONE：`billing::BillingClient` 抽象（queryProducts/purchase/restore/subscriptionActive）+ 桌面开发档 `FakeBillingClient` 假计费闭环（三卡占位定价/购买/恢复购买/「模拟已订阅」开发开关，订阅状态经 settings 表 `subscription_active` 契约键持久化，DetailPage/LibraryPage 免费层锁与庆祝页推荐读同一状态，儿童侧仍零价格信息）+ 正式商店档 `StoreBillingClient` 空实现（Windows 商店/Google Play 接法文档化，无真实 SDK/密钥，界面退「即将上线」占位）+ 单测 `billing`/`qt_billing_bridge`（未订阅锁付费模型/假购买解锁/restore）；真实商店 SDK 接入 PLANNED——依赖 V1 付费闭环） |
| **QT-6 打包发布** | windeployqt/MSIX、macdeployqt/DMG 公证、Linux AppImage；ImGui 版退役为内部工具 | QT-1~5 | `IN_PROGRESS`（打包脚手架 DONE：install 规则（Qt≥6.5 部署 API 自动收运行库 / 6.4 文档化 windeployqt/macdeployqt）+ CPack 并存/Qt-only 两种包形态（`MAGTILE_PACKAGE_QT_ONLY`）+ starter 30 模型子集叠加 + LGPL 合规清单，操作手册 `scripts/package_qt_desktop.md`；冒烟脚本 DONE：Windows 实机一键 `scripts/smoke_qt_windows.ps1`（环境检测→构建→ctest→CPack NSIS/ZIP→Qt6.4 自动跑 windeployqt / ≥6.5 核对自动部署→包内清单断言（Qt DLL 六件套/qwindows/qml 树/CRT/目录登记一致性）→offscreen 启动→重压 *-deployed.zip，-DryRun 环境报告+断言逻辑自检（含 qwindows/目录缺失双失败注入）已在 pwsh 过）+ Linux 一键 `scripts/smoke_qt_linux_pack.sh` 全绿（三档 TGZ 清单断言 + **NSIS 冒烟升级：cpack -G NSIS 生成 project.nsi 经 makensis 编译通过 + 并存包双快捷方式断言** + starter 解包目录一致性 + offscreen 实测 + ldd 动态链接核验）+ 手册新增第十一节 Windows 实机验收清单（装→启→库→教程→退→卸载 + 缺 VC++ 运行库/QML 插件未拷/qwindows 缺失等排查表）；windeployqt 实机运行与干净机验收（跑上述脚本+清单即可）、MSIX、DMG 签名公证、AppImage、许可全文随包 PLANNED） |

**退役条件**：QT-3 完成且教程播放器通过 UI_UX_SPEC §14 验收清单后，`library --gui` 从用户文档移除、降级为 `--dev-gui`（保留冒烟测试）；QT-6 完成后商店渠道只发 Qt 版。

## 5. 屏幕清单（Qt 版覆盖进度）

| 屏幕（UI_UX_SPEC 章节） | GL/ImGui 版 | Qt 版 | 迁移阶段 |
|------------------------|-------------|-------|----------|
| 首页 / 模型库 §5 | 卡片网格 + 进度徽标 + 分龄三档密度/筛选收放 | 网格/徽标/继续上次卡片 `DONE`；筛选器（难度/主题/只用核心 9 片/我能搭的）+ 筛选空态 + 缺片徽标 `DONE`；分龄布局（4–6 超大卡/7–9 标准/10+ 紧凑 + 筛选器收放）+「我能搭的」空态推荐 `DONE` | QT-0 / QT-1 |
| 模型详情 §5.4 | 无 | `DONE`（3D 可旋转成品预览（复用教程视口只读 previewMode, 拖动旋转/滚轮缩放, 不写存档）/BOM 对照库存缺片琥珀提示/套装分层标签/收藏/开始搭建大按钮/预计用时「🕒 大约 N 分钟」温和档位估算（4-6 岁更大字, 缺片时照常显示）） | QT-1 |
| 教程播放器 §6 ★ | 步骤导航/高亮/ghost/相机 已可用 | `DONE`（3D 视口 + 步骤导航/高亮/ghost/轨道相机/退出自动存档, 与 GL 版共用场景渲染层与存档；🔊 步骤朗读 + 4-6 岁自动朗读已接 QT-4 骨架；每步星星反馈 + 进度条 10% 里程碑小星已接 QT-4；触屏手势（单指旋转 / 双指捏合缩放 / 双指平移）`DONE`；🔊 波形动画 `PLANNED`） | QT-3 |
| 完成庆祝页 §6.2 | 无 | `DONE`（彩带 + 星星弹跳 + 温和文案 + 成就卡（片数/步数）+「再搭一次/回模型库」大按钮；教程完成原位替换进入, 减少动效时静态降级；「再搭一个」推荐 2 个相近难度可搭模型: 同难度 ±1 优先/排除刚完成/免费层, 点卡直接开搭, 无推荐整块隐藏） | QT-4 |
| 进度与成就 §7 | CLI 有数据 | `DONE`（进度页「我的作品」: 三格统计 + 成就墙条带 + 进行中/已完成/收藏列表 + 空态引导；成就墙全览: 未解锁灰色剪影 + 达成条件, 不显示百分比；首页大按钮 + 温和统计卡片双入口）；成就触发定义表 `IN_PROGRESS`（展示层按完成数分档判定, 写库触发待统一收口） | QT-4 |
| 设置 §8 | 无 | 字号三档/减少动效/步骤朗读开关/年龄段 `DONE`（家长门后设置页, 即时生效并落 SQLite）；主题/语言/库存复入口 `PLANNED` | QT-2 |
| 家长门 §9 | 算术题门 + 中文大写软键盘 已可用 | 32px 入口 + 门界面（软键盘/冷却）+ 家长中心 + 会话守卫 `DONE`；PIN / 手写键盘 `PLANNED` | QT-2 |
| Onboarding / 库存录入 §10 | 库存录入首启弹窗 + 图形录入 | 库存图形录入 `DONE`；年龄段前置流程 `DONE`（首启温和全屏引导：三档大卡片选完落盘只出现一次, 家长可在设置改档；GL 版年龄段前置 `PLANNED`）；快捷套装预填 `PLANNED` | QT-5 |
| 订阅页 §11 | 无 | 脚手架 `DONE`（家长门后；免费 30 vs 全库对比实时读目录；温和文案 + 承诺清单；「即将上线」CTA + mailto 占位；首页/家长中心/设置页三入口）；正式订阅页（三卡定价/透明条款/恢复购买/IAP）`PLANNED` | QT-5 |

**商用视觉抛光（2026-08）**：Theme 新增 `headerHeight/spacingSmall/viewportBg/overlayLight/textDim` 令牌收口全部页面的页眉高/视口底色/浮层底/未点亮星色（QML 侧硬编码色值清零，只剩 Theme 单例）；模型库目录空态改温和文案 +「再试一次」重试大按钮（`studio.reload` 幂等，statusMessage 小字给家长看诊断，0 模型不再自称"已就绪"）；筛选栏分组加组间留白；首页页脚不再露数据目录工程路径（诊断移入家长中心「隐私与数据」卡）；减少动效补齐两处降级：教程视口呼吸高亮定格最亮描边且不自驱重绘（`TutorialViewport.reduceMotion`），庆祝页彩带在减少动效下不实例化（此前仅隐藏、28 条动画仍在后台跑）。

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| Qt 6.4（apt 版）与 6.5+ 行为差异（QML 资源前缀 `/qt/qml`、`loadFromModule` 缺失） | CMake 显式固定 `RESOURCE_PREFIX /qt/qml`，`main.cpp` 显式 `addImportPath`，用 `engine.load(QUrl)` 而非 6.5 专属 API；CI 以 6.4 为兼容下限 |
| 3D 集成：Qt 6 默认 RHI，可能不走 GL 后端 | 桌面端以 `QSG_RHI_BACKEND=opengl` + `QQuickFramebufferObject` 起步；QRhi 重写列为长期项，接口已由 `render/renderer.hpp` 抽象隔离 |
| LGPL 合规被商店/法务挑战 | 只动态链接 Qt Essentials；发布物附许可清单；必要时切换 Qt 商业订阅（预算见 COMMERCIAL_PLAN.md） |
| 双外壳期间功能漂移 | 共用 `magtile_core` 与同一存档路径；UI_UX_SPEC 是唯一验收标准，两版状态都登记在 §15 汇总表 |
| 儿童侧性能（冷启动 ≤ 2s, §14） | 模型库只读目录元数据（已按此设计）；QML 编译缓存（qmlcachegen 随 qt_add_qml_module 默认启用）；预览图懒加载 |
