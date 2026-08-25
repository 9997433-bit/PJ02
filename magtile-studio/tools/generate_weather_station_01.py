#!/usr/bin/env python3
"""生成模型 data/models/weather_station_01.json (山地气象观测站)。

内容批 B 1/5: 全库第一座气象观测站 —— 与机场塔台 (单一高塔) 和
天文台 (穹顶鼓身) 刻意错开: 本作没有"一栋主楼", 主角是观测坪上
的"三件观测仪器", 每件一种专属结构 —— 测风塔 (两层墙环 + 瘦高
风杆直上 4.0 + 风向旗), 百叶箱 (下层清色支架墙环架空, 上层整圈
窗格方就是百叶), 雨量筒 (开顶墙环只围不盖, 雨水直接落进蓝色
底格); 东南角光伏板 30 度朝天为仪器供电, 数据屏窗格方立在坪缝
上 —— 全库唯一的"仪器三件套"科学场景。

结构总览 (世界单位: 1.0 = 正方形磁力片边长):
  - 观测坪 (x [0,5], y [0,4]): 单位方板 x20 (雨量筒底格为蓝)   20 片
  - 测风塔 (x [0,1], y [0,1]): 两层墙环 x8 + 压顶 + 风杆 + 旗   11 片
  - 百叶箱 (x [2,3], y [2,3]): 支架墙环 x4 + 窗格方百叶环 x4 +
    压顶                                                          9 片
  - 雨量筒 (x [4,5], y [1,2]): 开顶墙环                          4 片
  - 光伏板 (x [3,4], y=4 北沿): 支撑墙 + 30 度斜板               2 片
  - 数据屏 (x [2,3], y=1 坪缝): 窗格方立牌                       1 片
  合计 47 片, 10 个教程步骤, 5 种磁力片形状 (全部 CORE-9 之内)。

物理规则要点 (validate 常规 + strict 双档零警告):
  - 测风塔层层墙环四角竖边互咬闭环, 上层墙底边整边吸下层墙顶,
    R8 高层检查由闭环拓扑天然通过; 风杆底边"压顶北沿 + 塔北墙顶"
    一线双吸, 风向旗骑压顶东沿, 重心正压铰链线力矩为零;
  - 百叶箱下层清色墙环是"支架", 上层窗格方环是"百叶", 语义即
    结构; 雨量筒开顶墙环只围不盖, 四角竖边互咬照样闭合;
  - 光伏板顶边整边吸支撑墙顶, 坡尾自己落地生根 (顶铰链 + 接地
    双路径, 梯田田埂坡道同款受力);
  - 全部墙脚踩观测坪拼缝整边吸合, 数据屏底边吸坪缝零力矩。

用法: python3 tools/generate_weather_station_01.py  (在 magtile-studio 目录下运行)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magtile_gen import ModelBuilder  # noqa: E402

b = ModelBuilder()

PAD = "gray"        # 观测坪
GRASS = "green"     # 坪边草地
RAIN = "blue"       # 雨量筒底格 (接住的雨水)
TOWER = "gray"      # 测风塔
CAP = "clear"       # 塔顶压顶
MAST = "clear"      # 风杆
VANE = "red"        # 风向旗
LEG = "clear"       # 百叶箱支架层
LOUVER = "clear"    # 百叶 (窗格方)
BOX_CAP = "cyan"    # 百叶箱压顶
GAUGE = "cyan"      # 雨量筒
PANEL = "blue"      # 光伏板
STAND = "gray"      # 光伏支撑墙
SCREEN = "cyan"     # 数据屏


def wall_ns_t(tid, tile_type, x0, y, z0, color):
    b.add(tid, tile_type, (x0 + 0.5, y, z0 + 0.5), (90, 0, 0), color)


def wall_ew_t(tid, tile_type, x, y0, z0, color):
    b.add(tid, tile_type, (x, y0 + 0.5, z0 + 0.5), (90, 0, 90), color)


# =================================================================
# 1. 观测坪 (x [0,5], y [0,4]): 20 片单位方板, 雨量筒底格为蓝
# =================================================================
for y0 in range(4):
    for x0 in range(5):
        if (x0, y0) == (4, 1):
            color = RAIN                       # 雨量筒底格
        elif (x0 + y0) % 2 == 0:
            color = PAD
        else:
            color = GRASS
        b.flat(f"pad_{x0}_{y0}", x0, y0, 0.0, color)

# =================================================================
# 2. 测风塔 (x [0,1], y [0,1]): 两层墙环 + 压顶 + 风杆 + 风向旗
# =================================================================
for lvl in range(2):
    b.wall_ns(f"tw{lvl}_s", 0, 0.0, lvl, TOWER)
    b.wall_ns(f"tw{lvl}_n", 0, 1.0, lvl, TOWER)
    b.wall_ew(f"tw{lvl}_w", 0.0, 0, lvl, TOWER)
    b.wall_ew(f"tw{lvl}_e", 1.0, 0, lvl, TOWER)
b.flat("tw_cap", 0, 0, 2.0, CAP)
b.spire_ns("tw_mast", 0, 1.0, 2.0, MAST)       # 风杆直上 4.0
b.crest_ew("tw_vane", 1.0, 0, 2.0, VANE)       # 风向旗骑压顶东沿

# =================================================================
# 3. 百叶箱 (x [2,3], y [2,3]): 支架层 + 窗格方百叶环 + 压顶
# =================================================================
b.wall_ns("sc_leg_s", 2, 2.0, 0, LEG)
b.wall_ns("sc_leg_n", 2, 3.0, 0, LEG)
b.wall_ew("sc_leg_w", 2.0, 2, 0, LEG)
b.wall_ew("sc_leg_e", 3.0, 2, 0, LEG)
wall_ns_t("sc_lv_s", "window_square", 2, 2.0, 1, LOUVER)
wall_ns_t("sc_lv_n", "window_square", 2, 3.0, 1, LOUVER)
wall_ew_t("sc_lv_w", "window_square", 2.0, 2, 1, LOUVER)
wall_ew_t("sc_lv_e", "window_square", 3.0, 2, 1, LOUVER)
b.flat("sc_cap", 2, 2, 2.0, BOX_CAP)

# =================================================================
# 4. 雨量筒 (x [4,5], y [1,2]): 开顶墙环, 只围不盖
# =================================================================
b.wall_ns("rg_s", 4, 1.0, 0, GAUGE)
b.wall_ns("rg_n", 4, 2.0, 0, GAUGE)
b.wall_ew("rg_w", 4.0, 1, 0, GAUGE)
b.wall_ew("rg_e", 5.0, 1, 0, GAUGE)

# =================================================================
# 5. 光伏板 (北沿) + 数据屏 (坪缝)
# =================================================================
b.wall_ns("pv_stand", 3, 4.0, 0, STAND)
b.ramp("pv_panel", "+y", 4.0, 3, 1.0, PANEL)   # 顶边吸墙顶, 坡尾落地
wall_ns_t("data_screen", "window_square", 2, 1.0, 0, SCREEN)

# =================================================================
# 教程步骤 (10 步)
# =================================================================
b.step(
    "铺观测坪南两行: 灰绿相间的单位方板行行等边互吸。",
    [f"pad_{x0}_{y0}" for y0 in range(2) for x0 in range(5)],
    tip="蓝色那格要放在东边第二行 —— 它是雨量筒的接水底格。",
)
b.step(
    "铺观测坪北两行: 再来十片, 整片场坪连成一张网。",
    [f"pad_{x0}_{y0}" for y0 in range(2, 4) for x0 in range(5)],
    highlight=["pad_0_0"],
    tip="所有仪器都要踩坪上的拼缝, 每一道缝都是一条磁力吸边。",
)
b.step(
    "立测风塔第一层: 四片灰墙合环, 四角竖边互咬。",
    ["tw0_s", "tw0_n", "tw0_w", "tw0_e"],
    highlight=["pad_0_0"],
    tip="墙脚整边吸住坪缝, 闭环墙筒是最稳的塔身。",
)
b.step(
    "测风塔第二层墙环整边骑上第一层墙顶。",
    ["tw1_s", "tw1_n", "tw1_w", "tw1_e"],
    highlight=["tw0_s"],
    tip="上层每片墙底边都要与下层墙顶整边对齐再松手。",
)
b.step(
    "塔顶压顶四边全吸, 风杆与风向旗骑上塔顶。",
    ["tw_cap", "tw_mast", "tw_vane"],
    highlight=["tw1_n"],
    tip="风杆底边同时吸住压顶北沿和北墙顶 —— 一条线上两道保险, "
        "杆尖直上 4.0。",
)
b.step(
    "搭百叶箱支架层: 四片清色墙把箱体架离地面。",
    ["sc_leg_s", "sc_leg_n", "sc_leg_w", "sc_leg_e"],
    highlight=["pad_2_2"],
    tip="百叶箱要离地通风, 温度计才量得准。",
)
b.step(
    "百叶层上箱: 整圈窗格方骑上支架墙顶, 再盖青色压顶。",
    ["sc_lv_s", "sc_lv_n", "sc_lv_w", "sc_lv_e", "sc_cap"],
    highlight=["sc_leg_s"],
    tip="窗格方的镂空就是百叶 —— 风穿箱而过, 太阳晒不进去。",
)
b.step(
    "围雨量筒: 四片青色墙开顶合环, 蓝色底格在筒心。",
    ["rg_s", "rg_n", "rg_w", "rg_e"],
    highlight=["pad_4_1"],
    tip="只围不盖, 雨水才落得进来; 四角竖边互咬照样闭环。",
)
b.step(
    "立数据屏: 窗格方立牌插在坪缝上, 面向观测坪。",
    ["data_screen"],
    highlight=["sc_lv_s"],
    tip="今天的风速、气温、雨量, 都会显示在这块屏上。",
)
b.step(
    "装光伏板收尾: 支撑墙立在北沿, 斜板顶边吸墙顶、坡尾落地。",
    ["pv_stand", "pv_panel"],
    highlight=["data_screen"],
    tip="30 度朝天正对太阳 —— 观测站开始记录今天的天气!",
)

b.finalize(
    model_id="weather_station_01",
    name="山地气象观测站",
    name_en="Weather Station 01",
    description=(
        "只用核心九片型的气象观测场景: 没有一栋主楼, 主角是观测坪上"
        "的三件仪器 —— 测风塔两层墙环层层闭环, 清色风杆一线双吸直上"
        " 4.0, 红色风向旗骑沿零力矩; 百叶箱下层清色支架墙环架空, "
        "上层整圈窗格方就是百叶, 风穿箱而过; 雨量筒开顶墙环只围"
        "不盖, 雨水直接落进蓝色底格。东南角光伏板顶边吸墙顶、坡尾"
        "落地生根, 青色数据屏立在坪缝上 —— 今天的风从哪边来?"
    ),
    difficulty=2,
    tags=["自然", "科学", "气象", "观测站"],
    min_pieces=47,
    min_steps=10,
)
