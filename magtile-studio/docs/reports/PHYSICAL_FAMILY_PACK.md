# D4+ 实物复核结构族去重包 (Physical Family Pack)

- 生成日期: 2026-08-26
- 生成工具: `tools/physical_family_pack.py --markdown docs/reports/PHYSICAL_FAMILY_PACK.md` —— 模型库 / 复核状态 / 风险报告变化后**重新生成**, 勿手改; 缓建签核以策展书面记录为准, 本报告只提供确定性族划分与估算
- 风险分来源: 复用风险报告 PHYSICAL_RISK_REPORT.json (physical_risk_report 产物, 接口约定见 BUILD_VERIFICATION.md 2.1 节); 已复核判定与 `tools/list_physical_pending.py` 同源 (同一 classify 函数)

## 1. 定位 (与上架抽样包互补)

[`PHYSICAL_SAMPLE_V1.md`](PHYSICAL_SAMPLE_V1.md) 回答「上架前哪些必须**先**搭」(免费层/D5/大片数旗舰的**抽样**); 本报告回答「哪些结构原型彼此**重复**」(全集清零阶段的**去重**): 每族先实搭 1 个代表, 代表通过后同族其余 D4+ 成员可向策展申请缓建, 削减重复实搭人手。两清单取并集, 抽样包成员始终必搭不参与缓建。**族去重不豁免全集清零** —— `tools/run_release_gate.sh --fail-on-pending` 终防线仍以 D4+ 全集为准, 缓建只是排产顺序与人手预算的工程估算, 采纳与否是策展/QA 的政策决定。

## 2. 聚类口径 (确定性, 重跑可复现)

| 要素 | 取值 |
| --- | --- |
| 特征 | `content_meta.structural_signature.tile_histogram` + difficulty + 主题 tags (剔除层级标记 免费/进阶/挑战/需要扩展装, 并入 catalog theme) |
| 相似度 | 0.60 x 片型直方图加权 Jaccard (逐片型 Σmin/Σmax) + 0.25 x 主题标签 Jaccard + 0.15 x 难度接近度 (1 - 难度差/4) |
| 硬门 | 至少共享 1 个主题标签 且 难度差 <= 1 |
| 聚法 | 完全连接凝聚聚类, 族内任意两成员相似度 >= 0.67 (非单连接, 防传递链假同族) |

全库 250 个模型聚成 **191 族**: 多成员族 46 个 (共 105 模型, 折叠 59 个重复原型), 单模型族 145 个 (D1 x18, D2 x15, D3 x83, D4 x24, D5 x5)。片型直方图是**备料构成**视角, 不含连接拓扑 —— 同族成员工序仍可能不同, 这是缓建须人工签核而非自动豁免的根本原因。

## 3. 结构族表 (多成员族 46 个)

