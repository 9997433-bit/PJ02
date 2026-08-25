# MagTile Studio 跨平台技术架构

本文档定义 MagTile Studio 从单一桌面应用 (GLFW + OpenGL) 演进为多平台商业产品的技术架构: 目标平台、共享核心 + 平台外壳模式、各平台渲染策略、UI 框架选型 (含最终推荐)、数据与同步、内容分发、构建/CI 矩阵、目录结构扩展与 Android 专项方案。

关联文档: [ARCHITECTURE.md](ARCHITECTURE.md) (模块划分与数据格式)、[ROADMAP.md](ROADMAP.md) (商业化阶段)、[CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) (内容库规划)。

---

## 1. 目标平台与优先级

| 平台 | 最低版本 | 定位 | 优先级 |
| --- | --- | --- | --- |
| Windows 10 / 11 | Windows 10 1809 (x64) | 首发商业平台, 家庭 PC 主战场 | **P0 — MVP** |
| Android 平板 | API 26 (Android 8.0), 优先 10″+ 平板 | 第二发布平台, 亲子场景核心设备 | **P0 — MVP+1** |
| macOS | macOS 12 (Apple Silicon + Intel) | 开发机 + 小众销售渠道 | P1 |
| Linux | Ubuntu 22.04+ | 开发 / CI 平台, 不做商业发布 | P1 (仅内部) |
| iOS iPad | iPadOS 16+ | 未来阶段, 架构预留 | P2 (预留) |

优先级依据: 目标用户 (家长 + 6~12 岁儿童) 的设备分布集中在 Windows 家用机与 Android 平板; macOS/Linux 由跨平台框架"顺带"覆盖, 不单独投入; iPad 商业价值高但需要 Metal 渲染路径与 App Store 合规投入, 放在 Android 验证商业模式之后。

---

## 2. 总体架构模式: 共享 C++ 核心 + 平台外壳

### 2.1 分层结构

