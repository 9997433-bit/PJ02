#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 实物风险巡检工具 (tools/physical_risk_report.py) 回归测试
#
# BUILD_VERIFICATION.md 2.1 节接口约定的第 1 件套 (L2 标记判定 /
# 风险报告) 的行为锁: 用一组合成微模型 (临时目录, 不进库) 验证
#
#   1. --json 机器可读输出可解析, 每模型条目含 id 与 L2 标记数组
#      (字段名兼容约定口径 model_id/flags/flagged 与工具现行口径
#      id/l2_flags/l2_requirement, 以免两侧措辞收敛期间互相卡脖子);
#   2. 触发条件检出: 平铺低风险模型零标记; 连续 3 片垂直墙链命中
#      条件 2 (C2 / tall_wall_chain); content_meta.l2_manual_flag
#      命中条件 5 (C5 / manual_flag), 且被标记模型的综合结论为真;
#   3. 风险分排序信号: 墙链高风险模型分高于平铺模型 (若工具输出
#      risk_score 字段);
#   4. 报告型退出码: 人读/机读模式对合法输入恒 0 (门禁语义另有
#      旗标, 不在报告模式里偷偷升级); 模型目录不存在必须非零拒绝。
#
# 全程 --no-validate (跳过 L1 校验器实跑): 本测试锁的是标记判定与
# 报告契约, 不依赖 C++ 构建产物, 秒级完成。
#
# 用法: test_physical_risk_report.py <repo_root>
# 退出码: 0 = 全部通过, 1 = 存在失败, 2 = 用法/环境错误
# =============================================================

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FAILURES = []


def check(ok, message):
    tag = "[通过]" if ok else "[失败]"
    print(f"{tag} {message}")
    if not ok:
        FAILURES.append(message)


def get_id(entry):
    """条目 id: 约定口径 model_id 与工具现行口径 id 均接受。"""
    return entry.get("model_id", entry.get("id"))


def get_flags(entry):
    """L2 标记数组: 约定口径 flags 与工具现行口径 l2_flags 均接受。"""
    flags = entry.get("flags", entry.get("l2_flags"))
    return [str(f) for f in flags] if isinstance(flags, list) else None


def is_flagged(entry):
    """综合结论: flagged / l2_required 布尔字段优先, 否则由标记数组推断。"""
    for key in ("flagged", "l2_required"):
        if isinstance(entry.get(key), bool):
            return entry[key]
    flags = get_flags(entry)
    return bool(flags)


def flat_tile(tile_id, x, y, color):
    return {"id": tile_id, "type": "square", "position": [x, y, 0.0],
            "rotation": [0, 0, 0], "color": color}


def wall_tile(tile_id, z, color):
    return {"id": tile_id, "type": "square", "position": [0.5, 0.0, z],
            "rotation": [90, 0, 0], "color": color}


def make_model(model_id, name, tiles, difficulty=1, content_meta=None):
    model = {
        "schema_version": 1,
        "id": model_id,
        "name": name,
        "name_en": model_id,
        "description": "风险巡检回归测试的合成微模型 (临时目录, 不进库)。",
        "difficulty": difficulty,
        "total_pieces": len(tiles),
        "tags": ["测试夹具"],
        "final_assembly": tiles,
        "steps": [{
            "step_number": 1,
            "description": "按清单放好全部磁力片。",
            "tip": "",
            "tiles_to_add": [t["id"] for t in tiles],
            "highlight_tiles": [],
        }],
    }
    if content_meta is not None:
        model["content_meta"] = content_meta
    return model