| 族 | 规模 | 难度 | 共同标签 | 族内最低相似度 | 成员 (**粗体 = 代表**) |
| --- | --- | --- | --- | --- | --- |
| F001 | 4 | D3 | 交通、城市、城市生活、街景 | 0.745 | `car_wash_01` `pedestrian_overpass_01` `toll_station_01` **`traffic_light_junction_01`** |
| F002 | 4 | D3 | 中世纪、城堡、城堡王国 | 0.676 | **`castle_tower_01`** `drawbridge_01` `medieval_gate_01` `trebuchet_01` |
| F003 | 3 | D3 | 城市、城市生活 | 0.704 | **`ambulance_01`** `er_entrance_01` `fire_truck_01` |
| F004 | 3 | D3 | 城市、城市生活 | 0.682 | `bike_rack_park_01` **`dental_clinic_01`** `kindergarten_01` |
| F005 | 3 | D3 | 工程、工程结构、载具 | 0.689 | `bulldozer_01` **`dump_truck_01`** `road_construction_01` |
| F006 | 3 | D3 | 城市生活 | 0.734 | **`cable_car_01`** `gas_station_01` `sandbox_park_01` |
| F007 | 3 | D3 | 自然世界 | 0.684 | `cactus_desert_01` `dinosaur_stego_01` **`kangaroo_01`** |
| F008 | 3 | D2 | 城市、城市生活 | 0.693 | `city_bus_stop_01` **`puppet_theater_01`** `rehab_park_01` |
| F009 | 3 | D4 | 城市、城市生活、建筑、职业体验 | 0.807 | **`fire_station_01`** `pet_clinic_01` `post_office_01` |
| F010 | 3 | D4 | 交通、城市生活、火车 | 0.671 | `freight_yard_01` **`steam_locomotive_01`** `train_station_01` |
| F011 | 3 | D2~D3 | 城市、城市生活、车轮底座、载具 | 0.682 | **`police_car_01`** `snowplow_01` `taxi_01` |
| F012 | 2 | D4 | 载具 | 0.680 | **`aircraft_carrier_01`** `race_track_01` |
| F013 | 2 | D4 | 交通、城市、城市生活 | 0.740 | **`airport_terminal_01`** `parking_garage_01` |
| F014 | 2 | D3 | 机场、航空 | 0.677 | `airport_terminal_02` **`control_tower_01`** |
| F015 | 2 | D4~D5 | 旗舰、滚珠、滚珠乐园、竞速 | 0.775 | `ball_run_tower_01` **`marble_grand_cascade_01`**† |
| F016 | 2 | D2 | 沙滩、海岸、海洋航行 | 0.685 | `beach_hut_01` **`lifeguard_tower_01`** |
| F017 | 2 | D3 | 节日 | 0.673 | **`birthday_party_01`** `pumpkin_lantern_01` |
| F018 | 2 | D3 | 运动 | 0.740 | **`bowling_alley_01`** `horse_stable_01` |
| F019 | 2 | D3 | 田园 | 0.749 | `bridge_wood_01` **`chicken_coop_01`** |
| F020 | 2 | D3 | 自然世界 | 0.708 | `butterfly_01` **`giraffe_01`** |
| F021 | 2 | D3 | 动物园、野生动物 | 0.730 | `butterfly_garden_01` **`elephant_pavilion_01`** |
| F022 | 2 | D3 | 自然 | 0.717 | `cabin_lake_01` **`panda_bamboo_01`** |
| F023 | 2 | D3 | 自然、自然世界 | 0.699 | `campfire_site_01` **`canoe_01`** |
| F024 | 2 | D3 | 机场、航空 | 0.748 | `cargo_plane_01` **`hangar_01`** |
| F025 | 2 | D3 | 农场、田园、车轮底座 | 0.693 | **`combine_harvester_01`** `tractor_01` |
| F026 | 2 | D3 | 海洋航行 | 0.685 | `coral_reef_02` **`fishing_boat_01`** |
| F027 | 2 | D3 | 工程、工程结构 | 0.671 | `crane_tower_01` **`suspension_bridge_01`** |
| F028 | 2 | D3 | 动物世界、自然、自然世界 | 0.749 | **`crocodile_01`** `hedgehog_01` |
| F029 | 2 | D3 | 运动 | 0.690 | `diving_tower_01` **`slide_playground_01`** |
| F030 | 2 | D1 | 亲子入门 | 0.677 | `duckling_pond_01` **`festival_gate_01`** |
| F031 | 2 | D3 | 奇幻、童话 | 0.696 | **`fairy_castle_01`** `magic_tree_01` |
| F032 | 2 | D3 | 海洋、海洋航行 | 0.698 | **`fireboat_01`** `whale_01` |
| F033 | 2 | D2 | 城市、城市生活、职业体验 | 0.703 | **`forklift_01`** `tow_truck_01` |
| F034 | 2 | D4 | 海洋航行、港口 | 0.723 | `harbor_crane_01` **`submarine_dock_01`** |
| F035 | 2 | D4 | 城市生活 | 0.720 | **`helicopter_01`** `library_building_01` |
| F036 | 2 | D3 | 工程、工程结构 | 0.701 | **`hydro_dam_01`** `solar_farm_01` |
| F037 | 2 | D3 | 海岸、海洋航行 | 0.706 | **`lighthouse_pier_01`** `whale_watching_01` |
| F038 | 2 | D3 | 航天探索 | 0.681 | `lunar_lander_01` **`radio_telescope_01`** |
| F039 | 2 | D3 | 航天、航天器、航天探索 | 0.749 | `moon_lander_01` **`space_shuttle_01`** |
| F040 | 2 | D3 | 交通、城市生活、火车 | 0.793 | **`mountain_rail_01`** `railway_crossing_01` |
| F041 | 2 | D3 | 动物世界、自然、自然世界 | 0.737 | **`owl_01`** `peacock_01` |
| F042 | 2 | D3 | 帆船、海洋、海洋航行 | 0.722 | **`pirate_ship_01`** `sailboat_01` |
| F043 | 2 | D4 | 树屋、自然、自然世界 | 0.700 | `rainforest_canopy_01` **`treehouse_01`** |
| F044 | 2 | D4 | 城市生活 | 0.704 | **`rescue_hq_01`** `stadium_gate_01`† |
| F045 | 2 | D3 | 航天、航天探索 | 0.686 | `satellite_dish_01` **`space_station_01`** |
| F046 | 2 | D4 | 建筑地标 | 0.695 | `temple_greek_01` **`triumphal_arch_01`** |