```
┌────────────────────────────────────────────────────────────────┐
│                        平台外壳 (Platform Shells)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ 桌面 Shell    │ │ Android Shell │ │ iOS Shell    │            │
│  │ Qt 6 (Win/   │ │ Gradle + JNI  │ │ (未来)       │            │
│  │ macOS/Linux) │ │ + Qt/GLES     │ │ Metal/Qt     │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         │  窗口/输入/生命周期/文件路径/内购/推送 (平台差异全部在此层) │
├─────────┴────────────────┴────────────────┴────────────────────┤
│                  magtile_core (共享 C++20 核心库)                │
│  core (数据模型/JSON IO) · physics (校验) · tutorial (教程引擎)   │
│  render (IRenderer 接口 + GL 后端绘制逻辑) · progress (SQLite)    │
│  content (清单/下载/校验)  —— 目标: ≥ 80% 代码量在此层复用          │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 核心原则

1. **`magtile_core` 是唯一业务真相**。物理规则、教程状态机、模型数据、进度存档、内容清单解析全部在核心库内, 任何平台外壳都不得复制这些逻辑。现有代码已满足此约束 (core/physics/tutorial 零图形依赖), 直接继承。
2. **核心库形态**: 桌面平台静态链接 (`STATIC`, 现状); Android 编译为 `libmagtile_core.so` (JNI 要求动态库); iOS 静态链接进 app 二进制。同一套 CMake 目标通过工具链文件切换, 不为平台分叉源码。
3. **平台外壳只做五件事**: ① 创建窗口/图形上下文并驱动帧循环; ② 把触摸/鼠标/键盘输入翻译为核心库的抽象输入事件; ③ 提供平台路径 (存档目录、缓存目录) 与生命周期回调 (Android onPause 等); ④ 商店集成 (内购、评分引导); ⑤ 打包与签名。
4. **接口边界用纯 C++ 头文件表达** (现有 `include/magtile/`), Android 侧再包一层薄 JNI。禁止让 JNI/Objective-C++ 类型渗入核心库头文件。
5. **80% 复用率的度量口径**: 以编译进各平台包的源码行数计, 核心库 + 共享 QML/UI 描述 ≥ 80%, 各平台外壳 (JNI 胶水、打包脚本、平台服务适配) ≤ 20%。渲染绘制逻辑 (shader、网格组装、描边/幽灵片效果) 属于共享部分, 只有"上下文创建"属于外壳。

### 2.3 现有代码需要的一项重构

当前 `magtile_render_gl` 把 **GLFW 窗口管理** 与 **GL 绘制逻辑** 耦合在同一目标里。跨平台化的第一步是把二者拆开:

- `render/gl_draw/` — 纯绘制: shader、VBO 组装、`submitTile` 实现, 只假设"当前线程已有一个 GL/GLES 上下文", 不 include GLFW。GL 4.1 与 GLES 3.0 共用此层 (见 §3.3)。
- `render/context_glfw/` — 桌面独立窗口路径 (保留, 供 CLI `--gui` 与开发调试用)。
- 平台外壳 (Qt / Android GLSurfaceView) 各自创建上下文后调用 `gl_draw`。

`IRenderer` 接口 (`initialize / beginFrame / submitTile / endFrame / shouldClose`) 不变, 仅新增一个"外部上下文"构造路径。

---

## 3. 各平台渲染策略与后端矩阵

### 3.1 后端矩阵

| 平台 | 首选后端 | 图形 API / 版本 | 上下文来源 | 备选/演进 | 状态 |
| --- | --- | --- | --- | --- | --- |
| Windows | `GLBackend` | OpenGL 4.1 Core (驱动实际提供 4.6) | Qt (`QOpenGLWindow`/QQuick) 或 GLFW | Vulkan 1.2 (性能需要时) | ✅ 绘制逻辑已存在 |
| macOS | `GLBackend` | OpenGL 4.1 Core (系统上限, 已弃用但可用) | 同上 | Metal (经 Qt RHI 或 MoltenVK) — iPad 路径落地时一并迁移 | ✅ 同上 |
| Linux | `GLBackend` | OpenGL 4.1 Core | 同上 | Vulkan | ✅ 同上 |
| Android | `GLESBackend` | **OpenGL ES 3.0** (API 26+ 设备覆盖率 ≈ 100%) | EGL (GLSurfaceView / Qt Quick) | Vulkan 1.1 (API 26+ 覆盖率约 85%, 不作为基线) | 🔲 待实现 (与 GL 4.1 共享 90% 代码) |
| iOS iPad | `MetalBackend` 或 GLES→Metal 转译 | Metal 2 | CAMetalLayer | 若届时已有 Vulkan 后端则走 MoltenVK | 🔲 未来 |

### 3.2 为什么不现在就上 Vulkan

MagTile 的渲染负载是: 数百个半透明凸多边形 + 描边高亮 + 幽灵片 + 轨道相机 + ImGui/QML HUD, 单帧 draw call < 1000, 任何 2015 年后的 GPU 都远未饱和。Vulkan 带来的是 3~5 倍的样板代码与显著更高的驱动兼容性测试成本 (尤其 Android 碎片化), 换不来用户可感知的收益。决策: **GL 4.1 / GLES 3.0 为基线, Vulkan 仅在出现明确性能瓶颈或 Android GL 驱动质量问题时立项**, `IRenderer` 抽象保证届时替换不触碰业务代码。

### 3.3 GL 4.1 与 GLES 3.0 的统一策略

两者的交集完全覆盖本项目需求 (VAO、实例化、UBO、MSAA、sRGB)。具体做法:

- **Shader 双版本头**: 同一份 GLSL 主体, 构建期拼接 `#version 410 core` 或 `#version 300 es` + 精度限定符前缀。当前仅 3~4 个 shader (平面片、描边、地面网格、拾取), 手工维护双头的成本远低于引入 shader 交叉编译工具链; 若 shader 数量超过 ~15 个再引入 `glslang`/Qt shadertools。
- **API 加载**: 桌面继续用自研加载器 (`gl_api.cpp`); Android 直接链接 `libGLESv3.so`, 无需加载器。差异封装在 `gl_api.hpp` 的一个平台分支里。
- **禁用清单**: 绘制层禁止使用 GLES 3.0 不存在的特性 (几何着色器、`GL_QUADS`、双面独立混合等), CI 里用 GLES 头编译一次绘制层做静态保证。

---

## 4. UI 框架选型

UI 框架决定的是: 教程 HUD、模型浏览/搜索、进度页、设置、商店/内购页 —— 即 3D 视口**之外**的一切。3D 视口本身始终由自研 `IRenderer` 绘制, 不依赖 UI 框架的场景图。

### 4.1 候选方案