def build_models_dir(repo_root: Path, workdir: Path) -> Path:
    """临时数据目录: models/ 三个合成模型 + 复制真实 tile_catalog.json
    (扩展片型 tier 判定的单一来源, 缺失时工具虽有兜底集合, 但测试
    应当走真实目录路径)。"""
    models_dir = workdir / "models"
    models_dir.mkdir(parents=True)
    shutil.copy(repo_root / "data" / "tile_catalog.json",
                workdir / "tile_catalog.json")

    plates = [flat_tile("g0", 0.5, -0.5, "blue"), flat_tile("g1", 0.5, 0.5, "cyan"),
              flat_tile("g2", 1.5, -0.5, "cyan"), flat_tile("g3", 1.5, 0.5, "blue")]
    walls = [flat_tile("g0", 0.5, -0.5, "blue"), flat_tile("g1", 0.5, 0.5, "cyan"),
             wall_tile("w1", 0.5, "red"), wall_tile("w2", 1.5, "yellow"),
             wall_tile("w3", 2.5, "green")]

    cases = [
        make_model("rr_flat_low_risk", "平铺低风险", plates),
        make_model("rr_tall_wall_chain", "三连垂直墙链", walls, difficulty=2),
        make_model("rr_manual_flag", "手动标记", plates,
                   content_meta={"l2_manual_flag": True}),
    ]
    for model in cases:
        (models_dir / f"{model['id']}.json").write_text(
            json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return models_dir


def run_tool(tool: Path, *args):
    return subprocess.run([sys.executable, str(tool), *args],
                          capture_output=True, text=True)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"用法: {sys.argv[0]} <repo_root>", file=sys.stderr)
        return 2
    repo_root = Path(sys.argv[1]).resolve()
    tool = repo_root / "tools" / "physical_risk_report.py"
    if not tool.is_file():
        print(f"错误: 风险巡检工具不存在: {tool} (CMake 应在工具入库后才注册本测试)",
              file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="magtile_risk_report_") as tmp:
        workdir = Path(tmp)
        models_dir = build_models_dir(repo_root, workdir)
        ver_dir = workdir / "verification"  # 不存在: 全部按未复核处理

        # ---- 1. --json 机读输出: 报告型退出码 0 + 契约字段 ----------
        proc = run_tool(tool, str(models_dir), "--no-validate", "--json",
                        "--verification-dir", str(ver_dir), "--top", "2")
        check(proc.returncode == 0,
              f"--json 报告模式退出码为 0 (实际: {proc.returncode})")
        payload = None
        try:
            payload = json.loads(proc.stdout)
            check(True, "--json 输出可被 json.loads 解析")
        except ValueError as exc:
            check(False, f"--json 输出不是合法 JSON: {exc}")

        if payload is not None:
            entries = payload.get("models")
            check(isinstance(entries, list) and len(entries) == 3,
                  "models 数组包含全部 3 个合成模型")
            by_id = {}
            if isinstance(entries, list):
                for entry in entries:
                    mid = get_id(entry)
                    check(mid is not None, "每个条目都有 id (model_id/id)")
                    check(get_flags(entry) is not None,
                          f"条目 {mid} 有 L2 标记数组 (flags/l2_flags)")
                    by_id[mid] = entry

            flat = by_id.get("rr_flat_low_risk")
            tall = by_id.get("rr_tall_wall_chain")
            manual = by_id.get("rr_manual_flag")
            check(flat is not None and tall is not None and manual is not None,
                  "三个合成模型的条目都按 id 找得到")

            # ---- 2. 触发条件检出 ------------------------------------
            if flat is not None:
                check(get_flags(flat) == [] and not is_flagged(flat),
                      f"平铺低风险模型零 L2 标记 (实际: {get_flags(flat)})")
            if tall is not None:
                tall_flags = get_flags(tall) or []
                check(any("C2" in f or "tall" in f or "chain" in f
                          for f in tall_flags),
                      f"三连垂直墙链命中条件 2 (C2/tall_wall_chain, 实际: {tall_flags})")
                check(is_flagged(tall), "墙链模型的 L2 综合结论为已标记")
            if manual is not None:
                manual_flags = get_flags(manual) or []
                check(any("C5" in f or "manual" in f for f in manual_flags),
                      f"content_meta.l2_manual_flag 命中条件 5 (C5/manual_flag, 实际: {manual_flags})")
                check(is_flagged(manual), "手动标记模型的 L2 综合结论为已标记")

            # ---- 3. 风险分排序信号 (字段存在时才断言) ----------------
            if (flat is not None and tall is not None
                    and isinstance(flat.get("risk_score"), (int, float))
                    and isinstance(tall.get("risk_score"), (int, float))):
                check(tall["risk_score"] > flat["risk_score"],
                      f"墙链模型风险分高于平铺模型 "
                      f"({tall['risk_score']} > {flat['risk_score']})")

        # ---- 4. 人读报告模式: 同样恒 0 -------------------------------
        proc = run_tool(tool, str(models_dir), "--no-validate",
                        "--verification-dir", str(ver_dir))
        check(proc.returncode == 0 and proc.stdout.strip() != "",
              f"人读报告模式退出码 0 且有输出 (实际: {proc.returncode})")

        # ---- 5. 数据错误必须非零拒绝 ---------------------------------
        proc = run_tool(tool, str(workdir / "no_such_models_dir"), "--no-validate")
        check(proc.returncode != 0,
              f"模型目录不存在时以非零退出码拒绝 (实际: {proc.returncode})")

    print()
    if FAILURES:
        print(f"[失败] 风险巡检工具回归存在 {len(FAILURES)} 处失败")
        return 1
    print("[通过] 风险巡检工具回归全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
