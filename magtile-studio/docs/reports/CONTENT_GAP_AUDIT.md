# 内容缺口审计: 234 模型库 vs 主题 × 难度矩阵

- 生成时间: 2026-08-25
- 审计基线: foundation 分支 (内容批 A–E 全部并入, 全库 **234** 个模型, 100% 通过全量 QA)
- 对照标尺: [CONTENT_STRATEGY.md](../CONTENT_STRATEGY.md) 2.2 节「主题 × 难度分布矩阵」(13 主题 × D1–D5, 终态目标 **520** 个)
- 审计口径: 逐模型人工归类 (方法见第 2 节), 难度与片数取自 `data/model_catalog.json` (工具生成, 与模型 JSON 逐项一致)
- 产出: 逐主题 D1–D5 现状/目标对照 (第 3 节)、缺口排序 (第 5 节)、批 F–I 共 **16 个选题建议** (第 7 节)

## 1. 总览: 三个结构性发现

全库 234 个 = 520 目标的 **45%**。按体量走到了近半程, 但分布严重偏科, 三个问题一个比一个大:

| # | 发现 | 数字 | 影响 |
| --- | --- | --- | --- |
| 1 | **难度塌缩到 D3** | D1 **0**/78、D2 20/130、D3 **169/156 (已超终态目标)**、D4 44/104、D5 **1**/52 | 策略定位 D1 是引流入口 (15%)、D4–D5 是订阅转化的"灯塔内容" (30%)——目前引流入口不存在, 灯塔只有 `skyscraper_01` 一座 |
| 2 | **约三成模型落在 13 主题矩阵之外** | 69/234 (29.5%) 无法归入任何策略主题 (城市生活/职业体验/运动/田园农事等, 明细见第 6 节) | 矩阵外内容本身质量合格且有留存价值, 但它挤占了批次产能——矩阵内 13 主题合计只到 165/520 (32%) |
| 3 | **四个主题近乎空转** | 实用功能 1/36、几何艺术 2/44、滚珠乐园 3/38、桥梁工程 4/40 | 这四个主题合计缺 148 个, 占全部剩余缺口 (520−165=355) 的 42%; 其中滚珠乐园是策略钦点的"可玩性"招牌主题 |

结论先行: **批 F–I 不缺"再来 16 个 D3 场景", 缺的是 D1/D2 入门位与 D4/D5 灯塔位, 且必须落在饥饿主题上。** 第 7 节的 16 个选题全部按此原则给出 (7 × D1、6 × D2、1 × D4、2 × D5; 零 D3)。

## 2. 口径与归类方法

`data/model_catalog.json` 的 `theme` 字段是**展示用主题角标** (由标签推导, 如「城市生活」「田园」「运动」), 与策略 2.2 节的 13 个排期主题**不是同一套词表**; 全库 234 个模型的 `content_meta.series` 字段 (schema v2 中承载策略主题的正字段) **全部缺失**。因此本审计按模型 id / 名称 / 标签 / 描述逐一人工归入 13 主题, 归类判例如下:

1. **就近归入, 但不硬塞**: 与某主题定位 (2.2 节右列) 明确同族的才归入; 城市生活/职业体验/运动/田园农事等确无归属的, 记入「矩阵外」桶, 不摊薄矩阵内数字。
2. **载具基础设施跟随载具主题**: 机场航站楼/塔台/机库/港口/船坞/灯塔 → 海空交通; 车站/道口/停车场/加油站 → 陆地交通 (工程机械亦按策略原文归陆地交通)。
3. **策略文档自带判例优先**: 2.2/§6 节点名的归属直接沿用——`rescue_hq_01`/`roman_aqueduct_01` → 建筑地标 (§6 ⑪⑧), `trex_skeleton_01` → 动物世界 (§6 ②), 摩天轮/风车/机甲 → 幻想与机械 (2.2 节原文), 测地穹顶 → 几何艺术 (§6 ⑤)。
4. **动物场馆归动物世界**: 动物园馆舍/观兽设施 (企鹅池、大象馆、观鲸站) 与具象动物同归, 因其造型主角是动物。
5. **民俗节庆归节日限定**: 龙舟 (端午)、舞狮 (新春)、雪人 (冬季亲子) 按节庆属性归入, 不按"船/人偶"拆散。

