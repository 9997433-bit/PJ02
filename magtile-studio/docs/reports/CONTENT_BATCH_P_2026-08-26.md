# 批 P：扩展片型全覆盖选题 (10 个)

- 目标：补齐 13 种片型中「模型数/片次」明显偏少的画像，让用户勾选豪华/扩展套装后有对应玩法
- 难度：2×D1 + 6×D2 + 1×D3 + 1×D4，零 D3 新增
- 置换：入库 10 个 → 退役矩阵外 D3 候选 #17–#26（保持 250 上限）

| # | id | 主打片型 | D | 系列 | 招牌方向 |
|---|-----|---------|---|------|---------|
| P1 | `plaza_canopy_01` | large_square | D1 | practical_utility | 两片大正方形拼遮阳顶棚 + 四柱展台 |
| P2 | `conservatory_01` | window_square | D2 | plant_garden | 一排窗格方温室立面 + 梯形屋檐 |
| P3 | `hex_honeycomb_01` | hexagon | D2 | geometric_art | 六边环带蜂窝墙 + 平顶 |
| P4 | `rhombus_patchwork_01` | rhombus | D2 | geometric_art | 菱形密铺地毯立起成屏风 |
| P5 | `trapezoid_awning_01` | trapezoid | D2 | plant_garden | 梯形雨棚连廊 + 花台 |
| P6 | `marble_splitter_01` | door_frame | D2 | marble_run | 双轨分流门框方 + 坡道 |
| P7 | `streetcar_01` | wheel_base | D2 | land_transport | 有轨电车双轮底盘 + 车厢 |
| P8 | `switchback_ramp_01` | right_triangle | D2 | marble_run | 直角三角折返坡道塔 |
| P9 | `sector_rotunda_01` | sector | D3 | landmark_architecture | 扇形拱券围成半圆殿 |
| P10 | `expansion_orb_01` | 菱+梯+六+扇 | D4 | geometric_art | 四扩展片型合球近似摆件 |

片型覆盖缺口（入库前基线）：large_square 7 模型、sector 8、rhombus 18、hexagon 28、trapezoid 25。

## 附注: foundation 摘取入库时的规模返工 (2026-08-26)

按 `BATCH_P_MERGE_PLAN_2026-08-26.md` 的 cherry-pick 预案入 foundation 时,
全量 QA 的难度感知片数下限闸门 (`test_all_models.sh` / `test_anti_trivial.py`:
非 D1 下限 40 片, 形状 >= 3 种 —— 批 P 支分叉后 foundation 新增的口径)
拦下 4 个 D2, 已在 foundation 基线返工扩规模, 逐个 strict 零警告复验:

| id | 原规模 | 返工后 | 扩展内容 |
|----|-------|-------|---------|
| `hex_honeycomb_01` | 32 片/6 步 (2 种形状) | 44 片/8 步 (3 种) | 广场外圈 12 片方板 (3.4.6.4 半正密铺环带) |
| `rhombus_patchwork_01` | 39 片/10 步 (2 种形状) | 41 片/10 步 (3 种) | 步道口三角迎宾垫 x2 |
| `marble_splitter_01` | 30 片/8 步 | 40 片/10 步 | 穿廊地坪 x4 + 分流广场方板 x4 + 小旗 x2 |
| `trapezoid_awning_01` | 31 片/8 步 | 40 片/9 步 | 扇贝补花砖 x3 + 步道延伸 x2 + 绿篱/角花 x4 |

另: 退役名单按 merge plan 附录 B 在 foundation 基线重算 (原 #17–#25 已被
foundation 配额批抢先退役), 实际退役为重算后的前 10 矩阵外 D3;
`sector_rotunda_01` 的 technique_tags.secondary 以生成器为准
(T14_diagonal_bracing, 分支头检出的 JSON 带的 T17_negative_space
是重写中间版残留, 重写后设计已无负空间高窗)。