| 方案 | 简述 |
| --- | --- |
| **A. Qt 6 (Qt Quick/QML)** | C++ 原生框架, 一套代码覆盖 Win/macOS/Linux/Android/iOS; QML 声明式 UI + C++ 模型层 |
| **B. Flutter + Dart FFI** | Flutter 做全部 UI, 经 FFI 调 C++ 核心; 3D 视口经 `Texture` 外接纹理嵌入 |
| **C. 各平台原生** | Windows (WinUI 3) + Android (Jetpack Compose) + iOS (SwiftUI) 各写一套 UI |

### 4.2 详细对比 (Qt 6 vs Flutter + FFI)

| 维度 | Qt 6.7+ (QML) | Flutter 3.x + FFI | 优势方 |
| --- | --- | --- | --- |
| **与 C++ 核心集成** | 直接链接 `magtile_core`, QML 经 `Q_PROPERTY`/`Q_INVOKABLE` 绑定 C++ 对象, 零序列化开销 | 需手写/生成 C ABI 包装层 (`ffigen`), 回调、字符串、结构体跨边界都要 marshal; 教程引擎这类有状态对象的双向绑定尤其繁琐 | **Qt (决定性)** |
| **3D 视口嵌入** | `QQuickFramebufferObject` / RHI 纹理节点, GL 上下文与 Qt 共享, 成熟且文档充分; 输入事件直达 C++ | 桌面端外接纹理 (`TextureRegistry`) 需按平台写 embedder 插件 (Win: D3D↔GL interop 或 ANGLE), 官方支持以移动端为主, 桌面属于社区探索区; 每帧有一次纹理拷贝/同步成本 | **Qt (决定性)** |
| **Windows 桌面成熟度** | 20+ 年桌面积累, 高 DPI/多显示器/输入法/安装包生态完备 | 可用且在改善, 但桌面仍非 Flutter 主航道; 复杂窗口行为与外设兼容问题需自担 | Qt |
| **Android 成熟度** | 官方支持, Qt for Android 打包/JNI 桥完善; 包体较大 (见下) | 一线支持, Android 是 Flutter 主场, 渲染性能与手势体验极佳 | Flutter |
| **iOS 路径 (未来)** | 官方支持, 同一 QML 代码 + Metal (Qt RHI) | 一线支持 | 平手 |
| **UI 开发效率 / 动效** | QML 声明式 + 热重载 (qmlls/Design Studio), 动效能力足够教程类 UI | Hot reload 极快, Material 组件库丰富, 动效开发体验业界最佳 | Flutter (小幅) |
| **团队技能匹配** | 现团队即 C++ 团队, 只需增学 QML (语法量小) | 需引入 Dart + Flutter 工程体系, 团队维护两种语言两套工具链 | **Qt** |
| **包体积 (Android, arm64)** | 约 +25~35 MB (Qt 库) | 约 +8~12 MB (Flutter engine) | Flutter |
| **许可与成本** | LGPLv3 动态链接免费可商用 (需允许用户重链接, Android 上 Qt 本就以 .so 分发, 天然合规); 商业许可作为可选升级 (Small Business ≈ $500+/开发者/年, 标准商业 ≈ $3,000~4,000/开发者/年, 以 Qt 官网现价为准) | 框架 BSD 免费; 隐性成本在 FFI 层与桌面 embedder 的自研维护 | 名义上 Flutter, 实际综合成本 Qt 更低 (见 4.3) |
| **长期风险** | Qt 公司商业模式稳定, LGPL 路线受社区监督; 风险: 许可条款年年收紧, 需在依赖上保持动态链接纪律 | Google 对桌面端投入存在不确定性; FFI 包装层随核心 API 演进持续付费 | Qt (小幅) |
| **CI/交付** | CMake 原生, 与现有构建体系同构; aqtinstall 在 CI 装 Qt 成熟 | 需并行维护 Gradle/Flutter 工具链 + CMake 双体系 | Qt |

### 4.3 结论: **选 Qt 6 作为 MVP 唯一 UI 框架**

**推荐路径: Qt 6 (Qt Quick/QML) + LGPLv3 动态链接, 覆盖 Windows MVP 与 Android 第二平台; 3D 视口经 `QQuickFramebufferObject` 嵌入自研 GL 渲染。**

决策依据 (按权重排序):