逐模型归类清单全文见附录 A, 复核时可逐条对质。

## 3. 主题 × 难度矩阵: 现状 / 520 目标

每格为 `现状/目标`; 「应到」列为按当前进度 (234/520 = 45%) 的线性应到数, 用于判断主题是超前还是欠账。

| 主题 | D1 | D2 | D3 | D4 | D5 | 合计 | 完成度 | 应到(45%) | 判定 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 城堡与要塞 | 0/6 | 0/10 | 6/14 | 1/8 | 0/4 | 7/42 | 17% | 18.9 | 欠账 |
| 陆地交通 | 0/8 | 5/12 | **26/12** | 7/8 | 0/2 | 38/42 | 90% | 18.9 | 超前 (D3 超编 14) |
| 海空交通 | 0/4 | 0/8 | **13/10** | **8/8** | 0/2 | 21/32 | 66% | 14.4 | 超前 (D3/D4 已满) |
| 航天器 | 0/4 | 2/8 | **15/10** | 1/8 | 0/4 | 18/34 | 53% | 15.3 | 略超 (全堆在 D3) |
| 动物世界 | 0/10 | 2/14 | **20/14** | 2/8 | 0/2 | 24/48 | 50% | 21.6 | 略超 (D3 超编 6) |
| 建筑地标 | 0/4 | 0/10 | 9/14 | 6/12 | 1/10 | 16/50 | 32% | 22.5 | 欠账 (D5 缺 9) |
| 桥梁工程 | 0/2 | 0/8 | 3/12 | 1/10 | 0/8 | 4/40 | 10% | 18.0 | **重度欠账** |
| 几何艺术 | 0/8 | 1/12 | 1/12 | 0/8 | 0/4 | 2/44 | 5% | 19.8 | **重度欠账** |
| 滚珠乐园 | 0/2 | 0/8 | 1/12 | 2/10 | 0/6 | 3/38 | 8% | 17.1 | **重度欠账** |
| 植物花园 | 0/8 | 1/10 | 3/10 | 3/4 | 0/0 | 7/32 | 22% | 14.4 | 欠账 |
| 节日限定 | 0/8 | 0/10 | 8/10 | 0/6 | 0/2 | 8/36 | 22% | 16.2 | 欠账 (全是 D3) |
| 实用功能 | 0/10 | 1/12 | 0/10 | 0/4 | 0/0 | 1/36 | 3% | 16.2 | **重度欠账** |
| 幻想与机械 | 0/4 | 2/8 | 14/16 | 0/10 | 0/8 | 16/46 | 35% | 20.7 | 欠账 (D4/D5 全空) |
| **矩阵内小计** | **0/78** | **14/130** | **119/156** | **31/104** | **1/52** | **165/520** | 32% | — | |
| 矩阵外 (第 6 节) | 0 | 6 | 50 | 13 | 0 | 69 | — | — | 占全库 29.5% |
| **全库合计** | **0** | **20** | **169** | **44** | **1** | **234** | 45% | — | |

## 4. 难度轴分析: D3 单极

