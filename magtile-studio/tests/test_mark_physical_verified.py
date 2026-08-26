#!/usr/bin/env python3
# =============================================================
# MagTile Studio - 实物签核落盘工具 (tools/mark_physical_verified.py) 回归测试
#
# 路径 A 用户签核工具的行为锁: 用合成微模型 (临时目录, 不进库) +
# 桩校验器 (记录参数、按模型名决定退出码, 不依赖 C++ 构建产物) 验证
#
#   1. 成功路径: D4 模型 strict 通过 -> 三字段落进 content_meta
#      (紧跟 series 之后), 其余字段与 JSON 排版 (indent=2 + 收尾换行)
#      不被破坏, 桩校验器收到 validate + --profile strict 调用;
#   2. 防线逐条: 模型不存在 / 日期非法 / 未来日期 -> 退出码 2 且不写;
#      难度 < 4 -> 退出码 1 且不写; strict 校验失败 -> 退出码 1 且不写;
#   3. --dry-run: 检查全过退出码 0, 文件字节不变;
#   4. 幂等与笔记保留: 已标记模型可覆盖改日期; --notes 省略时保留
#      已有 physical_notes, 首次省略则不写该键。
#
# 用法: test_mark_physical_verified.py <repo_root>
# 退出码: 0 = 全部通过, 1 = 存在失败, 2 = 用法/环境错误
# =============================================================

import json
import os
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


def make_model(model_id, difficulty, content_meta=None):
    tiles = [{"id": f"t{i}", "type": "square",
              "position": [float(i), 0.0, 0.0],
              "rotation": [0, 0, 0], "color": "blue"} for i in range(4)]
    model = {
        "schema_version": 1,
        "id": model_id,
        "name": f"签核工具测试模型 {model_id}",
        "name_en": model_id,
        "description": "签核工具回归测试的合成微模型 (临时目录, 不进库)。",
        "difficulty": difficulty,
        "total_pieces": len(tiles),
        "tags": ["测试"],
        "final_assembly": tiles,
        "steps": [{"index": 1, "title": "一步到位", "tiles": tiles}],
    }
    if content_meta is not None:
        model["content_meta"] = content_meta
    return model