1. **产品重心在 3D 视口, 而非 UI 组件**。本产品 70% 的屏幕面积和 90% 的工程难点是自研 3D 教程视口。Qt 让 C++ 渲染器以共享上下文零拷贝嵌入; Flutter 则要为每个桌面平台自研外接纹理 embedder —— 把最大的工程风险恰好放在 Flutter 最薄弱的环节。
2. **消灭 FFI 层这个纯负债**。教程引擎、物理校验、内容管线的 API 会随 500+ 模型内容库持续演进, Qt 方案下这只是改一个 C++ 头文件; Flutter 方案下每次都要同步改 C 包装 + Dart 绑定 + 双侧测试。
3. **一套代码真覆盖五平台**。Windows MVP 验证后, macOS/Linux 构建"免费"获得, Android/iOS 复用同一 QML; 方案 C (各平台原生) 三套 UI 的人力是小团队不可承受的, 直接排除。
4. **许可成本可控且有退路**: MVP 期走 LGPL 动态链接 (合规要点: Qt 库以 .so/.dll 分发、随包附许可声明、不静态链接 Qt), 商业化验证后如需静态链接/官方支持再购商业许可, 属于"成功了才花钱"的成本结构。
5. Flutter 的两个真实优势 —— Android 包体更小、UI 动效开发更快 —— 对本产品都不构成翻盘点: 包体大头是 3D 资产而非框架 (见 §7), 教程类 UI 的动效复杂度中等。

**触发重评的条件** (写明以防路径依赖): 若 MVP 后产品方向转为"移动优先 + 重营销页/社区 UI", 且桌面降级为次要平台, 则重新评估 Flutter (届时 FFI 面积也已因 API 稳定而缩小)。

---

## 5. 数据与同步: 本地优先

### 5.1 本地存储 (MVP 必做) — ✅ 已实现 (`magtile::progress`, 详见 [PROGRESS.md](PROGRESS.md))

- **引擎**: SQLite 3 (公有领域, 全平台一致, 单文件易备份)。桌面/Android 均用同一封装 `magtile::progress` (核心库模块, amalgamation 内嵌于 `third_party/sqlite3/`, 全平台统一自编译)。
- **存放位置**: Windows `%APPDATA%/MagTile/`, macOS `~/Library/Application Support/MagTile/`, Linux `~/.local/share/magtile/`, Android `Context.getFilesDir()`。路径由平台外壳注入, 核心库不猜路径 (CLI 即桌面外壳, 已按上表注入默认路径, `--db` 可覆盖)。
- **核心表** (schema v1 已建; `content_state` 随内容分发功能落地时加入 v2):

```sql
-- 每个模型的教程进度
CREATE TABLE model_progress (
  model_id      TEXT PRIMARY KEY,   -- 对应 data/models/<id>.json
  current_step  INTEGER NOT NULL DEFAULT 0,
  completed_at  INTEGER,            -- unix 时间戳, NULL = 未完成
  play_seconds  INTEGER NOT NULL DEFAULT 0,
  favorited     INTEGER NOT NULL DEFAULT 0,  -- 0/1 收藏标记
  updated_at    INTEGER NOT NULL    -- 同步冲突判定用
);
CREATE TABLE achievements (         -- 已解锁成就 (未解锁不落库)
  id TEXT PRIMARY KEY, unlocked_at INTEGER NOT NULL
);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
-- 磁力片库存 JSON 存于 settings 表 key = 'tile_inventory'
CREATE TABLE content_state (        -- [规划中] 已下载内容包的版本与校验状态 (见 §6)
  pack_id TEXT PRIMARY KEY, version INTEGER, sha256 TEXT, installed_at INTEGER
);
```

- schema 带 `PRAGMA user_version` 做迁移版本号 (当前 v1), 迁移路径随核心库回归测试 (`progress_roundtrip`); 版本号高于应用支持范围时拒绝写入, 防止旧应用损坏新存档。

### 5.2 云同步 (MVP 后, 可选功能)

- **原则: 离线优先**。无账号/无网络时功能 100% 可用; 账号只解锁"多设备进度同步 + 购买内容跨设备恢复"。
- **协议**: 客户端把 `model_progress` 增量 (按 `updated_at` 水位) POST 到同步服务; 冲突解决按 `model_id` 粒度取 `updated_at` 较新者, 但 `completed_at`/`play_seconds` 取双端最大值 (完成状态与时长只增不减, 天然可合并)。
- **账号与儿童合规**: 账号注册由家长完成 (邮箱/微信/Apple ID), 不采集儿童个人信息; 需满足中国《儿童个人信息网络保护规定》与 Google Play 家庭政策 (见 §9.4)。进度数据不含敏感信息, 传输 TLS, 服务端按用户隔离即可, 不做端侧加密。
- **实现规模**: 一个无状态 HTTP 服务 + 对象存储/托管数据库即可, 不引入实时通道; 客户端侧同步逻辑放核心库 (`magtile::sync`), 网络 IO 由平台外壳注入 (桌面 Qt Network, Android OkHttp 或同用 Qt)。

