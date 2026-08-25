# 免费层三端清单对齐 (Free Tier Manifest)

本文档是免费层 (免费 30) 在三端分发链路上的**清单对齐凭据**: 记录一次真实发生的清单漂移、以 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) 为准的裁决过程, 以及此后防止再度漂移的自动守卫。选品原则与日常换血流程见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §2.5.1, 本文不重复。

## 1. 免费层的三条分发链路

| 链路 | 载体 | 免费层如何生效 | 子集支持 |
| --- | --- | --- | --- |
| 桌面 / 移动运行时 | 模型 JSON `tags` 数组中的 `免费` 标签 | 运行时按标签解锁 (只锁内容不锁功能, COMMERCIAL_PLAN §2.1) | 天然支持 —— 标签即事实来源 |
| Windows 安装包 (starter 档) | `platforms/windows/packaging/starter_models.txt` | CPack `-DMAGTILE_PACKAGE_MODEL_SET=starter` 经 `tools/make_data_subset.py` 裁剪 data/ 随包分发 | 支持 (见 `scripts/package_windows.md` 第三节) |
| Android APK | `platforms/android/app/build.gradle.kts` 的 `stageMagTileAssets` 任务 | **总是全量打包** 整个 data/ (目录 + 全部模型 + 缩略图) 进 APK assets, 免费层同样靠运行时标签生效 | **暂不支持** starter 子集 (见第 5 节) |