| 难度 | 现状 | 520 目标 | 45% 应到 | 达成率(对应到) | 诊断 |
| --- | ---: | ---: | ---: | ---: | --- |
| D1 (入门, 20–28 片) | **0** | 78 | 35.1 | **0%** | 策略把 D1 定为 4–6 岁亲子引流入口, 现库对该人群**无一可搭**; 免费 30 里最低门槛也是 D2 |
| D2 (进阶, 28–48 片) | 20 | 130 | 58.5 | 34% | 严重不足; 免费层"全库仅有的 4 个 D2 全部免费"侧面印证 D2 稀缺 |
| D3 (熟练, 48–75 片) | 169 | 156 | 70.2 | **241%** | **已超过 520 终态目标 13 个**; 后续批次每加一个 D3, 终态就要多砍一个 |
| D4 (挑战, 75–110 片) | 44 | 104 | 46.8 | 94% | 总量健康, 但集中在陆交/海空/矩阵外; 幻想与机械 (0/10)、滚珠 (2/10)、桥梁 (1/10) 的 D4 灯塔位空着 |
| D5 (大师, 110–180 片) | **1** | 52 | 23.4 | **4%** | 仅 `skyscraper_01`; D4–D5 合计占比 19% (目标 30%), 订阅转化的"灯塔内容"是最大商业缺口 |

生产惯性显而易见: 批 A–E 的舒适区是 50–75 片的 D3 场景模型。**建议自批 F 起对 D3 执行冻结 (策展人按 4.4 节职责冻结排期), 直到 D1 ≥ 20、D5 ≥ 6。**

## 5. 主题缺口排序 (矩阵内)

按「应到(45%) − 现状」的欠账绝对值排序:

| 排名 | 主题 | 现状 | 应到 | 欠账 | 最饿的格子 (现状/目标) |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | 几何艺术 | 2 | 19.8 | −17.8 | D1 0/8、D2 1/12、D3 1/12、D4 0/8 |
| 2 | 实用功能 | 1 | 16.2 | −15.2 | D1 0/10、D2 1/12、D3 0/10 |
| 3 | 滚珠乐园 | 3 | 17.1 | −14.1 | D2 0/8、D3 1/12、D5 0/6 |
| 4 | 桥梁工程 | 4 | 18.0 | −14.0 | D2 0/8、D3 3/12、D4 1/10、D5 0/8 |
| 5 | 城堡与要塞 | 7 | 18.9 | −11.9 | D1 0/6、D2 0/10、D3 6/14 |
| 6 | 节日限定 | 8 | 16.2 | −8.2 | D1 0/8、D2 0/10 (现有 8 个全是 D3); 万圣节零覆盖 (策略点名) |
| 7 | 植物花园 | 7 | 14.4 | −7.4 | D1 0/8、D2 1/10; "花/盆栽"原型仅玫瑰长廊 1 例 |
| 8 | 建筑地标 | 16 | 22.5 | −6.5 | D5 1/10 (次于摩天楼再无灯塔) |
| 9 | 幻想与机械 | 16 | 20.7 | −4.7 | D4 0/10、D5 0/8 (龙/机甲高难灯塔全空) |
| — | 动物世界/航天器/海空交通/陆地交通 | — | — | 持平或超前 | 共同问题: D1 全部为 0 |

## 6. 矩阵外 69 个: 定性与治理建议

矩阵外模型按目录展示主题聚类: 城市生活 23、运动 11、田园 (农舍/梯田/玉米迷宫等农事场景) 7、工程结构 (船闸/大坝/水塔/光伏等市政工程) 6、自然世界 (营地/绿洲/火山/气象站) 4、音乐 4、校园 4、海洋航行 (海底实验室/救生站/海滩小屋) 3、博物馆 2、其他 5。

这批内容**不是废品**——城市生活/职业体验是免费 30 的主力供给, 运动与校园自带亲子话题性。问题在于策略与产线两张皮: 2.2 节矩阵没有这些主题的排期名额, 它们的产出也就不消耗任何格子, 导致"批批有产出、矩阵不前进"。治理建议 (二选一, 由策展人决断):