† = 同时入选上架抽样包 (必搭, 不参与缓建)。单模型族的代表即其自身, 含单模型族的全量族表见 `tools/physical_family_pack.py --json`。

## 4. 代表清单 (多成员族, 46 个)

| 族 | 代表 | 名称 | 难度 | 片数 | 步数 | L2 标记 | 风险分 | 复核状态 | 上架抽样包 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F001 | `traffic_light_junction_01` | 红绿灯路口 | D3 | 74 | 13 | `tall_wall_chain` | 37.3 | 待复核 | 否 |
| F002 | `castle_tower_01` | 土丘要塞主塔 | D3 | 75 | 13 | `tall_wall_chain` | 42.7 | 待复核 | 否 |
| F003 | `ambulance_01` | 120 急救车 | D3 | 53 | 16 | `tall_wall_chain` | 33.8 | 待复核 | 否 |
| F004 | `dental_clinic_01` | 牙科诊所 | D3 | 61 | 12 | `tall_wall_chain` | 33.3 | 待复核 | 否 |
| F005 | `dump_truck_01` | 自卸卡车 | D3 | 74 | 18 | `tall_wall_chain` | 36.6 | 待复核 | 否 |
| F006 | `cable_car_01` | 缆车站 | D3 | 64 | 16 | `tall_wall_chain` | 35.5 | 待复核 | 否 |
| F007 | `kangaroo_01` | 袋鼠妈妈 | D3 | 70 | 13 | `tall_wall_chain` | 38.4 | 待复核 | 否 |
| F008 | `puppet_theater_01` | 木偶剧场 | D2 | 46 | 10 | `tall_wall_chain` | 24.4 | 待复核 | 否 |
| F009 | `fire_station_01` | 一号消防站 | D4 | 81 | 19 | `tall_wall_chain` | 50.3 | 待复核 | 否 |
| F010 | `steam_locomotive_01` | 蒸汽机车 | D4 | 99 | 18 | `tall_wall_chain` | 51.2 | 待复核 | 否 |
| F011 | `police_car_01` | 警车 | D3 | 53 | 16 | — | 29.7 | 待复核 | 否 |
| F012 | `aircraft_carrier_01` | 航母甲板段 | D4 | 84 | 18 | `tall_wall_chain` | 46.4 | 待复核 | 否 |
| F013 | `airport_terminal_01` | 国际机场航站楼 | D4 | 77 | 18 | `tall_wall_chain` | 51.3 | 待复核 | 否 |
| F014 | `control_tower_01` | 机场管制塔台 | D3 | 62 | 14 | `tall_wall_chain` | 41.9 | 待复核 | 否 |
| F015 | `marble_grand_cascade_01` | 瀑布双道滚珠梯台 | D5 | 87 | 25 | `tall_wall_chain` | 54.6 | 待复核 | 是 |
| F016 | `lifeguard_tower_01` | 海滩救生站 | D2 | 48 | 11 | `tall_wall_chain` | 25.0 | 待复核 | 否 |
| F017 | `birthday_party_01` | 生日派对 | D3 | 69 | 14 | `tall_wall_chain` | 33.1 | 待复核 | 否 |
| F018 | `bowling_alley_01` | 保龄球馆 | D3 | 56 | 13 | `tall_wall_chain` | 31.4 | 待复核 | 否 |
| F019 | `chicken_coop_01` | 农场鸡舍 | D3 | 62 | 16 | `tall_wall_chain` | 33.0 | 待复核 | 否 |
| F020 | `giraffe_01` | 长颈鹿 | D3 | 52 | 16 | `tall_structure`、`tall_wall_chain` | 44.5 | 待复核 | 否 |
| F021 | `elephant_pavilion_01` | 大象馆 | D3 | 75 | 15 | `tall_wall_chain` | 35.7 | 待复核 | 否 |
| F022 | `panda_bamboo_01` | 竹林大熊猫 | D3 | 65 | 13 | `tall_wall_chain` | 32.3 | 待复核 | 否 |
| F023 | `canoe_01` | 湖上独木舟 | D3 | 68 | 16 | — | 29.9 | 待复核 | 否 |
| F024 | `hangar_01` | 飞机维修机库 | D3 | 74 | 14 | — | 32.7 | 待复核 | 否 |
| F025 | `combine_harvester_01` | 联合收割机 | D3 | 74 | 14 | `tall_wall_chain` | 35.3 | 待复核 | 否 |
| F026 | `fishing_boat_01` | 渔船靠泊 | D3 | 63 | 16 | `tall_wall_chain` | 33.1 | 待复核 | 否 |
| F027 | `suspension_bridge_01` | 海湾悬索桥 | D3 | 74 | 16 | `l1_warning`、`tall_wall_chain` | 55.4 | 待复核 | 否 |
| F028 | `crocodile_01` | 大嘴鳄鱼 | D3 | 53 | 16 | — | 28.9 | 待复核 | 否 |
| F029 | `slide_playground_01` | 滑梯乐园 | D3 | 67 | 16 | `tall_wall_chain` | 35.2 | 待复核 | 否 |
| F030 | `festival_gate_01` | 新春彩门 | D1 | 22 | 5 | — | 11.7 | 待复核 | 否 |
| F031 | `fairy_castle_01` | 仙子天桥城堡 | D3 | 66 | 13 | `tall_wall_chain` | 37.9 | 待复核 | 否 |
| F032 | `fireboat_01` | 消防喷水礼船 | D3 | 63 | 12 | `tall_wall_chain` | 33.5 | 待复核 | 否 |
| F033 | `forklift_01` | 叉车 | D2 | 46 | 10 | — | 22.0 | 待复核 | 否 |
| F034 | `submarine_dock_01` | 潜艇维修船坞 | D4 | 89 | 18 | `tall_wall_chain`、`critical_com_margin` | 50.4 | 待复核 | 否 |
| F035 | `helicopter_01` | 救援直升机 | D4 | 87 | 18 | `tall_wall_chain` | 45.3 | 待复核 | 否 |
| F036 | `hydro_dam_01` | 水电站大坝 | D3 | 62 | 16 | `tall_wall_chain` | 34.9 | 待复核 | 否 |
| F037 | `lighthouse_pier_01` | 灯塔栈桥 | D3 | 72 | 16 | `tall_wall_chain` | 43.4 | 待复核 | 否 |
| F038 | `radio_telescope_01` | 射电望远镜 | D3 | 62 | 16 | `tall_wall_chain`、`weak_edge_load_bearing` | 40.3 | 待复核 | 否 |
| F039 | `space_shuttle_01` | 航天飞机 | D3 | 68 | 15 | — | 31.1 | 待复核 | 否 |
| F040 | `mountain_rail_01` | 登山齿轨小火车 | D3 | 61 | 13 | `tall_wall_chain` | 35.8 | 待复核 | 否 |
| F041 | `owl_01` | 月夜猫头鹰 | D3 | 52 | 12 | `tall_wall_chain` | 34.6 | 待复核 | 否 |
| F042 | `pirate_ship_01` | 海盗船与藏宝码头 | D3 | 74 | 13 | `tall_wall_chain` | 36.4 | 待复核 | 否 |
| F043 | `treehouse_01` | 树屋 | D4 | 79 | 18 | `tall_wall_chain` | 47.2 | 待复核 | 否 |
| F044 | `rescue_hq_01` | 救援行动总部 | D4 | 101 | 18 | `tall_wall_chain` | 48.2 | 待复核 | 否 |
| F045 | `space_station_01` | 轨道空间站 | D3 | 69 | 16 | `tall_wall_chain` | 37.9 | 待复核 | 否 |
| F046 | `triumphal_arch_01` | 凯旋门 | D4 | 88 | 18 | `tall_wall_chain` | 50.6 | 待复核 | 否 |