STUB_APP = """#!/usr/bin/env python3
# 桩校验器: 记录收到的参数; 模型路径含 strictfail 时退出码 1, 其余 0。
import sys
from pathlib import Path
log = Path(__file__).parent / "validate_calls.log"
with log.open("a", encoding="utf-8") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
sys.exit(1 if "strictfail" in sys.argv[2] else 0)
"""


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: test_mark_physical_verified.py <repo_root>", file=sys.stderr)
        return 2
    repo_root = Path(sys.argv[1]).resolve()
    tool = repo_root / "tools" / "mark_physical_verified.py"
    if not tool.is_file():
        print(f"错误: 工具不存在: {tool}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="mark_physical_") as tmp:
        tmp_path = Path(tmp)
        models_dir = tmp_path / "data" / "models"
        models_dir.mkdir(parents=True)

        app = tmp_path / "stub_magtile_app.py"
        app.write_text(STUB_APP, encoding="utf-8")
        app.chmod(0o755)
        call_log = tmp_path / "validate_calls.log"

        def dump(model):
            path = models_dir / f"{model['id']}.json"
            path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
            return path

        d4_path = dump(make_model(
            "tower_d4_01", 4,
            content_meta={"series": "castle_fortress",
                          "structural_signature": {"tile_histogram": {"square": 4}}}))
        d3_path = dump(make_model("hut_d3_01", 3))
        fail_path = dump(make_model("strictfail_d4_01", 4))

        def run(model_id, *extra):
            return subprocess.run(
                [sys.executable, str(tool), model_id,
                 "--models-dir", str(models_dir), "--app", str(app), *extra],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # -- 1. 防线: 模型不存在 -> 2 --
        proc = run("no_such_model_01", "--date", "2026-08-25")
        check(proc.returncode == 2, f"模型不存在退出码 2 (实际 {proc.returncode})")

        # -- 2. 防线: 日期非法 / 未来日期 -> 2, 文件不动 --
        before = d4_path.read_bytes()
        proc = run("tower_d4_01", "--date", "2026/08/25")
        check(proc.returncode == 2, f"非 ISO 日期退出码 2 (实际 {proc.returncode})")
        proc = run("tower_d4_01", "--date", "2999-01-01")
        check(proc.returncode == 2, f"未来日期退出码 2 (实际 {proc.returncode})")
        check(d4_path.read_bytes() == before, "日期被拒后模型文件字节不变")

        # -- 3. 防线: 难度 < 4 -> 1, 文件不动 --
        before_d3 = d3_path.read_bytes()
        proc = run("hut_d3_01", "--date", "2026-08-25")
        check(proc.returncode == 1, f"D3 模型被拒退出码 1 (实际 {proc.returncode})")
        check(d3_path.read_bytes() == before_d3, "D3 被拒后模型文件字节不变")

        # -- 4. 防线: strict 校验失败 -> 1, 文件不动 --
        before_fail = fail_path.read_bytes()
        proc = run("strictfail_d4_01", "--date", "2026-08-25")
        check(proc.returncode == 1,
              f"strict 校验失败被拒退出码 1 (实际 {proc.returncode})")
        check(fail_path.read_bytes() == before_fail, "strict 被拒后模型文件字节不变")

        # -- 5. --dry-run: 检查全过 -> 0, 文件不动 --
        proc = run("tower_d4_01", "--date", "2026-08-25", "--dry-run")
        check(proc.returncode == 0, f"dry-run 全过退出码 0 (实际 {proc.returncode})")
        check(d4_path.read_bytes() == before, "dry-run 后模型文件字节不变")

        # -- 6. 成功路径: 落盘三字段 + 排版/字段保真 + 校验器调用形态 --
        call_log.write_text("", encoding="utf-8")
        proc = run("tower_d4_01", "--date", "2026-08-25",
                   "--notes", "官方新片 62 分钟; 敲击/提起/拆解重搭全 Pass")
        check(proc.returncode == 0, f"成功落盘退出码 0 (实际 {proc.returncode})")
        raw = d4_path.read_text(encoding="utf-8")
        model = json.loads(raw)
        cm = model.get("content_meta") or {}
        check(cm.get("physical_verified") is True, "content_meta.physical_verified=true")
        check(cm.get("physical_verified_at") == "2026-08-25",
              "physical_verified_at 为传入日期")
        check(cm.get("physical_notes", "").startswith("官方新片"),
              "physical_notes 为传入笔记")
        check("physical_verified" not in model, "physical_verified 未写到顶层")
        keys = list(cm.keys())
        check(keys[:4] == ["series", "physical_verified", "physical_verified_at",
                           "physical_notes"],
              f"三字段紧跟 series 之后 (实际顺序 {keys})")
        check(cm.get("structural_signature") == {"tile_histogram": {"square": 4}},
              "content_meta 其余键保持不变")
        check(model["difficulty"] == 4 and len(model["final_assembly"]) == 4,
              "模型其余字段保持不变")
        check(raw == json.dumps(model, ensure_ascii=False, indent=2) + "\n",
              "JSON 排版保持 indent=2 + 收尾换行")
        calls = call_log.read_text(encoding="utf-8").strip().splitlines()
        check(len(calls) == 1 and calls[0].startswith("validate ")
              and "--profile strict" in calls[0],
              f"校验器按 validate --profile strict 调用 (实际 {calls})")

        # -- 7. 幂等覆盖: 改日期 + 省略 --notes 时保留已有笔记 --
        proc = run("tower_d4_01", "--date", "2026-08-26")
        check(proc.returncode == 0, f"已标记模型覆盖改日期退出码 0 (实际 {proc.returncode})")
        cm = json.loads(d4_path.read_text(encoding="utf-8"))["content_meta"]
        check(cm.get("physical_verified_at") == "2026-08-26", "覆盖后日期更新")
        check(cm.get("physical_notes", "").startswith("官方新片"),
              "--notes 省略时保留已有笔记")

        # -- 8. 首次省略 --notes: 不写 physical_notes 键 --
        d4b_path = dump(make_model("tower_d4_02", 4))
        proc = run("tower_d4_02", "--date", "2026-08-25")
        check(proc.returncode == 0, f"无笔记落盘退出码 0 (实际 {proc.returncode})")
        cm = json.loads(d4b_path.read_text(encoding="utf-8")).get("content_meta") or {}
        check(cm.get("physical_verified") is True
              and "physical_notes" not in cm,
              "首次省略 --notes 时不写 physical_notes 键")

    print()
    if FAILURES:
        print(f"共 {len(FAILURES)} 项失败:")
        for message in FAILURES:
            print(f"  - {message}")
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