1. **修订矩阵**: 在 CONTENT_STRATEGY.md 2.2 节增设「城市生活」「运动场馆」「田园农庄」等主题并分配 D1–D5 名额, 承认既成事实, 重分 520 总盘;
2. **冻结矩阵外供给**: 批 F 起选题池只从 13 主题缺口出题, 矩阵外存量作为"番外"沉淀。

无论选哪条, 都应**回填全库 `content_meta.series` 字段** (13 主题词表 + 增设主题), 让本审计从人工归类变成 `update_model_catalog.py` 可机检的常规指标。附录 A 的归类清单可直接作为回填底稿。

## 7. 批 F–I 选题建议 (16 个)

选题原则: ① 只打第 5 节的饥饿格子; ② 难度配比 7×D1 + 6×D2 + 1×D4 + 2×D5, **零 D3**; ③ D1 主技法受难度带约束只能用 T01/T18 (1.1 节), 每批主技法重复 ≤ 2、主题不重复 (满足 4.3 节批次纪律); ④ D1/D2 选题全部限定 core-9 片型 (免费层候补池, 2.5 节); ⑤ 每个选题给出与最近似库内模型的差异锚点 (3.2 节唯一性预检); ⑥ 「招牌方向」仅为策展预审输入, 正式 `signature_statement` 须由结构设计师撰写 (4.2 节 AI 边界)。

### 批 F (2×D1 + 1×D2 + 1×D4)

| # | 建议 id | 选题 | 主题 | 难度 | 片数预算 | 主技法 + 次技法 | 招牌方向 / 差异锚点 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | `photo_frame_01` | 自立相框画架 | 实用功能 | D1 | 22 | T01 盒式 + T14 斜撑 | 后撑三角让相框自立, 双层地台夹缝即插纸槽; 与 `desk_organizer_01` (桌面收纳站) 功能与剪影均不同 |
| F2 | `tessellation_lantern_01` | 密铺柱面灯笼 | 几何艺术 | D1 | 24 | T18 密铺 + T13 薄壳 | 密铺立上柱面成灯笼腔体 (满足 J4 "密铺必须立起来"); 与 `tessellation_screen_01` (平面三折屏风) 形态相异 |
| F3 | `sunflower_pot_01` | 向日葵盆栽 | 植物花园 | D2 | 34 | T05 平面翻折 + T11 镜像 | 花盘放射展开图一次向心翻折立起花瓣; 补"盆栽"原型空白, 与 `rose_pergola_01` (长廊花架) 无相似结构 |
| F4 | `truss_bridge_01` | 钢桁架大桥 | 桥梁工程 | D4 | 88 | T02 桁架 + T11 镜像 + T14 斜撑 | 上承式三角桁架连排跨河, 补桥梁四原型中缺失的"桁架桥"; 与 `suspension_bridge_01` (悬索)/`covered_bridge_01` (廊桥屋盖) 传力逻辑不同; D4 需实物复核 |

### 批 G (2×D1 + 1×D2 + 1×D5)

| # | 建议 id | 选题 | 主题 | 难度 | 片数预算 | 主技法 + 次技法 | 招牌方向 / 差异锚点 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | `watchtower_01` | 城墙转角哨塔 | 城堡与要塞 | D1 | 24 | T01 盒式 + T17 负空间 | 单塔 + 转角城墙短段, 箭窗负空间; 城堡主题首个 D1, 与 `castle_tower_01` (75 片土丘要塞) 体量与结构均拉开 |
| G2 | `halloween_pumpkin_01` | 万圣节南瓜灯屋 | 节日限定 | D1 | 26 | T01 盒式 + T17 负空间 | 三角眼嘴洞口即鬼脸, 洞口周边闭环传力; 补万圣节零覆盖 (2.2 节点名节日) |
| G3 | `swan_01` | 白天鹅 | 动物世界 | D2 | 36 | T11 镜像 + T12 层叠 | 双翼镜像同步下料, S 颈以退台内收把重心拉回接地凸包; 动物世界首批 D2 具象动物 |
| G4 | `marble_relay_city_01` | 四塔接力滚珠城 | 滚珠乐园 | D5 | 128 | T08 滚珠轨道 + T16 分体对接 + T11 镜像 | 四座发球塔分体预制、对接成环形接力动线, 弹珠跨塔换轨; 与 `ball_run_tower_01` (单塔双轨) / `marble_run_spiral_01` (螺旋滑道) 动线拓扑不同; 全库第 2 个 D5, 入库前 100% 实物跑珠 |