代表选取规则: D4+ 优先 > 未实物复核优先 > L2 标记命中多者 (风险报告就位时, 检测编码见 BUILD_VERIFICATION.md 第 2 节) > 风险分最高 > id 升序 —— 族内风险上界先过手, 代表通过对同族的覆盖论证才有分量。

## 5. 可削减人手估算 (D4+ 待复核口径)

| 口径 | 模型数 | 实搭预算 |
| --- | ---: | ---: |
| 全集逐个实搭 (基线) | 51 | 3870 分钟 ≈ 64.5 小时 |
| 族去重后必搭 (代表 + 单模型族 + 抽样包成员) | 40 | 3100 分钟 ≈ 51.7 小时 |
| **可缓建 (须策展签核)** | **11** | **770 分钟 ≈ 12.8 小时 (省 20%)** |

| 可缓建模型 | 难度 | 所在族 | 兜底代表 | 单模型预算 |
| --- | --- | --- | --- | ---: |
| `pet_clinic_01` | D4 | F009 | `fire_station_01` | 70 分钟 |
| `post_office_01` | D4 | F009 | `fire_station_01` | 70 分钟 |
| `freight_yard_01` | D4 | F010 | `steam_locomotive_01` | 70 分钟 |
| `train_station_01` | D4 | F010 | `steam_locomotive_01` | 70 分钟 |
| `race_track_01` | D4 | F012 | `aircraft_carrier_01` | 70 分钟 |
| `parking_garage_01` | D4 | F013 | `airport_terminal_01` | 70 分钟 |
| `ball_run_tower_01` | D4 | F015 | `marble_grand_cascade_01` | 70 分钟 |
| `harbor_crane_01` | D4 | F034 | `submarine_dock_01` | 70 分钟 |
| `library_building_01` | D4 | F035 | `helicopter_01` | 70 分钟 |
| `rainforest_canopy_01` | D4 | F043 | `treehouse_01` | 70 分钟 |
| `temple_greek_01` | D4 | F046 | `triumphal_arch_01` | 70 分钟 |

纪律 (缓建不是免检):

1. 缓建只调整**排产顺序**, 不改变门禁 —— 终防线 `--fail-on-pending` 清零口径不变, 缓建成员最终仍须实搭或由策展按族级抽检政策书面豁免;
2. 申请缓建的前提: 同族代表已实搭 **Pass** 且落盘 `content_meta.physical_verified` 三字段; 代表 Fail 则整族全员实搭;
3. 片型直方图不含连接拓扑, 同族成员若含独有高危工序 (悬臂/合壳/大跨度), 策展应将其移出缓建名单;
4. 模型内容变更 (`final_assembly` / `steps`) 后族划分可能失效, 重新生成本报告再议。

## 6. 建议排产顺序

1. 上架抽样包 ([`PHYSICAL_SAMPLE_V1.md`](PHYSICAL_SAMPLE_V1.md), 上架前必须);
2. 本报告第 4 节族代表中尚未覆盖的部分 (按风险分降序);
3. 单模型族的 D4+ 待复核成员;
4. 缓建成员收尾 (或按策展签核的族级抽检政策处理)。