---

## 6. 内容分发: 内置底包 + CDN 增量

模型内容的物理形态非常有利: 每个模型 = 一个 JSON (几 KB~几十 KB) + 一张缩略图 (~50 KB); 500 模型全量也仅约 30~50 MB, "重"的是未来可能的贴图/音频。

### 6.1 分发结构

```
安装包内置 (APK/AAB/MSI):
  ├── tile_catalog.json            形状目录 (随版本走, 不热更)
  ├── starter_pack/                入门内容包: 50~80 个模型 + 缩略图
  └── 应用本体
CDN (对象存储 + CDN, 国内阿里云 OSS/腾讯 COS, 海外 CloudFront):
  ├── manifest/v<N>.json           内容清单: 包列表、版本号、每文件 sha256、签名
  ├── packs/<pack_id>/<version>/   按主题打包的模型集 (zip, 数 MB 级)
  └── models/<id>/<rev>/           单模型粒度文件 (增量更新单元)
```

### 6.2 更新协议

1. 客户端启动/手动刷新时拉取 `manifest` (带 `If-None-Match`), 用内置公钥验证清单签名 (防 CDN 篡改)。
2. 对比本地 `content_state` 表, 只下载**新增或 sha256 变化**的文件 (模型级增量, 不做二进制 diff —— 文件本来就小, bsdiff 属于过度设计)。
3. 下载到临时目录 → 校验 sha256 → **调用核心库 `PhysicsValidator` 复检** → 原子移入内容目录 → 更新 `content_state`。校验失败的内容直接丢弃并上报, 保证"云端事故不会污染本地内容库"。
4. 全程可断点续传、可离线: 清单拉不到就用本地内容, 无任何功能降级弹窗。

### 6.3 商业化衔接

付费内容包 = 清单中带 `entitlement_id` 的包; 购买凭证 (Play Billing / 桌面端订单) 换取下载授权 (CDN 签名 URL)。已下载内容离线永久可用, 授权校验只发生在下载时。

---

## 7. 构建与 CI 矩阵 (GitHub Actions)

### 7.1 PR 门禁矩阵 (每次提交)

| Job | Runner | 工具链 | 内容 |
| --- | --- | --- | --- |
| `linux-gcc` | ubuntu-24.04 | GCC 13 | 配置(GL OFF) + 构建 + `ctest` (含全部模型 `validate`) |
| `linux-clang-gl` | ubuntu-24.04 | Clang 17 | GL ON + xvfb 冒烟 (`--gui --frames 30 --screenshot`) |
| `windows-msvc` | windows-2022 | MSVC 2022 | GL ON 构建 + `ctest` |
| `macos-arm64` | macos-14 | Apple Clang | GL ON 构建 + `ctest` |
| `android-core` | ubuntu-24.04 | NDK r27 + CMake toolchain | 交叉编译 `magtile_core` + `gl_draw` (arm64-v8a, GLES 头), **不跑测试, 只保证编译通过** —— 这是 §3.3 禁用清单的执行点 |
| `content-lint` | ubuntu-24.04 | — | 全部 `data/models/*.json` 走 validate + 教程一致性 (现有 ctest 已覆盖, 独立列出便于内容团队看结果) |

要点: FetchContent 依赖 + ccache 全部走 `actions/cache`; Qt 引入后用 `jurplel/install-qt-action` (aqtinstall) 固定小版本; 核心库单元测试跑在宿主平台即可 (核心库无平台分支, 交叉编译产物无需上模拟器)。

### 7.2 发布流水线 (tag 触发)

| 产物 | Job | 打包 |
| --- | --- | --- |
| Windows | windows-2022 | `windeployqt` + MSIX 或 Qt Installer Framework, 代码签名 (EV 证书) |
| macOS | macos-14 | `macdeployqt` + notarization + DMG (P1, 随桌面代码免费产出) |
| Linux | ubuntu-24.04 | AppImage (仅内部/极客渠道) |
| Android | ubuntu-24.04 | `androiddeployqt` → AAB, Play 签名, 上传内测轨道 |

