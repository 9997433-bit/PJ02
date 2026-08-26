#!/usr/bin/env python3
"""生成 R5~R8 物理规则的测试夹具 (tests/test_physics_negative|positive/)。

这些夹具是增强物理规则的回归测试, 对应真实搭建中最常见的
"照着图纸搭却掉下来" 的失败模式。目录与执行约定 (见 CMakeLists.txt):

  tests/test_physics_negative/<code>.json
      故意违反物理规则的模型, 由 tests/test_physics_negative.sh 执行:
      `magtile_app validate` 必须以非零退出码拒绝, 且输出必须包含
      文件名对应的错误码;
  tests/test_physics_positive/*.json
      处于承载预算之内的合法结构, validate 必须通过 (退出码 0),
      防止静力规则矫枉过正误杀磁力片的常规玩法。

本脚本生成的夹具一览 (R1~R4 的负例 floating_tile / overlapping_tiles /
unstable_cantilever 为手工维护, 不在此脚本范围内):

  1. hanging_chain_overload    悬挂链超重          R5 (Error)
  2. cantilever_overload       双片悬臂折落        R6 (Error)
                               ★ 该模型可通过旧版全部 4 条规则,
                                 是 "校验通过但实搭掉落" 的典型标本
  3. enclosed_placement        封闭腔体内补片      R7b (Error)
  4. unplaceable_order         步骤内顺序写反      R7a (Error, code=unplaceable_tile)
  5. single_cantilever_within_budget  单片外挑 (预算内, 必须通过)

坐标约定与 tools/generate_castle_model.py 一致:
  平铺片 rot = (0,0,0); 南北向立片 (平面 y=常数) rot = (90,0,0);
  东西向立片 (平面 x=常数) rot = (90,0,90)。

用法: python3 tools/generate_test_models.py  (在 magtile-studio 目录下运行)
"""

import json
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests"
NEGATIVE_DIR = TESTS_DIR / "test_physics_negative"
POSITIVE_DIR = TESTS_DIR / "test_physics_positive"

FLAT = (0, 0, 0)        # 平铺
WALL_NS = (90, 0, 0)    # 立片, 平面 y = 常数 (法向沿 y)
WALL_EW = (90, 0, 90)   # 立片, 平面 x = 常数 (法向沿 x)


def tile(tile_id, tile_type, pos, rot, color):
    return {
        "id": tile_id,
        "type": tile_type,
        "position": [round(v, 6) for v in pos],
        "rotation": [round(v, 6) for v in rot],
        "color": color,
    }


def step(number, description, tiles_to_add, tip=""):
    return {
        "step_number": number,
        "description": description,
        "tip": tip,
        "tiles_to_add": list(tiles_to_add),
        "highlight_tiles": [],
    }