### 批 H (2×D1 + 1×D2 + 1×D5)

| # | 建议 id | 选题 | 主题 | 难度 | 片数预算 | 主技法 + 次技法 | 招牌方向 / 差异锚点 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | `storage_chest_01` | 翻盖百宝盒 | 实用功能 | D1 | 24 | T01 盒式 + T05 翻折 | 盖板平拼后整体翻折合盖, 磁吸边即铰链; 与 `desk_organizer_01` (敞口格架) 开合方式不同 |
| H2 | `tulip_bed_01` | 郁金香花坛 | 植物花园 | D1 | 26 | T01 盒式 + T18 密铺 | 花坛围栏围合 + 三支郁金香立柱, 围栏色带按密铺节奏交替; 补"花"原型 D1 空白 |
| H3 | `star_octahedron_01` | 星形八面体摆件 | 几何艺术 | D2 | 30 | T05 平面翻折 + T11 镜像 | 两组四面体互穿成星芒, 底座正对角自锁; 几何艺术首个多面体 (现库仅密铺与穹顶各 1) |
| H4 | `temple_of_heaven_01` | 祈年殿 | 建筑地标 | D5 | 132 | T12 层叠退台 + T04 拱 + T13 薄壳 | 三重圆檐攒尖 + 圆形台基, 逐环收分; 与 `pagoda_01` (方檐五重塔 D3) 檐形/平面制式均不同; 补 D5 灯塔 (地标 D5 现 1/10), 兼顾国内市场号召力; 逐一实物复核 |

### 批 I (1×D1 + 3×D2)

| # | 建议 id | 选题 | 主题 | 难度 | 片数预算 | 主技法 + 次技法 | 招牌方向 / 差异锚点 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I1 | `santa_sleigh_01` | 圣诞驯鹿雪橇 | 节日限定 | D2 | 36 | T09 车辆底盘 + T11 镜像 | 弧形滑刃以直角三角连排代替车轮, 礼物箱可开舱; 与 `christmas_market_01` (集市货亭) 同节日不同结构 |
| I2 | `marble_cascade_01` | 阶梯瀑布滚珠台 | 滚珠乐园 | D2 | 34 | T12 层叠退台 + T08 滚珠轨道 | 三级退台即三级落珠瀑布, 轨道服从台阶几何 (T08 难度带 3–5, 故以 T12 为主技法降档入门); 滚珠主题首个 D2, 仍需实物跑珠 |
| I3 | `trestle_bridge_01` | 三跨栈桥梁桥 | 桥梁工程 | D2 | 32 | T14 斜撑 + T16 分体对接 | 等距三跨分体预制、斜撑桥墩逐跨对接; 补桥梁"梁桥"原型 D2 空白, 与 `bridge_wood_01` (单跨乡间木桥 D3) 跨数与装配范式不同 |
| I4 | `mini_bus_01` | 迷你小巴 | 陆地交通 | D1 | 26 | T01 盒式 + T09 车辆底盘 | 车轮底座核心片首个 D1 载具, 全库第一个孩子能独立完成的"车"; 陆地交通总量虽超前, 但 D1 格 0/8——引流格优先于总量 |

**落地后走势**: 批 F–I 完成时全库 250 个, D1 0→7、D2 20→26、D5 1→3, 实用功能 1→3、几何艺术 2→4、滚珠乐园 3→6、桥梁工程 4→6; D3 保持 169 不再恶化。D1 缺口 (78) 靠 4 批填不满, 建议批 J 起将 D1/D2 占比长期锁定在每批 3/4 以上, 直至 D1 追平应到线。