---

## 8. 目录结构扩展

### 8.1 目标结构

```
magtile-studio/
├── CMakeLists.txt              # 顶层: 平台分派 + 公共选项
├── shared/
│   ├── core/                   # ← 现 src/{core,physics,tutorial} + include/magtile 迁入
│   │   ├── include/magtile/
│   │   └── src/
│   ├── render/                 # ← 现 src/render 拆分后迁入
│   │   ├── gl_draw/            #    共享绘制逻辑 (GL 4.1 / GLES 3.0)
│   │   └── context_glfw/       #    桌面独立窗口路径 (开发/CLI 用)
│   └── ui/                     # QML 组件 + 资源 (全平台共享)
├── platforms/
│   ├── desktop/                # Qt 桌面 shell (Win/macOS/Linux 同一份代码)
│   │   └── main.cpp, CMakeLists.txt
│   ├── windows/                # Windows 专项: 打包脚本(MSIX)、图标、签名配置
│   ├── android/                # Gradle 工程: Manifest、JNI 桥、资产打包、Play 配置
│   │   ├── app/src/main/cpp/jni_bridge.cpp
│   │   └── app/build.gradle.kts
│   └── ios/                    # 未来预留 (空目录 + README)
├── apps/
│   └── cli/                    # ← 现 src/app (validate/catalog/tutorial CLI, 内容团队工具)
├── data/  assets/  tools/  docs/  tests/  third_party/  cmake/
```

### 8.2 迁移策略: 两步走, 先别名后搬迁

- **第一步 (立即, 零风险)**: 顶层 CMake 保持现有 `src/` 路径不动, 仅按上述结构新增 `platforms/` 与 `shared/ui/`; `magtile_core` 目标名与头文件路径 (`include/magtile/...`) 是稳定接口, 已按目标结构命名, 无需改动任何 `#include`。
- **第二步 (Qt 桌面 shell 落地的同一 PR)**: `git mv src/core src/physics src/tutorial → shared/core/src/`, `src/render → shared/render/`, `src/app → apps/cli/`, 改动仅限 CMake 内路径变量 —— 选在该时机是因为 shell 落地本来就要动 CMake, 合并一次结构性 diff, 避免长期维护"别名 + 实体"双轨。

---

## 9. Android 专项方案

### 9.1 工具链与版本基线

| 项 | 取值 | 依据 |
| --- | --- | --- |
| NDK | r27 LTS | C++20 完整支持 (需 r25+), LTS 维护期长 |
| minSdk | **26** (Android 8.0) | 目标平板存量覆盖 ≈ 98%; API 26 起 GLES 3.0 全覆盖、支持 Java 8 API desugaring 免负担 |
| targetSdk | 跟随 Play 政策 (2026 年为 API 35+, 每年例行升级) | Play 硬性要求: targetSdk 距最新版不得超过 1 年 |
| ABI | `arm64-v8a` (发布) + `x86_64` (仅模拟器调试包) | Play 强制 64 位; armeabi-v7a 平板存量已可忽略, 砍掉省一半 native 体积 |
| 构建 | Gradle 8 + AGP, `externalNativeBuild` 挂现有 CMake | 单一 CMake 真相, Gradle 只做壳 |
| 图形 | GLES 3.0 (EGL), 见 §3 | — |

### 9.2 平板体验要求

- **布局**: 横屏优先 (教程视口 + 右侧步骤面板双栏), QML 按 `sw600dp/sw840dp` 断点切换单/双栏; 支持分屏与自由窗口 (可 resize, 不锁方向), 满足 Google 大屏质量指南 (避免被 Play 平板专区降权)。
- **输入**: 触摸手势 (单指旋转/双指缩放平移) 与手写笔、外接键鼠 (`←/→` 切步骤) 并存 —— 输入抽象层在核心库, 外壳只做事件翻译。
- **生命周期**: `onPause` 即保存进度 + 释放 GL 上下文 (EGL context lost 必须可恢复, 绘制层所有 GPU 资源支持重建); `onTrimMemory` 释放缩略图缓存。

### 9.3 包体预算 (AAB, arm64 下载体积)

