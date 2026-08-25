# 商店上架素材规格说明 (STORE ASSETS SPEC) — Google Play 与 Microsoft Store

> 状态: **草稿 / 脚手架**。本文是 **Google Play** 与 **Microsoft Store**
> 两大国际渠道上架素材 (截图 / 置顶大图 / 图标 / 视频) 与文案字段限制、
> 年龄分级申报的**逐渠道规格细目**。分工边界:
> [STORE_LISTING.md](STORE_LISTING.md) 管「字」(文案与后台字段, 覆盖
> Play + 国内安卓商店), [../store_assets/README.md](../store_assets/README.md)
> 管「图的产出」(命名、目录、截图内容脚本、入库规则), 本文管「Play 与
> Microsoft Store 的规格数字与申报口径」—— Microsoft Store 渠道的素材
> 规格**首次在本文立档** (STORE_LISTING.md §1 将其列为渠道启动时另立
> 文档项)。两商店后台要求随政策变动, 全部数字提交当周【以后台为准】;
> 与 store_assets/README.md §2 尺寸表如有出入, 以后台实测为准并**同步
> 回填两文**, 不允许两文长期不一致。

---

## 1. 范围与渠道状态

| 渠道 | 状态 | 工程前置 |
| --- | --- | --- |
| Google Play | V1 提交渠道 (COMMERCIAL_PLAN §5.1~5.2) | AAB + Play App Signing + release 签名 ([../platforms/android/README.md](../platforms/android/README.md)); 字段清单见 [STORE_LISTING.md](STORE_LISTING.md) §3 |
| Microsoft Store | 后续渠道 (桌面档), 本文先行立素材规格 | MSIX 商店包 + Partner Center 包身份 ([WINDOWS_STORE_BILLING_SANDBOX_QA.md](WINDOWS_STORE_BILLING_SANDBOX_QA.md) 前置 P1~P3; 打包路线 [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md)) |

- 国内安卓商店 (华为 / 小米 / 应用宝 / OPPO / vivo) 素材规格维护在
  [../store_assets/README.md](../store_assets/README.md) §2, 不在本文重复。
- 本产品在 Microsoft Store 按「**应用 (App)**」类目提交, 非游戏 ——
  游戏专属素材位 (2:3 Poster art / 1:1 Box art / Xbox 三件套) **不适用**,
  不制作 (见第 3.2 节)。
- 素材内容红线全渠道一致: 零价格 / 零促销 / 零品牌 IP
  ([STORE_LISTING.md](STORE_LISTING.md) §5、§9.3、§10), Microsoft Store
  素材同样执行, 不因渠道放松。

## 2. 截图规格 (尺寸与数量)

### 2.1 Google Play

| 设备位 | 尺寸基线 (px) | 格式 | 数量 | 备注 |
| --- | --- | --- | --- | --- |
| 手机 | 1080×1920 (9:16 竖) | PNG (24 位) / JPG, 无透明 | **2~8 张** (下限口径 ≥4, STORE_LISTING §5) | 边长 320~3840, 长边 ≤ 短边 2 倍; 参与商店推荐位需 ≥4 张且分辨率 ≥1080px |
| 7 英寸平板 | 1200×1920 (竖) 或 1920×1200 (横) | 同上 | **≤8 张** (口径 ≥2) | 横屏优先展示 3D 视口 (STORE_LISTING §6) |
| 10 英寸平板 | 2560×1600 或 1920×1200 (横) | 同上 | **≤8 张** (口径 ≥2) | 平板是主力形态, 实机截图 |

### 2.2 Microsoft Store

| 设备位 | 尺寸 (px) | 格式 | 数量 | 备注 |
| --- | --- | --- | --- | --- |
| Desktop | ≥1366×768, 支持 4K (3840×2160) | PNG, 单文件 ≤50MB | **1~10 张** (至少 1 张为提交硬性下限; 口径 ≥4) | 制作基线 **1920×1080 横屏**; Desktop 截图同时展示给 Surface Hub 用户 |
| 其他设备族 (Xbox / Holographic) | — | — | 0 | 不支持的设备族**不上传截图** (官方明确要求) |

- 每张截图可配 **≤200 字符**说明文字 (caption), 从
  [STORE_LISTING.md](STORE_LISTING.md) 描述中取词, 不新造口径。
- 关键视觉与文字放画面**上 2/3** (商店可能在下 1/3 叠加文字层);
  不在截图内另加 logo / 营销标语大字报。
- 多语言各自单独上传: 每个 Store listing 语言页的截图与 caption
  独立维护, 简中为基线, 英文随 V2 国际投放期补齐。

### 2.3 内容脚本 (两渠道共用)