## 附录 A: 逐模型归类清单 (234 个)

复核用底稿; 归类判例见第 2 节。格式: `id(D难度)`。

**城堡与要塞 (7)**: castle_foundation_01(D3), castle_tower_01(D3), drawbridge_01(D3), knight_armor_01(D3), medieval_gate_01(D3), trebuchet_01(D3), castle_drawbridge_01(D4)

**陆地交通 (38)**: car_repair_shop_01(D2), city_bus_stop_01(D2), forklift_01(D2), snowplow_01(D2), tow_truck_01(D2), ambulance_01(D3), bulldozer_01(D3), bullet_train_01(D3), cable_car_01(D3), car_wash_01(D3), cement_mixer_01(D3), combine_harvester_01(D3), crane_tower_01(D3), crane_tower_02(D3), dump_truck_01(D3), excavator_01(D3), fire_truck_01(D3), food_truck_01(D3), gas_station_01(D3), ice_cream_truck_01(D3), monorail_01(D3), mountain_rail_01(D3), police_car_01(D3), railway_crossing_01(D3), road_construction_01(D3), suspension_rail_01(D3), taxi_01(D3), toll_station_01(D3), tractor_01(D3), traffic_light_junction_01(D3), trailer_home_01(D3), freight_yard_01(D4), parking_garage_01(D4), race_track_01(D4), school_bus_01(D4), steam_locomotive_01(D4), subway_station_01(D4), train_station_01(D4)

**海空交通 (21)**: airport_terminal_02(D3), canoe_01(D3), cargo_plane_01(D3), control_tower_01(D3), cruise_ship_01(D3), drone_pad_01(D3), fishing_boat_01(D3), hangar_01(D3), helicopter_pad_01(D3), hot_air_balloon_01(D3), lighthouse_pier_01(D3), sailboat_01(D3), submarine_01(D3), aircraft_carrier_01(D4), airport_terminal_01(D4), cargo_ship_01(D4), ferry_terminal_01(D4), harbor_crane_01(D4), helicopter_01(D4), lighthouse_01(D4), submarine_dock_01(D4)

**航天器 (18)**: astronaut_training_01(D2), capsule_recovery_01(D2), asteroid_mining_01(D3), lunar_lander_01(D3), mars_habitat_01(D3), mars_rover_01(D3), mission_control_01(D3), moon_lander_01(D3), observatory_01(D3), planetarium_01(D3), planetarium_02(D3), radio_telescope_01(D3), rocket_crawler_01(D3), satellite_dish_01(D3), space_elevator_01(D3), space_shuttle_01(D3), space_station_01(D3), rocket_launchpad_01(D4)

**动物世界 (24)**: apiary_01(D2), turtle_beach_01(D2), aquarium_tunnel_01(D3), butterfly_01(D3), butterfly_garden_01(D3), chicken_coop_01(D3), coral_reef_01(D3), coral_reef_02(D3), crocodile_01(D3), dinosaur_stego_01(D3), elephant_pavilion_01(D3), giraffe_01(D3), horse_stable_01(D3), owl_01(D3), panda_bamboo_01(D3), penguin_01(D3), penguin_pool_01(D3), safari_lodge_01(D3), sheep_farm_01(D3), trex_skeleton_01(D3), whale_01(D3), whale_watching_01(D3), dinosaur_hall_01(D4), elephant_01(D4)

**建筑地标 (16)**: amphitheater_01(D3), chinese_garden_01(D3), clock_tower_01(D3), great_wall_01(D3), museum_01(D3), pagoda_01(D3), pyramid_giza_01(D3), sydney_opera_01(D3), tokyo_tower_01(D3), eiffel_tower_01(D4), hanging_garden_01(D4), rescue_hq_01(D4), roman_aqueduct_01(D4), temple_greek_01(D4), triumphal_arch_01(D4), skyscraper_01(D5)