| 组成 | 预算 | 说明 |
| --- | --- | --- |
| 应用代码 + magtile_core | ≤ 5 MB | 核心库本身极小 |
| Qt 运行库 (Quick/QML/Network) | ≤ 30 MB | 按需裁模块, `androiddeployqt` 自动裁剪 |
| 入门内容包 (50~80 模型 + 缩略图) | ≤ 15 MB | install-time asset pack |
| **基础下载合计** | **≤ 50 MB** | 红线 60 MB, 超出即启动裁剪评审 |
| 扩展内容 | 不计入 | Play Asset Delivery on-demand pack 或 §6 自有 CDN, 二选一以自有 CDN 为主 (与桌面共用一套分发) |

### 9.4 Google Play 合规清单

- **格式**: 必须 AAB (App Bundle) + Play App Signing; APK 仅内部测试分发。
- **targetSdk 政策**: 每年 8 月 31 日前升到上一年度 API, 排入年度例行工程。
- **家庭政策**: 产品面向儿童 → 必须参加"家庭共享/儿童与家庭"计划: 无行为广告、无未披露数据采集、家长门控 (购买/外链前家长验证)、完成"数据安全"表单与教师认可计划 (可选加分)。账号体系按 §5.2 设计即天然合规 (家长注册、不采集儿童信息)。
- **内购**: 内容包购买必须走 Play Billing (30%/15% 抽成计入定价), 桌面端订单不能在 Android 端直接解锁下载 —— 通过账号同步授权规避重复购买 (Play 政策允许跨平台授权恢复)。
- **其他**: 隐私政策 URL、儿童类目截图规范、GLES 3.0 要求声明 (`<uses-feature android:glEsVersion="0x00030000" android:required="true"/>`)。

### 9.5 JNI 边界设计

JNI 面积刻意压到最小 —— 外壳到核心库只需 6 个入口:

```
nativeInit(assetPath, filesDir)     nativeResize(w, h)
nativeRender()                      nativeTouch(type, x, y, pointerId)
nativeLifecycle(event)              nativeCommand(json)  // 其余一切走 JSON 命令
```

`nativeCommand` 以 JSON 字符串承载低频操作 (加载模型/跳步/查询进度), 复用核心库现成的 JSON IO, 避免为每个功能开一个 JNI 方法。若 Android 外壳最终采用 Qt (§4 推荐路径), 则连这层 JNI 都由 Qt for Android 代管, 本节作为"非 Qt 外壳"的后备方案保留。

---

## 10. 分阶段落地顺序

| 阶段 | 交付物 | 关键工作 |
| --- | --- | --- |
| P0-a | 渲染层拆分 | §2.3 重构: `gl_draw` 与窗口管理分离, GLES 编译门禁进 CI |
| P0-b | Windows MVP | Qt 6 桌面 shell (QML HUD 替代 ImGui 面向用户部分; ImGui 保留为开发者调试面板)、SQLite 进度、MSIX 打包签名 |
| P0-c | 内容分发 | 清单协议 + CDN + 增量下载 + 下载后复检 |
| P1 | Android 平板 | GLES 后端、Qt for Android 打包、Play 合规、内购 |
| P1+ | 云同步 | 账号 + 进度同步服务 |
| P2 | macOS 正式发布 / iPad 立项 | Metal 路径 (Qt RHI), App Store 合规 |

---

## 11. 决策摘要

1. **架构**: 共享 C++20 核心库 (`magtile_core`) + 薄平台外壳, 复用率目标 ≥ 80%; 核心库是唯一业务真相。
2. **UI 框架**: **Qt 6 (QML) + LGPLv3 动态链接**, 一套 UI 覆盖 Windows/macOS/Linux/Android/iOS。决定性理由: 3D 视口零拷贝嵌入 + 无 FFI 维护负债 + 团队 C++ 技能直接复用; Flutter 的包体与动效优势对本产品不构成翻盘点。
3. **渲染**: GL 4.1 (桌面) / GLES 3.0 (Android) 双头共享同一绘制层, `IRenderer` 抽象已就位; Vulkan/Metal 仅作为记录在案的演进选项, 不在 MVP 立项。
4. **数据**: SQLite 本地优先, 云同步为可选增值; 冲突按"进度只增不减"合并。
5. **内容**: 安装包内置入门包 + 签名清单驱动的 CDN 模型级增量更新, 下载内容强制过物理校验器复检。
6. **Android**: NDK r27, minSdk 26, 仅 arm64-v8a, AAB ≤ 50 MB, 家庭政策合规前置设计。