def write(out_dir, file_name, model_id, name, description, tiles, steps):
    placed = [t for s in steps for t in s["tiles_to_add"]]
    assert len(placed) == len(tiles) == len(set(placed)), \
        f"{model_id}: 步骤必须恰好覆盖全部磁力片"
    model = {
        "schema_version": 1,
        "id": model_id,
        "name": name,
        "name_en": model_id,
        "description": description,
        "difficulty": 1,
        "total_pieces": len(tiles),
        "tags": ["测试夹具"],
        "final_assembly": tiles,
        "steps": steps,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / file_name
    out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已生成 {out} ({len(tiles)} 片, {len(steps)} 步)")


# ------------------------------------------------------------------
# 1. 悬挂链超重 (R5): 双塔吊桥, 桥面下挂 5 片正方形竖链 (约 150g),
#    全部悬挂在中间桥面板一条磁力边下方, 超过 120g 悬挂预算
#    (额定 150g/单位边长 x 0.8 抗碰撞裕量)。
#    实物对照: 磁力片吊链挂到第 5 片左右时, 最上面那条磁力边被整串拉脱。
#    对照组: 挂 4 片 (120g) 恰好在预算内, 不会触发。
# ------------------------------------------------------------------
def gen_hanging_chain_overload():
    tiles = []
    steps_list = []

    # 两座 6 片高的立柱塔 (平面 x=0 与 x=3), 底片直接立在桌面上
    for name, x, color in (("ta", 0.0, "blue"), ("tb", 3.0, "cyan")):
        for k in range(6):
            tiles.append(tile(f"{name}{k + 1}", "square", (x, 0.0, k + 0.5), WALL_EW, color))
    steps_list.append(step(1, "自下而上叠 6 片方片, 立起西侧塔柱 (平面 x=0)。",
                           [f"ta{k + 1}" for k in range(6)],
                           tip="每叠一片都要上下边完全贴合。"))
    steps_list.append(step(2, "同样方法立起东侧塔柱 (平面 x=3)。",
                           [f"tb{k + 1}" for k in range(6)]))

    # 顶部桥面: 3 片平铺方片连接双塔 (z=6)
    for i in range(3):
        tiles.append(tile(f"d{i + 1}", "square", (i + 0.5, 0.0, 6.0), FLAT, "orange"))
    steps_list.append(step(3, "在塔顶架设 3 片橙色桥面板, 两端分别吸在双塔顶边。",
                           ["d1", "d2", "d3"]))

    # 错误示范: 中间桥面板 (d2) 的 y=0.5 侧边下挂 5 片竖链 (约 150g)
    for k in range(5):
        tiles.append(tile(f"h{k + 1}", "square", (1.5, 0.5, 5.5 - k), WALL_NS, "red"))
    steps_list.append(step(4, "错误示范: 从中间桥面板边缘向下挂 5 片红色方片吊链。",
                           [f"h{k + 1}" for k in range(5)],
                           tip="整串约 150g 全部吊在一条磁力边上, 实物必掉 —— 校验器必须拒绝。"))

    write(NEGATIVE_DIR, "hanging_chain_overload.json",
          "fixture_hanging_chain_overload", "负例夹具: 悬挂链超重",
          "反面教材: 5 片正方形竖链 (约 150g) 悬挂在单条磁力边下方, 超过 120g 悬挂预算 "
          "(额定 150g/单位边长 x 80% 抗碰撞裕量)。现实中最上面那条磁力边会被整串拉脱。"
          "校验器必须报 hanging_chain_overload 错误并拒绝该模型。",
          tiles, steps_list)


# ------------------------------------------------------------------
# 2. 双片悬臂 (R6): 两片地板 + 两片立墙 (共 2 高) + 墙顶水平外挑 2 片。
#    ★ 地板同时充当配重, 整体重心仍在接地凸包内 —— 旧版 R1~R4 全部
#    通过, 但悬挑绕墙顶铰链产生 60g·单位 力矩, 远超 20g·单位 预算
#    (额定 25 x 0.8); 墙底铰链同样超限 (60 > 40)。
#    实物对照: 平挑第二片刚吸上, 整条悬臂就绕墙顶边向下翻折脱落。
# ------------------------------------------------------------------
def gen_cantilever_overload():
    tiles = [
        tile("g0", "square", (0.5, -0.5, 0.0), FLAT, "blue"),
        tile("g1", "square", (0.5, 0.5, 0.0), FLAT, "cyan"),
        tile("w1", "square", (0.5, 0.0, 0.5), WALL_NS, "red"),
        tile("w2", "square", (0.5, 0.0, 1.5), WALL_NS, "orange"),
        tile("c1", "square", (0.5, 0.5, 2.0), FLAT, "yellow"),
        tile("c2", "square", (0.5, 1.5, 2.0), FLAT, "purple"),
    ]
    steps = [
        step(1, "平放两片地板, 前后并排吸合。", ["g0", "g1"]),
        step(2, "在两片地板的公共边上立起第一层墙片。", ["w1"]),
        step(3, "在墙顶叠加第二层墙片。", ["w2"]),
        step(4, "错误示范: 从墙顶向水平方向连续外挑 2 片平板。", ["c1", "c2"],
             tip="重心没有出接地范围, 旧规则全绿; 但墙顶单边铰链撑不住 60g·单位的力矩, 实物必翻落。"),
    ]
    write(NEGATIVE_DIR, "cantilever_overload.json",
          "fixture_cantilever_overload", "负例夹具: 双片悬臂折落",
          "反面教材: 2 高墙顶水平外挑 2 片。整体重心仍在接地凸包内, 旧版 4 条规则全部通过, "
          "但悬臂绕墙顶铰链的重力力矩 (60g·单位) 远超单条磁力边的抗弯预算 (20g·单位), "
          "实物中悬臂会绕墙顶边向下翻折脱落。校验器必须报 cantilever_overload 错误并拒绝该模型。",
          tiles, steps)


# ------------------------------------------------------------------
# 3. 封闭腔体内补片 (R7b): 先搭好 2x1x1 全封闭盒子 (地板/四墙/顶盖),
#    最后一步才放盒子内部的竖直隔断 —— 13 个外部方向全被挡死,
#    手和磁力片都伸不进去。
#    注意: 该模型的最终成品完全合法; 只要把隔断挪到封顶之前放置即可
#    通过 —— 这正是 "装配顺序可行性" 与 "静态可行性" 的本质区别。
# ------------------------------------------------------------------
def gen_enclosed_placement():
    tiles = [
        tile("g1", "square", (0.5, 0.5, 0.0), FLAT, "blue"),
        tile("g2", "square", (1.5, 0.5, 0.0), FLAT, "cyan"),
        tile("f1", "square", (0.5, 0.0, 0.5), WALL_NS, "red"),
        tile("f2", "square", (1.5, 0.0, 0.5), WALL_NS, "red"),
        tile("b1", "square", (0.5, 1.0, 0.5), WALL_NS, "orange"),
        tile("b2", "square", (1.5, 1.0, 0.5), WALL_NS, "orange"),
        tile("l1", "square", (0.0, 0.5, 0.5), WALL_EW, "green"),
        tile("r1", "square", (2.0, 0.5, 0.5), WALL_EW, "green"),
        tile("t1", "square", (0.5, 0.5, 1.0), FLAT, "yellow"),
        tile("t2", "square", (1.5, 0.5, 1.0), FLAT, "yellow"),
        tile("dv", "square", (1.0, 0.5, 0.5), WALL_EW, "purple"),
    ]
    steps = [
        step(1, "平铺 2 片地板。", ["g1", "g2"]),
        step(2, "沿地板四周立起 6 片围墙, 组成 2x1 的盒身。",
             ["f1", "f2", "b1", "b2", "l1", "r1"]),
        step(3, "盖上 2 片顶盖, 盒子完全封闭。", ["t1", "t2"]),
        step(4, "错误示范: 在已封闭的盒子内部插入紫色隔断。", ["dv"],
             tip="隔断的吸附位全部在盒子内部, 封顶之后手已经伸不进去 —— 应把本步挪到封顶之前。"),
    ]
    write(NEGATIVE_DIR, "enclosed_placement.json",
          "fixture_enclosed_placement", "负例夹具: 封闭腔体内补片",
          "反面教材: 全封闭盒子完成后才放内部隔断, 放置点从任何外部方向都不可达, 实搭时手"
          "无法伸入。成品本身合法, 把隔断挪到封顶之前即可通过 —— 校验器必须报 "
          "enclosed_placement 错误并拒绝当前步骤顺序。",
          tiles, steps)


# ------------------------------------------------------------------
# 4. 步骤内顺序写反 (R7a): 同一步骤先列出第二层墙片、后列出第一层墙片。
#    按列表顺序放置时, 第二层墙片放下的那一刻下方还没有依托。
#    注意: 每个 "步骤完成后" 的整体状态都合法 (旧版逐步校验发现不了),
#    只有精确到步骤内逐片顺序的模拟才能暴露此问题。
# ------------------------------------------------------------------
def gen_unplaceable_order():
    tiles = [
        tile("g1", "square", (0.5, 0.5, 0.0), FLAT, "blue"),
        tile("w1", "square", (0.5, 0.0, 0.5), WALL_NS, "red"),
        tile("w2", "square", (0.5, 0.0, 1.5), WALL_NS, "orange"),
    ]
    steps = [
        step(1, "平放一片地板。", ["g1"]),
        step(2, "错误示范: 教程把第二层墙片写在第一层前面。", ["w2", "w1"],
             tip="w2 放下的那一刻 w1 还不存在, 半空中无处吸附 —— 调换 tiles_to_add 顺序即可通过。"),
    ]
    write(NEGATIVE_DIR, "unplaceable_order.json",
          "fixture_unplaceable_order", "负例夹具: 步骤顺序写反",
          "反面教材: 步骤内 tiles_to_add 顺序颠倒, 上层片先于下层片放置, 放置瞬间既不接地"
          "也吸不到任何已放置磁力片, 松手即掉。校验器必须报 unplaceable_tile 错误并拒绝该教程。",
          tiles, steps)


# ------------------------------------------------------------------
# 5. 单片外挑 (预算内, 必须通过): 两片地板 + 1 高墙 + 墙顶外挑 1 片。
#    力矩 30g x 0.5 = 15g·单位, 在 20g·单位 预算之内 (额定 25 x 0.8);
#    墙底铰链跨 2 条磁力边, 预算 40g·单位, 同样满足。
#    实物对照: 单片平挑在墙顶是磁力片的常规玩法, 确实立得住 ——
#    校验器不能矫枉过正把合法结构也拒绝。
# ------------------------------------------------------------------
def gen_single_cantilever_within_budget():
    tiles = [
        tile("g0", "square", (0.5, -0.5, 0.0), FLAT, "blue"),
        tile("g1", "square", (0.5, 0.5, 0.0), FLAT, "cyan"),
        tile("w1", "square", (0.5, 0.0, 0.5), WALL_NS, "red"),
        tile("c1", "square", (0.5, 0.5, 1.0), FLAT, "yellow"),
    ]
    steps = [
        step(1, "平放两片地板, 前后并排吸合。", ["g0", "g1"]),
        step(2, "在两片地板的公共边上立起一片墙。", ["w1"]),
        step(3, "从墙顶水平外挑 1 片平板 (在承载预算之内)。", ["c1"],
             tip="单片外挑力矩 15g·单位 < 预算 20g·单位, 实物立得住, 校验应当放行。"),
    ]
    write(POSITIVE_DIR, "single_cantilever_within_budget.json",
          "fixture_single_cantilever_within_budget", "正例夹具: 单片外挑",
          "正面对照组: 墙顶外挑单片, 力矩在铰链抗弯预算之内, 且墙底铰链跨两条磁力边。"
          "全部物理规则必须通过, 防止 R5/R6 静力规则矫枉过正误杀磁力片的常规玩法。",
          tiles, steps)


if __name__ == "__main__":
    gen_hanging_chain_overload()
    gen_cantilever_overload()
    gen_enclosed_placement()
    gen_unplaceable_order()
    gen_single_cantilever_within_budget()
