# D4+ 实物待复核排产队列 (Physical Review Queue)

- 生成日期: 2026-08-25
- 生成工具: `tools/export_physical_review_queue.py --markdown docs/reports/PHYSICAL_REVIEW_QUEUE.md` (CSV 版: `--csv docs/reports/PHYSICAL_REVIEW_QUEUE.csv`) —— 模型库 / 复核状态 / 风险报告变化后**重新生成**, 勿手改
- 数据来源 (单一来源, 本表不重算): 待复核判定与 `tools/list_physical_pending.py` 同源 (同一 classify 函数); 风险分/风险档/L2 标记 复用风险报告 PHYSICAL_RISK_REPORT.json (physical_risk_report 产物, 接口约定见 BUILD_VERIFICATION.md 2.1 节); 必搭/可缓建与 `tools/physical_family_pack.py` 同参数聚类 (阈值 0.67); 抽样包成员与 `tools/physical_sample_pack.py` 同源 (同一 select_sample)
- 排序: 风险分降序 (同分: 难度降序 > id 升序); **必搭 = 上架抽样包 ∪ 多成员族代表 ∪ 单模型族**, 可缓建 = 其余同族成员 (须策展签核, **不豁免** `--fail-on-pending` D4+ 全集清零终防线)

## 1. 摘要

| 口径 | 模型数 | 实搭预算 |
| --- | ---: | ---: |
| 必搭 (先排产) | 36 | 2570 分钟 ≈ 42.8 小时 |
| 可缓建 (须策展签核) | 10 | 700 分钟 ≈ 11.7 小时 |
| **合计 (D4+ 待复核全集)** | **46** | **3270 分钟 ≈ 54.5 小时** |

## 2. 队列 (按风险分降序, 46 行)

