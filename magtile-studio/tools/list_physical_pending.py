#!/usr/bin/env python3
"""列出 D4+ 且未通过实物搭建复核的模型清单 (QA 排产跟踪)。

背景: 软件 strict 全绿是入库必要条件, 不替代实物复核 —— difficulty >= 4
的模型必须按 docs/PHYSICAL_REBUILD_CHECKLIST.md 逐个实搭复核
(全库 strict 巡检报告第 5 节列出的 41 个 D4+ 模型即初始待复核清单)。

"已复核"判定口径 (满足任一):
  1. 模型 JSON `content_meta.physical_verified == true`
     (轻量摘要字段, 见 CONTENT_STRATEGY.md 5.1 节);
  2. 存在旁车文件 data/verification/<model_id>.json 且
     status == "physical_passed" 且 content_hash 与当前模型一致
     (权威记录, 见 BUILD_VERIFICATION.md 5.2 节; 哈希失配 = 模型被改过,
     旧结论作废, 仍计待复核)。

用法:
    tools/list_physical_pending.py [models_dir] [选项]
        models_dir            模型目录 (默认: 脚本同级仓库的 data/models)
        --verification-dir D  旁车验证记录目录 (默认: models_dir/../verification)
        --min-difficulty N    最低难度门槛 (默认 4, 即 D4+)
        --json                机器可读 JSON 输出
        --fail-on-pending     存在待复核模型时以退出码 1 结束 (发布门禁用);
                              默认仅报告不阻断 (run_full_qa.sh 关卡模式)

退出码: 0 = 报告完成 (默认) / 1 = --fail-on-pending 且存在待复核 / 2 = 数据错误
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def content_hash(model: dict) -> str:
    """与 BUILD_VERIFICATION.md 6 节门禁脚本一致的内容哈希。"""
    payload = json.dumps(
        {"final_assembly": model["final_assembly"], "steps": model["steps"]},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def classify(model: dict, ver_dir: Path):
    """返回 (verified: bool, via: str, warnings: [str])。"""
    warnings = []
    cm = model.get("content_meta") or {}

    if "physical_verified" in model:
        warnings.append("physical_verified 写在了顶层, 正确位置是 content_meta 下 (按未复核处理)")

    if cm.get("physical_verified") is True:
        if not cm.get("physical_verified_at"):
            warnings.append("physical_verified=true 但缺 physical_verified_at (复核日期必填)")
        via = "content_meta ({})".format(cm.get("physical_verified_at") or "日期缺失")
        return True, via, warnings

    sidecar = ver_dir / f"{model['id']}.json"
    if sidecar.is_file():
        try:
            ver = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            warnings.append(f"旁车文件 {sidecar} 无法解析: {exc}")
            return False, "", warnings
        if ver.get("status") == "physical_passed":
            if ver.get("content_hash") == content_hash(model):
                return True, f"旁车 {sidecar.name}", warnings
            warnings.append(f"旁车 {sidecar.name} 内容哈希失配 (模型已被修改), 实物结论作废需复验")
    return False, "", warnings


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="列出 D4+ 且未实物复核的模型清单")
    parser.add_argument("models_dir", nargs="?", default=str(root / "data" / "models"))
    parser.add_argument("--verification-dir", default=None)
    parser.add_argument("--min-difficulty", type=int, default=4)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-on-pending", action="store_true")
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    if not models_dir.is_dir():
        print(f"错误: 模型目录不存在: {models_dir}", file=sys.stderr)
        return 2
    ver_dir = Path(args.verification_dir) if args.verification_dir \
        else models_dir.parent / "verification"

    pending, verified, all_warnings = [], [], []
    total_scanned = 0
    for path in sorted(models_dir.glob("*.json")):
        try:
            model = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"错误: {path} 无法解析: {exc}", file=sys.stderr)
            return 2
        total_scanned += 1
        if int(model.get("difficulty", 0)) < args.min_difficulty:
            continue
        entry = {
            "id": model["id"],
            "difficulty": int(model["difficulty"]),
            "total_pieces": int(model.get("total_pieces", len(model.get("final_assembly", [])))),
            "steps": len(model.get("steps", [])),
        }
        ok, via, warnings = classify(model, ver_dir)
        for w in warnings:
            all_warnings.append(f"{model['id']}: {w}")
        if ok:
            entry["verified_via"] = via
            verified.append(entry)
        else:
            pending.append(entry)

    order = lambda e: (-e["difficulty"], e["id"])  # noqa: E731
    pending.sort(key=order)
    verified.sort(key=order)

    if args.as_json:
        print(json.dumps({
            "min_difficulty": args.min_difficulty,
            "models_scanned": total_scanned,
            "in_scope": len(pending) + len(verified),
            "pending_count": len(pending),
            "verified_count": len(verified),
            "pending": pending,
            "verified": verified,
            "warnings": all_warnings,
        }, ensure_ascii=False, indent=2))
    else:
        scope = f"D{args.min_difficulty}+"
        print(f"== 实物搭建复核跟踪 ({scope}, 规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==")
        print(f"扫描 {total_scanned} 个模型, {scope} 共 {len(pending) + len(verified)} 个: "
              f"已复核 {len(verified)}, 待复核 {len(pending)}")
        if pending:
            print(f"\n-- 待复核 ({len(pending)}) --")
            print(f"{'模型':<28} {'难度':<4} {'片数':>4} {'步骤':>4}")
            for e in pending:
                print(f"{e['id']:<28} D{e['difficulty']:<3} {e['total_pieces']:>4} {e['steps']:>4}")
        if verified:
            print(f"\n-- 已复核 ({len(verified)}) --")
            for e in verified:
                print(f"{e['id']:<28} D{e['difficulty']} via {e['verified_via']}")
        if all_warnings:
            print(f"\n-- 警告 ({len(all_warnings)}) --")
            for w in all_warnings:
                print(f"  [WARN] {w}")
        print(f"\n待复核数量: {len(pending)}"
              + (" (存在待复核, --fail-on-pending 生效)" if args.fail_on_pending and pending else ""))

    if args.fail_on_pending and pending:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