截图内容与顺序复用 [../store_assets/README.md](../store_assets/README.md)
§3 的 8 张脚本 (① 3D 教程视口 ② 模型库网格 ③「我能搭的」筛选
④ 家长中心隐私与数据 ⑤ 分龄界面 ⑥ 成就墙 ⑦ 断点续搭 ⑧ 成品实拍);
Microsoft Store 桌面档为横屏, 按平板横屏构图重排, 场景与卖点顺序不变。
全部为真实界面实机截图, 任何一张不得出现价格 / 倒计时 / 促销元素。

## 3. 置顶大图 / 推广图

### 3.1 Google Play — Feature graphic (置顶大图)

| 项 | 规格 |
| --- | --- |
| 尺寸 | **1024×500** (固定) |
| 格式 | PNG / JPG, 无透明 |
| 数量 | 1 (必填) |
| 内容 | 不放价格与促销元素; 不放玩具品牌 logo / IP 形象; 配置宣传视频后作为视频封面展示 |

### 3.2 Microsoft Store — Store logos 与推广图

| 素材位 | 尺寸 (px) | 是否制作 | 说明 |
| --- | --- | --- | --- |
| 1:1 App tile icon | **300×300** | **制作** (强烈推荐位) | 上传后商店优先用它而非 MSIX 包内图标; 母版导出 |
| 16:9 Super hero art | **1920×1080** 或 3840×2160 | **制作** (推荐位) | 商店推荐位/详情页顶图; **不得含标题文字**; 关键元素居中、避开下 1/3 (可能叠渐变); 有视频时为视频播完后的定帧底图 |
| 2:3 Poster art | 720×1080 / 1440×2160 | 不制作 | 仅游戏适用 |
| 1:1 Box art | 1080×1080 / 2160×2160 | 不制作 | 仅游戏适用 |
| Xbox 三件套 (Branded key art 等) | — | 不制作 | 不上 Xbox 设备族 |
| Holographic 2:1 (2400×1200) | — | 不制作 | 不支持 Holographic |

全部 PNG, 单文件 ≤50MB。Super hero art 官方内容规范: 不用 UI 截图、
不用设备图、不用通用素材图库、避免政治/宗教符号 —— 用 3D 模型渲染
主视觉 (与 Play 置顶大图同视觉源, 各自按比例重构图, 不做拉伸复用)。

## 4. 应用图标要求

制作规则不变: **1024×1024 母版唯一源头, 向下导出**
([../store_assets/README.md](../store_assets/README.md) §2), 无圆角、
无投影、无透明边缘 (圆角由商店/系统裁切)。

| 渠道 | 尺寸 (px) | 格式 | 说明 |
| --- | --- | --- | --- |
| Google Play (后台上传) | **512×512, ≤1MB** | PNG (32 位) | 商店自动裁圆角; 与应用内自适应图标同视觉源 |
| Microsoft Store (后台上传) | **300×300** (1:1 App tile icon) | PNG | 见第 3.2 节, 优先级高于包内图标 |
| Microsoft Store (MSIX 包内资产) | Square 44×44 / 71×71 / 150×150 / 310×310, Wide 310×150, StoreLogo 50×50 (各含 100%~400% scale 档) | PNG | 属 MSIX 工程资源, 出包时由 Windows App Certification Kit 校验齐套; 与母版同视觉源, 落地随 [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) 第十节 MSIX 待办 |

## 5. 宣传视频 (可选)

两渠道均为**可选项**, V1 不阻塞提交, V2 投放期补
(STORE_LISTING §3 第 9 行口径)。分镜脚本入库
`store_assets/video/`, 成片不入库 (README §4 入库规则)。

| 项 | Google Play | Microsoft Store |
| --- | --- | --- |
| 提交形式 | **YouTube URL** (单条) | **mp4 / mov 直传**, 最多 15 条 (做 1 条即可) |
| 分辨率 | 16:9 横屏, 1080p 基线 | **必须 1920×1080** (硬性) |
| 时长 | 15~30s (store_assets 基线; 商店建议 30s~2min 内) | **≤60s 建议**, 文件 ≤2GB |
| 视频要求 | 公开或不公开 (unlisted) 均可; **关闭广告变现**、无年龄限制、允许嵌入 | MP4: H.264 (AVC1) + AAC-LC 48KHz; MOV: 1080p ProRes |
| 配套素材 | 封面用置顶大图 (第 3.1 节) | **缩略图 PNG 1920×1080 必配** + 标题 ≤255 字符; 视频置顶展示需同时上传 Super hero art (第 3.2 节) |
| 内容红线 | 无价格/促销/品牌 IP; 真实界面录屏 + 实拍 | 同左; 另: **视频内不放年龄分级标志** (商店内展示的官方口径) |

## 6. 文案字段字符限制

文案值一律从 [STORE_LISTING.md](STORE_LISTING.md) §2 裁剪/翻译,
不另立口径; 本节只锁**长度限制**:

### 6.1 Google Play

| 字段 | 限制 | 值来源 |
| --- | --- | --- |
| 应用名称 | **≤30 字符** | STORE_LISTING §2 |
| 简短描述 | **≤80 字符** | STORE_LISTING §2.1 |
| 完整描述 | **≤4000 字符** | STORE_LISTING §2.2 |