| # | 模型 | 名称 | 难度 | 风险分 | 风险档 | L2 标记 | 排产 | 依据 | 族 | 预算 (分) |
| ---: | --- | --- | --- | ---: | --- | --- | --- | --- | --- | ---: |
| 1 | `skyscraper_01` | 城市摩天大楼 | D5 | 63.9 | 高 | `tall_structure`、`tall_wall_chain` | **必搭** | 上架抽样包+单模型族 (S2) | F156 | 120 |
| 2 | `lighthouse_01` | 海岬灯塔 | D4 | 54.6 | 中 | `tall_structure`、`tall_wall_chain` | **必搭** | 单模型族 | F116 | 70 |
| 3 | `eiffel_tower_01` | 埃菲尔铁塔 | D4 | 51.5 | 中 | `tall_structure`、`tall_wall_chain` | **必搭** | 单模型族 | F089 | 70 |
| 4 | `airport_terminal_01` | 国际机场航站楼 | D4 | 51.3 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F013 | 70 |
| 5 | `steam_locomotive_01` | 蒸汽机车 | D4 | 51.2 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F010 | 70 |
| 6 | `triumphal_arch_01` | 凯旋门 | D4 | 50.6 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F052 | 70 |
| 7 | `castle_drawbridge_01` | 吊桥城堡 | D4 | 50.4 | 中 | `tall_wall_chain` | **必搭** | 上架抽样包+单模型族 (S3) | F071 | 70 |
| 8 | `marble_run_spiral_01` | 弹珠螺旋滑道 | D4 | 50.4 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F015 | 70 |
| 9 | `submarine_dock_01` | 潜艇维修船坞 | D4 | 50.4 | 中 | `tall_wall_chain`、`critical_com_margin` | **必搭** | 族代表 | F036 | 70 |
| 10 | `fire_station_01` | 一号消防站 | D4 | 50.3 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F009 | 70 |
| 11 | `rocket_launchpad_01` | 火箭发射台 | D4 | 50.2 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F142 | 70 |
| 12 | `subway_station_01` | 地铁一号线车站 | D4 | 49.8 | 中 | `tall_wall_chain` | **必搭** | 上架抽样包+单模型族 (S3) | F163 | 70 |
| 13 | `covered_bridge_01` | 风雨廊桥 | D4 | 48.7 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F080 | 70 |
| 14 | `ball_run_tower_01` | 螺旋滚珠塔 | D4 | 48.5 | 中 | `tall_wall_chain` | **必搭** | 上架抽样包 (S3) | F015 | 70 |
| 15 | `rescue_hq_01` | 救援行动总部 | D4 | 48.2 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F049 | 70 |
| 16 | `roman_aqueduct_01` | 罗马水道桥 | D4 | 48.2 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F145 | 70 |
| 17 | `treehouse_01` | 树屋 | D4 | 47.2 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F047 | 70 |
| 18 | `rainforest_canopy_01` | 雨林树冠天桥 | D4 | 47.0 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `treehouse_01` 兜底 | F047 | 70 |
| 19 | `harbor_crane_01` | 港口门吊 | D4 | 46.8 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `submarine_dock_01` 兜底 | F036 | 70 |
| 20 | `aircraft_carrier_01` | 航母甲板段 | D4 | 46.4 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F012 | 70 |
| 21 | `hospital_01` | 医院 | D4 | 46.2 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F107 | 70 |
| 22 | `parking_garage_01` | 立体停车场 | D4 | 46.2 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `airport_terminal_01` 兜底 | F013 | 70 |
| 23 | `elephant_01` | 大象 | D4 | 46.1 | 中 | `tall_wall_chain` | **必搭** | 上架抽样包+单模型族 (S3) | F090 | 70 |
| 24 | `helicopter_01` | 救援直升机 | D4 | 45.3 | 中 | `tall_wall_chain` | **必搭** | 族代表 | F037 | 70 |
| 25 | `cargo_ship_01` | 集装箱货轮 | D4 | 45.1 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F069 | 70 |
| 26 | `ferry_terminal_01` | 轮渡码头 | D4 | 44.5 | 中 | `tall_wall_chain` | **必搭** | 上架抽样包+单模型族 (S3) | F095 | 70 |
| 27 | `hanging_garden_01` | 空中花园 | D4 | 43.9 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F105 | 70 |
| 28 | `train_station_01` | 中央火车站 | D4 | 43.9 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `steam_locomotive_01` 兜底 | F010 | 70 |
| 29 | `pet_clinic_01` | 宠物医院 | D4 | 43.8 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `fire_station_01` 兜底 | F009 | 70 |
| 30 | `stadium_gate_01` | 体育场大门 | D4 | 43.8 | 中 | `tall_wall_chain` | **必搭** | 上架抽样包 (S3) | F049 | 70 |
| 31 | `temple_greek_01` | 希腊神庙 | D4 | 43.6 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `triumphal_arch_01` 兜底 | F052 | 70 |
| 32 | `library_building_01` | 城市图书馆 | D4 | 42.8 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `helicopter_01` 兜底 | F037 | 70 |
| 33 | `apartment_block_01` | 居民楼 | D4 | 42.6 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F054 | 70 |
| 34 | `basketball_arena_01` | 篮球馆 | D4 | 42.5 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F062 | 70 |
| 35 | `post_office_01` | 邮局 | D4 | 42.5 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `fire_station_01` 兜底 | F009 | 70 |
| 36 | `school_bus_01` | 校车 | D4 | 42.5 | 中 | `tall_wall_chain` | **必搭** | 单模型族 | F150 | 70 |
| 37 | `race_track_01` | 环形赛道 | D4 | 40.7 | 中 | `tall_wall_chain` | 可缓建 | 同族代表 `aircraft_carrier_01` 兜底 | F012 | 70 |
| 38 | `treehouse_02` | 双树树上小屋 | D4 | 40.0 | 中 | — | **必搭** | 上架抽样包+单模型族 (S3) | F172 | 70 |
| 39 | `warehouse_01` | 物流仓库 | D4 | 40.0 | 中 | — | **必搭** | 单模型族 | F178 | 70 |
| 40 | `freight_yard_01` | 驼峰货运编组场 | D4 | 39.5 | 低 | — | 可缓建 | 同族代表 `steam_locomotive_01` 兜底 | F010 | 70 |
| 41 | `volcano_base_01` | 火山科考站 | D4 | 39.0 | 低 | — | **必搭** | 单模型族 | F177 | 70 |
| 42 | `ice_rink_01` | 滑冰场 | D4 | 38.9 | 低 | — | **必搭** | 单模型族 | F110 | 70 |
| 43 | `dinosaur_hall_01` | 恐龙化石挖掘展厅 | D4 | 38.3 | 低 | — | **必搭** | 单模型族 | F085 | 70 |
| 44 | `stonehenge_01` | 草原巨石阵 | D4 | 38.2 | 低 | — | **必搭** | 上架抽样包+单模型族 (S3) | F161 | 70 |
| 45 | `tennis_court_01` | 网球场 | D4 | 38.1 | 低 | — | **必搭** | 上架抽样包+单模型族 (S3) | F168 | 70 |
| 46 | `soccer_goal_01` | 足球门与球场 | D4 | 36.9 | 低 | — | **必搭** | 单模型族 | F158 | 70 |

## 3. 纪律 (缓建不是免检)

1. 本表只合并三份既有产物的口径, 排产采纳与否是策展/QA 的政策决定; 可缓建成员最终仍须实搭, 或由策展按族级抽检政策**书面**豁免 (依据与流程见 [PHYSICAL_FAMILY_PACK.md](PHYSICAL_FAMILY_PACK.md) 第 5 节);
2. 申请缓建的前提: 同族代表已实搭 **Pass** 且落盘 `content_meta.physical_verified` 三字段; 代表 Fail 则整族全员实搭;
3. 实搭动作与判定标准以 [PHYSICAL_REBUILD_CHECKLIST.md](../PHYSICAL_REBUILD_CHECKLIST.md) 为准, 备料/打印/落盘见 [PHYSICAL_REVIEW_USER_GUIDE.md](PHYSICAL_REVIEW_USER_GUIDE.md);
4. 本表是快照 —— 模型内容 (`final_assembly` / `steps`) 或复核状态变化后, 先重新生成风险报告再重新导出本队列。