**桥梁工程 (4)**: bridge_wood_01(D3), pedestrian_overpass_01(D3), suspension_bridge_01(D3), covered_bridge_01(D4)

**几何艺术 (2)**: tessellation_screen_01(D2), geodesic_dome_01(D3)

**滚珠乐园 (3)**: marble_dash_lane_01(D3), ball_run_tower_01(D4), marble_run_spiral_01(D4)

**植物花园 (7)**: rose_pergola_01(D2), cactus_desert_01(D3), greenhouse_01(D3), greenhouse_dome_01(D3), rainforest_canopy_01(D4), treehouse_01(D4), treehouse_02(D4)

**节日限定 (8)**: birthday_party_01(D3), christmas_market_01(D3), dragon_boat_01(D3), fireworks_show_01(D3), lantern_festival_01(D3), lion_dance_01(D3), moon_festival_altar_01(D3), snowman_01(D3)

**实用功能 (1)**: desk_organizer_01(D2)

**幻想与机械 (16)**: gingerbread_house_01(D2), robot_arm_01(D2), carousel_01(D3), dragon_cave_01(D3), fairy_castle_01(D3), ferris_wheel_frame_01(D3), magic_tree_01(D3), merry_go_round_01(D3), robot_01(D3), robot_lab_01(D3), roller_coaster_hill_01(D3), roller_coaster_loop_01(D3), spider_bot_01(D3), wind_turbine_01(D3), windmill_01(D3), wizard_tower_01(D3)

**矩阵外 (69)** — 城市生活 23 / 运动 11 / 田园 7 / 工程结构 6 / 自然世界 4 / 音乐 4 / 校园 4 / 海洋航行 3 / 博物馆 2 / 其他 5: beach_hut_01(D2), boxing_ring_01(D2), lifeguard_tower_01(D2), puppet_theater_01(D2), rehab_park_01(D2), weather_station_01(D2), art_gallery_01(D3), bakery_shop_01(D3), bamboo_house_01(D3), basketball_court_01(D3), bike_rack_park_01(D3), bowling_alley_01(D3), cabin_lake_01(D3), campfire_site_01(D3), canal_lock_01(D3), climbing_wall_01(D3), conveyor_factory_01(D3), corn_maze_01(D3), deep_sea_lab_01(D3), dental_clinic_01(D3), diving_tower_01(D3), drive_in_cinema_01(D3), drum_set_01(D3), er_entrance_01(D3), eye_clinic_01(D3), farm_barn_01(D3), farm_silo_01(D3), flag_plaza_01(D3), fountain_plaza_01(D3), hydro_dam_01(D3), igloo_01(D3), jungle_gym_01(D3), kindergarten_01(D3), lego_style_house_01(D3), marching_band_01(D3), oasis_01(D3), open_air_cinema_01(D3), particle_accelerator_01(D3), piano_stage_01(D3), police_station_01(D3), rice_terrace_01(D3), sandbox_park_01(D3), scaffolding_site_01(D3), schoolyard_stand_01(D3), science_lab_01(D3), sculpture_plaza_01(D3), skate_park_01(D3), ski_jump_01(D3), ski_lodge_01(D3), slide_playground_01(D3), solar_farm_01(D3), supermarket_01(D3), swimming_pool_01(D3), violin_shop_01(D3), water_slide_park_01(D3), water_tower_01(D3), apartment_block_01(D4), basketball_arena_01(D4), fire_station_01(D4), hospital_01(D4), ice_rink_01(D4), library_building_01(D4), pet_clinic_01(D4), post_office_01(D4), soccer_goal_01(D4), stadium_gate_01(D4), tennis_court_01(D4), volcano_base_01(D4), warehouse_01(D4)
