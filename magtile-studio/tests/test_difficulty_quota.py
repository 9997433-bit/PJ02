#!/usr/bin/env python3
# =============================================================
# MagTile Studio - D3 冻结硬闸门 (tools/check_difficulty_quota.py) 回归测试
#
# CONTENT_GAP_AUDIT.md 7.3 节机制建议第 2 条的行为锁: 用合成微模型
# (临时目录, 不进库) 验证
#
#   1. 默认报告模式: 冻结与否均退出 0 (只报告不拦截);
#   2. --strict: 冻结生效 (D1<20 或 D5<6) 退出 1, 解冻后退出 0;
#   3. --batch 目录模式: 冻结期间批次含 D3 新模型退出 1,
#      白名单 (--whitelist-file) 豁免后退出 0;
#   4. --batch id 清单模式: 已入库 D3 模型同样被拦截;
#   5. 解冻后 (D1>=20 且 D5>=6) 批次 D3 放行退出 0;
#   6. 结构错误: 批次 id 无法解析退出 2。
#
# 用法: test_difficulty_quota.py <repo_root>
# 退出码: 0 = 全部通过, 1 = 存在失败, 2 = 用法/环境错误
# =============================================================

import json
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


def write_model(directory, model_id, difficulty):
    (directory / f"{model_id}.json").write_text(json.dumps({
        "schema_version": 1,
        "id": model_id,
        "name": model_id,
        "difficulty": difficulty,
        "final_assembly": [],
        "steps": [],
    }), encoding="utf-8")


def make_library(root, d1, d5, extra_d3=1):
    """构造合成主库: 指定数量的 D1/D5, 外加若干 D3 底噪。"""
    lib = root / "models"
    lib.mkdir(parents=True)
    for i in range(d1):
        write_model(lib, f"easy_{i:02d}", 1)
    for i in range(d5):
        write_model(lib, f"master_{i:02d}", 5)
    for i in range(extra_d3):
        write_model(lib, f"skilled_{i:02d}", 3)
    return lib


def run_tool(tool, *args):
    return subprocess.run([sys.executable, str(tool), *args],
                          capture_output=True, text=True)


def main(argv):
    if len(argv) != 2:
        print("用法: test_difficulty_quota.py <repo_root>", file=sys.stderr)
        return 2
    tool = Path(argv[1]) / "tools" / "check_difficulty_quota.py"
    if not tool.is_file():
        print(f"错误: 找不到 {tool}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="mt_quota_") as tmp:
        tmp = Path(tmp)

        # 冻结库 (D1=0, D5=1) 与解冻库 (D1=20, D5=6)
        frozen_lib = make_library(tmp / "frozen", d1=0, d5=1)
        open_lib = make_library(tmp / "open", d1=20, d5=6)

        # 批次目录: 一个 D3 + 一个 D2
        batch_dir = tmp / "batch"
        batch_dir.mkdir()
        write_model(batch_dir, "new_d3_model", 3)
        write_model(batch_dir, "new_d2_model", 2)

        # 1. 默认报告模式恒 0
        r = run_tool(tool, str(frozen_lib))
        check(r.returncode == 0, f"默认报告模式 (冻结库) 退出 0, 实际 {r.returncode}")
        check("生效中" in r.stdout, "冻结库报告标注 D3 冻结生效中")

        # 2. --strict: 冻结退出 1, 解冻退出 0
        r = run_tool(tool, str(frozen_lib), "--strict")
        check(r.returncode == 1, f"--strict (冻结库) 退出 1, 实际 {r.returncode}")
        r = run_tool(tool, str(open_lib), "--strict")
        check(r.returncode == 0, f"--strict (解冻库) 退出 0, 实际 {r.returncode}")
        check("已解冻" in r.stdout, "解冻库报告标注已解冻")

        # 3. 批次目录模式: 冻结期间 D3 被拦截, 白名单豁免
        r = run_tool(tool, str(frozen_lib), "--batch", str(batch_dir))
        check(r.returncode == 1, f"冻结期批次含 D3 退出 1, 实际 {r.returncode}")
        check("new_d3_model" in r.stdout, "违规名单点名 new_d3_model")

        wl = tmp / "whitelist.txt"
        wl.write_text("# 策展人签发\nnew_d3_model\n", encoding="utf-8")
        r = run_tool(tool, str(frozen_lib), "--batch", str(batch_dir),
                     "--whitelist-file", str(wl))
        check(r.returncode == 0, f"白名单豁免后退出 0, 实际 {r.returncode}")

        # 4. id 清单模式: 已入库 D3 模型同样被拦截
        id_list = tmp / "batch_ids.txt"
        id_list.write_text("# 批次复核\nskilled_00\n", encoding="utf-8")
        r = run_tool(tool, str(frozen_lib), "--batch", str(id_list))
        check(r.returncode == 1, f"id 清单含在库 D3 退出 1, 实际 {r.returncode}")

        # 5. 解冻后批次 D3 放行
        r = run_tool(tool, str(open_lib), "--batch", str(batch_dir))
        check(r.returncode == 0, f"解冻后批次 D3 放行退出 0, 实际 {r.returncode}")

        # 6. 结构错误: 批次 id 无法解析
        bad_list = tmp / "bad_ids.txt"
        bad_list.write_text("no_such_model\n", encoding="utf-8")
        r = run_tool(tool, str(frozen_lib), "--batch", str(bad_list))
        check(r.returncode == 2, f"批次 id 无法解析退出 2, 实际 {r.returncode}")

    print("=" * 62)
    if FAILURES:
        print(f"结果: {len(FAILURES)} 项失败")
        return 1
    print("结果: D3 冻结硬闸门回归测试全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