**权威口径**: [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.1 —— 免费层 = 当前 30 个带 `免费` 标签的模型 (选品状态**已落地**), 全部只用核心 9 片型 (core-9 占比 100%, 红线 ≥80%), D2 全部 4 个 + D3 26 个, 系列只给第一个。**模型 `tags` 是事实来源, starter 清单是它的打包投影** —— 两者必须集合相等。

## 2. 对齐前的差异清单 (2026-08 审计记录)

对齐前 `starter_models.txt` (Windows 打包任务产出) 与 `免费` 标签集合 (核心片筛选任务产出) 各 30 个, 但**只有 10 个重合**:

### 2.1 两边都有 (10 个, 无争议)

`beach_hut_01` `city_bus_stop_01` `forklift_01` `robot_arm_01` (D2 全部 4 个) + `castle_foundation_01` `crane_tower_01` `dinosaur_stego_01` `farm_barn_01` `igloo_01` `pyramid_giza_01` (D3)。

### 2.2 仅在旧 starter 清单 (20 个, 已移出)

| 模型 | 难度 | 扩展片型 | 与 COMMERCIAL_PLAN §2.1 的冲突 |
| --- | --- | --- | --- |
| `ball_run_tower_01` 螺旋滚珠塔 | D4 | hexagon | 难度超界 + 扩展片 |
| `butterfly_01` 花园大蝴蝶 | D3 | hexagon | 扩展片 |
| `carousel_01` 旋转木马 | D3 | rhombus, trapezoid | 扩展片 |
| `dragon_boat_01` 龙舟 | D3 | hexagon, rhombus | 扩展片 |
| `eiffel_tower_01` 埃菲尔铁塔 | D4 | — | 难度超界 |
| `excavator_01` 履带挖掘机 | D3 | rhombus | 扩展片 |
| `ferris_wheel_frame_01` 摩天轮 | D3 | hexagon, rhombus | 扩展片 |
| `fire_truck_01` 消防车 | D3 | — | (本身合规, 选品落选) |
| `food_truck_01` 美食餐车 | D3 | rhombus | 扩展片 |
| `great_wall_01` 长城敌楼段 | D3 | hexagon, rhombus, trapezoid | 扩展片 |
| `lighthouse_01` 海岬灯塔 | D4 | hexagon, sector, trapezoid | 难度超界 + 扩展片 |
| `lunar_lander_01` 月面着陆器 | D3 | hexagon | 扩展片 |
| `mars_rover_01` 火星探测车 | D3 | hexagon | 扩展片 |
| `penguin_01` 帝企鹅一家 | D3 | hexagon, rhombus | 扩展片 |
| `robot_01` 机器人卫士 | D3 | — | (本身合规, 选品落选) |
| `sailboat_01` 双体帆船 | D3 | hexagon | 扩展片 |
| `skyscraper_01` 城市摩天大楼 | D5 | — | 难度超界 (全库唯一 D5) |
| `tokyo_tower_01` 东京塔 | D3 | trapezoid | 扩展片 |
| `whale_01` 蓝鲸 | D3 | rhombus | 扩展片 |
| `windmill_01` 风车磨坊 | D3 | hexagon, rhombus, trapezoid | 扩展片 |

旧 starter 清单整体口径: D2×4 + D3×22 + D4×3 + D5×1, 其中 16/30 使用扩展片型, **core-9 占比仅 46.7%** —— 直接踩穿免费层 ≥80% 的质检红线 (CONTENT_STRATEGY §2.5 第 3 条)。

### 2.3 仅带 `免费` 标签 (20 个, 已补入 starter)

`bakery_shop_01` `bridge_wood_01` `cabin_lake_01` `cactus_desert_01` `campfire_site_01` `canoe_01` `fishing_boat_01` `gas_station_01` `giraffe_01` `greenhouse_01` `kindergarten_01` `oasis_01` `police_car_01` `roller_coaster_hill_01` `sandbox_park_01` `ski_jump_01` `slide_playground_01` `solar_farm_01` `taxi_01` `tractor_01` —— 全部 D3、全部纯 core-9。

## 3. 裁决与统一方式

**裁决: 以 `免费` 标签集合为准, 重写 `starter_models.txt`。** 依据 (均出自 COMMERCIAL_PLAN §2.1):

1. **选品状态已落地** —— §2.1 白纸黑字认定"当前 30 个模型带 `免费` 标签"即免费层选品, 标签集合就是定稿本身;
2. **core-9 红线** —— 免费库 ≥80% 只用核心片型且橱窗模型必须打「需要扩展装」标; 旧 starter 清单 46.7% 严重违反, 标签集合 100% 合规;
3. **难度口径** —— 免费层难度 1~2 为主、少量难度 3; 旧 starter 含 D4×3 + D5×1, 标签集合 D2×4 + D3×26 合规 (现库无 D1, 低难度以 D2~D3 口径执行)。

统一采用**最小 diff**: 只重写 `starter_models.txt` 一个清单文件 (30 行 id), 不动任何模型 JSON —— 反方向对齐需要增删 40 处 `tags` 并重跑目录登记, 且结果违反上述三条判据。

**旧清单中旗舰位的去向**: 旧 starter 的 `ball_run_tower_01` (旗舰球道) / `skyscraper_01` (难度天花板) 等"橱窗模型"并未被否定 —— COMMERCIAL_PLAN §2.1 把 ≤20% 的橱窗名额**刻意留空**, 待付费墙上线后由产品评审补选。届时操作: 给入选模型追加 `免费` 标签 (扩展片模型须已带 `需要扩展装` 标), 同步 `starter_models.txt`, 并把 `tools/verify_free_tier.py` 的"全 core-9"断言放宽为红线口径 (≥80%)。

## 4. 一致性守卫 (防再度漂移)

`tools/verify_free_tier.py` 固化三条断言, 任一失败退出码 1:

1. 带 `免费` 标签的模型**恰好 30 个**;
2. 免费层**全部只用核心 9 片型** (橱窗名额补选前的落地口径, 严于 ≥80% 红线);
3. `starter_models.txt` 与 `免费` 标签**集合相等** (设计如此, 见第 1 节 —— 清单是标签的打包投影), 不一致时逐条列出两侧差异。

```bash
python3 tools/verify_free_tier.py                 # 仓库默认路径
MAGTILE_FREE_TIER_CHECK=1 tests/run_full_qa.sh    # 随 QA 流水线 (可选关卡)
```

该关卡在 `tests/run_full_qa.sh` 中为**可选** (环境变量 `MAGTILE_FREE_TIER_CHECK=1` 开启): 免费层清单只在选品换血时变化, 日常内容合入不受它约束; 发布打包前必须开启。片型红线本身另有常开关卡兜底 (`check_core5_usage.py --strict`)。

加/换免费模型的完整流程见 CONTENT_STRATEGY §2.5.1 —— 其中已含"同步 starter 清单 + 跑本守卫"步骤。

## 5. Android 免费 APK 现状

`stageMagTileAssets` (platforms/android/app/build.gradle.kts) 目前**不支持 starter 子集**: 它无条件把仓库根 data/ 的形状目录、模型库目录、全部模型 JSON 与缩略图同步进 APK assets, 免费层在 Android 上与桌面全量包一样靠运行时 `免费` 标签生效 (只锁内容不锁功能)。**现阶段没有"免费 APK"这一发行物, 也不需要** —— Freemium 单包分发是移动端商店的标准形态。

若未来确需裁剪 APK 体积或出独立免费包, 推荐改造路径 (刻意未随本次对齐落地, Android 工程另有并行在途改动):

1. 给 `stageMagTileAssets` 增加 Gradle 属性开关 (如 `-PmagtileModelSet=starter`), 在同步前调用 `tools/make_data_subset.py --manifest platforms/windows/packaging/starter_models.txt` 产出裁剪目录, 再以该目录为 `from()` 源 —— 与 Windows CPack 的 `-DMAGTILE_PACKAGE_MODEL_SET=starter` 复用**同一份清单与同一个装配脚本**, 不产生第四份清单;
2. 缩略图随清单同裁 (make_data_subset 已处理, 缺图仅警告);
3. 打包后跑 `tools/verify_free_tier.py` 确认清单未漂移。

## 6. 三端「仅免费 / 全部」浏览体验 (产品层, 2026-08)

清单对齐后, 三端产品界面统一落地了免费层的筛选与温和引导 (不改 30 个 `免费` 标签集合, 判定统一走 `core::isFreeTierModel` —— 目录 `tags` 含 `免费`, 定义在 `include/magtile/core/model_catalog.hpp`; Android Kotlin 侧以同一标签直读目录 JSON):

| 端 | 筛选「仅免费」 | 非免费模型的温和引导 |
| --- | --- | --- |
| CLI | `magtile_app library --free-only` (可与 `--core-only` 叠加; 目录/模型对账照常覆盖全库) | — (列表工具, 不设引导) |
| ImGui 版 (`library --gui`) | 筛选行「免费模型」勾选 | 卡片「订阅解锁」角标 (温和紫, 元数据/收藏照常); 点卡片弹订阅引导弹窗: 「请家长来解锁」(经家长门进家长区订阅占位) /「先看免费模型」(一键切免费筛选) /「回模型库」; `--open` 深链是内容制作/CI 入口, 刻意不过引导 |
| Qt 版 | 筛选侧栏「🎁 免费模型」chip (`LibraryFilterModel::freeOnly`) | 卡片「🔒 订阅解锁」徽标; 详情页元数据/BOM 照常可看 + 温和说明条 (免费数实时读 `freeModelCount`), 「开始搭建」改「请家长来解锁」→ `openSubscriptionZone` 经家长门导向订阅页 (QT-5, §11) |
| Android | 筛选栏「只看免费模型」勾选 (Kotlin 读解包后的 `model_catalog.json` 标签; JNI 载荷刻意不动 —— 库存/进度链路另有并行在途改动; 目录读取失败时筛选温和禁用) | 详情弹窗将「教程即将上线」替换为温和订阅提示 (简介/物理校验照常可用) |

口径铁律不变: **只锁教程入口, 不锁浏览** (COMMERCIAL_PLAN §2.1 只锁内容不锁功能); 儿童侧只说「请家长来解锁」, 无价格/无倒计时/无催促/不用红色 (UI_UX_SPEC §11/§12.2); 标签数据缺失时一律**宁可放行, 不误锁免费内容**。
