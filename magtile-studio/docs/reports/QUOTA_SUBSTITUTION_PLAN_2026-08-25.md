# 难度配额置换规划 (路径 B1)

- 基线: 主库 250 模型
- 解冻线: D1 >= 20 且 D5 >= 6
- 现状: D1=0 D2=23 D3=181 D4=45 D5=1
- 冻结: **是**
- 净换题需求: **至少 25 次** (D1 +20, D5 +5)

## 1. 分阶段演算

| 阶段 | 动作 | D1 | D5 | 冻结 |
| --- | --- | ---: | ---: | --- |
| 现状 | — | 0 | 1 | 是 |
| 批 J–M (16 置换) | 退役 16×D3 → 8×D1+4×D2+1×D4+3×D5 | 8 | 4 | 是 |
| 批 N+ (建议) | 再置换 14 次 (D1 +12, D5 +2) | 20 | 6 | 否 |

批 J–M 选题见 [CONTENT_GAP_AUDIT.md](../CONTENT_GAP_AUDIT.md) §8。

## 2. 退役候选序 (前 30, 非免费 D3)

排序规则: 矩阵外桶 > 矩阵内超编主题 > 其他; 同档按片数降序。
**不可退役**: 免费层 26 个 D3 (`FREE_TIER_MANIFEST.md`)。

| # | 模型 id | 归类 | 片数 | 备注 |
| ---: | --- | --- | ---: | --- |
| 1 | `corn_maze_01` | farm | 75 | 矩阵外 |
| 2 | `police_station_01` | city_life | 75 | 矩阵外 |
| 3 | `schoolyard_stand_01` | campus | 75 | 矩阵外 |
| 4 | `marching_band_01` | music | 74 | 矩阵外 |
| 5 | `pipe_organ_01` | music | 74 | 矩阵外 |
| 6 | `rice_terrace_01` | farm | 74 | 矩阵外 |
| 7 | `water_tower_01` | engineering_misc | 74 | 矩阵外 |
| 8 | `circus_tent_01` | amusement | 73 | 矩阵外 |
| 9 | `fountain_plaza_01` | city_life | 73 | 矩阵外 |
| 10 | `scaffolding_site_01` | engineering_misc | 73 | 矩阵外 |
| 11 | `particle_accelerator_01` | other | 72 | 矩阵外 |
| 12 | `conveyor_factory_01` | engineering_misc | 71 | 矩阵外 |
| 13 | `eye_clinic_01` | city_life | 71 | 矩阵外 |
| 14 | `drive_in_cinema_01` | city_life | 70 | 矩阵外 |
| 15 | `art_gallery_01` | museum | 69 | 矩阵外 |
| 16 | `farm_silo_01` | farm | 69 | 矩阵外 |
| 17 | `piano_stage_01` | music | 67 | 矩阵外 |
| 18 | `science_lab_01` | campus | 67 | 矩阵外 |
| 19 | `supermarket_01` | city_life | 67 | 矩阵外 |
| 20 | `jungle_gym_01` | campus | 65 | 矩阵外 |
| 21 | `recycling_center_01` | city_life | 65 | 矩阵外 |
| 22 | `water_slide_park_01` | other | 65 | 矩阵外 |
| 23 | `deep_sea_lab_01` | maritime_misc | 64 | 矩阵外 |
| 24 | `swimming_pool_01` | sports | 64 | 矩阵外 |
| 25 | `violin_shop_01` | music | 64 | 矩阵外 |
| 26 | `er_entrance_01` | city_life | 63 | 矩阵外 |
| 27 | `bamboo_house_01` | farm | 62 | 矩阵外 |
| 28 | `bike_rack_park_01` | city_life | 62 | 矩阵外 |
| 29 | `climbing_wall_01` | sports | 62 | 矩阵外 |
| 30 | `diving_tower_01` | sports | 62 | 矩阵外 |

## 3. 执行纪律 (置换模式)

1. 用户书面批准路径 B1 后启动;
2. 每批: `tools/retire_models.sh --dry-run <id>...` 预览 → `--execute` 退役
   (或 `--from-plan N` 取本报告候选序前 N 个), 再入库新批;
3. 入库前跑 `tools/review_content_batch.sh` 五关机检;
4. 全库保持 250 模型; `check_difficulty_quota.py --strict` 达标后 G2 红灯②自动转绿。

生成: `python3 tools/plan_quota_substitution.py --markdown 本文件`