### 6.2 Microsoft Store (Partner Center, MSIX 档)

| 字段 | 限制 | 必填 | 值来源 / 说明 |
| --- | --- | --- | --- |
| Product name | 随名称预留 (Name reservation) | 必填 | 「MagTile Studio」, 与 MSIX 清单一致 |
| Description (完整描述) | **≤10000 字符**, 纯文本 (禁 HTML/URL) | **必填** | STORE_LISTING §2.2 扩写; 订阅披露段落必须保留 (§9.2 口径) |
| Short description (简短描述) | **≤1000 字符, 建议 ≤270** (部分版位只显示前 270) | 推荐 | STORE_LISTING §2.1 扩写; 不与 Description 首段重复 |
| Product features (功能列表) | **≤20 条 × ≤200 字符** | 推荐 | 从 §2.2 卖点段逐条拆; 不自带项目符号 |
| What's new in this version | **≤1500 字符** | 更新时填 | 首版留空 |
| Short title | **≤50 字符** | 可选 | 「磁力片工坊」 |
| Sort title / Voice title | 各 **≤255 字符** | 可选 | 不上 Xbox, 暂不填 |
| 截图 caption | **≤200 字符/张** | 可选 | 第 2.2 节 |

> 提交最低完成线 = Description + ≥1 张截图; 但按第 2/3 节推荐位
> 齐套提交, 缺 Store logos 会明显降低详情页质量。

## 7. 年龄分级内容申报

两渠道分级问卷同源 (**IARC** 体系; Play 在 Play Console 内答,
Microsoft 在 Partner Center 内答), 申报答案必须一致 —— 同一产品
两渠道答案不一致会触发复审。内容申报矩阵 (如实申报, 全渠道通用):

| 申报项 | 申报值 | 依据 |
| --- | --- | --- |
| 暴力 / 恐惧内容 / 性内容 / 受控物质 / 赌博 | **无** | 教育类搭建教程, 无任何此类内容 |
| 用户间交流 / UGC / 位置共享 / 个人信息共享 | **无** | 零收集 + 无社交 ([PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md)); Scale 阶段若加 UGC 必须重答问卷 |
| 应用内购买 | **有** (须如实勾选) | 订阅 + 买断包 (STORE_LISTING §9), 家长门后 |
| 预期评级 | Everyone / PEGI 3 / USK 0 或各体系最低档 | 与 STORE_LISTING §7.1 口径一致 |

渠道差异项:

- **Google Play**: 另有目标受众年龄组申报 (勾 5 岁及以下 + 6-8 +
  9-12) 与 Designed for Families 加入, 全套口径见
  [STORE_LISTING.md](STORE_LISTING.md) §7.1、§3 第 13/20 行, 本文不重复。
- **Microsoft Store**: IARC 问卷在提交流程 Age ratings 步骤内完成,
  证书随提交生成; 面向儿童的内容申报须与商店政策儿童条款对齐 ——
  零收集 + 家长门架构天然满足, 如实申报即可【以后台为准】。
  视频素材内不放分级标志 (第 5 节)。

## 8. 命名与落位 (store_assets 目录扩展)

Microsoft Store 素材沿用 [../store_assets/README.md](../store_assets/README.md)
§1 命名规则 (`<渠道>_<用途>_<宽>x<高>.png`, 全小写下划线), 渠道前缀
`msstore`, 截图设备目录 `desktop`:

```
store_assets/
├── icons/msstore_tile_300x300.png
├── feature/msstore_superhero_1920x1080.png
├── screenshots/desktop/zh-CN/01_tutorial3d_1920x1080.png
└── video/msstore_trailer_thumb_1920x1080.png   (缩略图; 成片不入库)
```

素材状态登记继续用 store_assets/README.md §4 登记表, Microsoft Store
条目随桌面渠道启动时追加, 脚手架阶段不建空目录不提交假图。

## 9. 关联文档

| 问题 | 文档 |
| --- | --- |
| 商店字段与文案 (单一事实来源) | [STORE_LISTING.md](STORE_LISTING.md) |
| 素材产出流程 / 命名 / 截图脚本 / 国内商店尺寸 | [../store_assets/README.md](../store_assets/README.md) |
| 价格与商品结构 | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2~§3 |
| 隐私口径 (截图 04 文案来源) | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) |
| Android 工程 (Play 实机截图来源) | [../platforms/android/README.md](../platforms/android/README.md) |
| MSIX 打包与桌面渠道待办 | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) |
| Microsoft Store 计费验收 (Partner Center 前置) | [WINDOWS_STORE_BILLING_SANDBOX_QA.md](WINDOWS_STORE_BILLING_SANDBOX_QA.md) |
| 章节完整性守卫 (STORE_LISTING / store_assets) | `tools/validate_store_listing.py` |
| V1 上架就绪对账单 | [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) |
