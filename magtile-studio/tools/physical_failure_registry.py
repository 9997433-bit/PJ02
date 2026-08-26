#!/usr/bin/env python3
"""实物失效登记账本 (Physical Failure Registry)。

背景: L3 实物复核发现的每一次真实失效 (掉片/坍塌/翻折), 都是软件规则
最贵的校准数据 —— BUILD_VERIFICATION.md 第 4 节要求"每次 L3 失效必须
归档: 编码 + 照片 + 模型 id + 步骤号", 凡"软件本应拦截却漏过"的失效
一律回填为负例夹具 (tests/test_physics_negative/) 的回归用例。本工具把
这条纪律从"口头约定"固化为一个机器可查的账本:

    data/physical_failures.json   (账本, 只经本工具读写, 勿手改)

每条登记项: model_id + 步骤号 + 失效编码 (F01~F12) + 照片路径 +
是否已下沉为 L1 负例夹具 (fixture_sunk / fixture_path)。闭环工作流
(抽样实搭 -> 失败登记 -> 生成负例夹具 -> CI 回归) 见
docs/PHYSICAL_CALIBRATION_WORKFLOW.md。

子命令:
    add        登记一次实物失效
                 --model <model_id>     必填, 须在 data/models/ 在库
                 --step N               必填, 教程步骤号 (0 = 成品固定
                                        动作阶段: 敲击/提起/拆解重搭)
                 --code FXX             必填, F01~F12 (BUILD_VERIFICATION.md §4)
                 --photo PATH|URL       必填, 失效照片 (仓库相对路径或
                                        QA 工单附件链接; 命名约定见
                                        PHYSICAL_REVIEW_USER_GUIDE.md §7)
                 --tester NAME          复核人 (建议填写)
                 --notes TEXT           现象一句话
                 --date YYYY-MM-DD      失效日期 (默认今天)
                 --sunk-fixture PATH    登记时已有对应夹具 (校验后直接记为已下沉)
    mark-sunk  把一条登记项标记为"已下沉 L1 夹具"
                 mark-sunk PF-0001 --fixture tests/test_physics_negative/<name>.json
                 夹具 JSON + .expected sidecar 必须存在, 且夹具名已登记进
                 tests/test_physics_fixture_registry.sh 的 REQUIRED_NEGATIVE
                 必备清单 (--allow-unregistered 可跳过, 仅限过渡期)
    list       列出账本 (--model/--code/--pending-sink 过滤, --json 机器可读)
    check      账本完整性门禁 (CI 挂接用): 编码合法 / 模型在库 / 已下沉项
                 的夹具与 sidecar 在位且已进必备清单; 报告"待下沉"缺口与
                 "仅 L3"编码 >= 3 次的季度复盘立项信号
                 --fail-on-pending-sink  存在 L1 必下沉而未下沉项时退出码 1

通用选项: --registry FILE 覆盖账本路径 (默认 data/physical_failures.json)。

退出码: 0 = 成功 / 1 = 门禁失败 (check 发现完整性错误, 或
--fail-on-pending-sink 命中) / 2 = 参数或数据错误
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "data" / "physical_failures.json"
MODELS_DIR = ROOT / "data" / "models"
NEG_DIR = ROOT / "tests" / "test_physics_negative"
FIXTURE_REGISTRY_SH = ROOT / "tests" / "test_physics_fixture_registry.sh"

SCHEMA_VERSION = 1

# 失效分类学 (与 BUILD_VERIFICATION.md 第 4 节逐行对应, 改表必须两处同步):
#   name       失效模式名
#   rule       应拦截的软件规则 / 缓解手段
#   layer      首个能发现的层
#   sink       下沉目标:
#     "L1"      必须下沉为 tests/test_physics_negative/ 负例夹具 (error 级),
#               漏过 = L1 规则或参数有缺陷, check 计入"待下沉"缺口;
#     "L1-警告"  缓解性下沉 (R8 类 warning 级夹具), 建议但不强制;
#     "L2"      归 L2 仿真管线 (蒙特卡洛容差抖动); 管线落地前若能构造
#               L1 代理夹具 (如长链/高墙预警) 亦计已下沉;
#     None      不可规则化 (品牌/环境/套件问题), 只计数供季度复盘 ——
#               同一编码累计 >= 3 次即触发"立项评估规则化"信号。
FAILURE_CODES = {
    "F01": {"name": "错位半搭", "rule": "R2 磁力吸合 (connect_tolerance)", "layer": "L1", "sink": "L1"},
    "F02": {"name": "空中孤片", "rule": "R1 接地支撑 (floating_tile)", "layer": "L1", "sink": "L1"},
    "F03": {"name": "悬挑倾覆", "rule": "R4 重心稳定 + R6 悬臂力矩 (cantilever_overload)", "layer": "L1", "sink": "L1"},
    "F04": {"name": "同层穿插", "rule": "R3 无重叠 (共面 SAT)", "layer": "L1", "sink": "L1"},
    "F05": {"name": "混品牌弱磁脱落", "rule": "软件不可拦截 -> L3 品牌测试 + 品牌兼容元数据", "layer": "仅 L3", "sink": None},
    "F06": {"name": "放置干涉 (够不着)", "rule": "R7 装配可达 (enclosed_placement); 操作空间校验仍属规划 (PHYSICS_RULES §8.3)", "layer": "L1/L3", "sink": "L1"},
    "F07": {"name": "手抖连锁塌", "rule": "缓解: R8 结构冗余警告 + 每步 <= 8 片粒度", "layer": "L3 儿童测试", "sink": "L1-警告"},
    "F08": {"name": "错位累积失稳", "rule": "L2 蒙特卡洛容差抖动; 长链结构预警", "layer": "L2", "sink": "L2"},
    "F09": {"name": "底面滑移", "rule": "测试环境规范 (3.0) + 教程通用防滑提示", "layer": "仅 L3", "sink": None},
    "F10": {"name": "拆不下来", "rule": "规划中的可达性校验逆向应用", "layer": "仅 L3", "sink": None},
    "F11": {"name": "重心出界", "rule": "R4 重心稳定 (unstable_center_of_mass)", "layer": "L1", "sink": "L1"},
    "F12": {"name": "磁力衰减片", "rule": "测试套件管理 (3.0 剔除 + 3.5 季度标定)", "layer": "仅 L3", "sink": None},
}

QUARTERLY_REVIEW_THRESHOLD = 3  # BUILD_VERIFICATION.md §4 维护要求: 仅 L3 编码 >= 3 次立项评估


def load_registry(path: Path) -> dict:
    """读账本; 不存在时返回空账本骨架 (首次 add 落盘时创建)。"""
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION,
                "_comment": "实物失效登记账本, 由 tools/physical_failure_registry.py 维护, 勿手改",
                "failures": []}
    try:
        reg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"错误: 账本 {path} 无法解析: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(reg.get("failures"), list):
        print(f"错误: 账本 {path} 缺少 failures 数组", file=sys.stderr)
        sys.exit(2)
    return reg


def save_registry(path: Path, reg: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_failure_id(reg: dict) -> str:
    max_n = 0
    for e in reg["failures"]:
        m = re.fullmatch(r"PF-(\d+)", str(e.get("failure_id", "")))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"PF-{max_n + 1:04d}"


def required_negative_names() -> set:
    """解析 tests/test_physics_fixture_registry.sh 的 REQUIRED_NEGATIVE 必备清单。"""
    if not FIXTURE_REGISTRY_SH.is_file():
        return set()
    text = FIXTURE_REGISTRY_SH.read_text(encoding="utf-8")
    m = re.search(r'REQUIRED_NEGATIVE="([^"]*)"', text)
    if not m:
        return set()
    return {line.strip() for line in m.group(1).splitlines() if line.strip()}


def is_url(photo: str) -> bool:
    return photo.startswith("http://") or photo.startswith("https://")


def validate_fixture(fixture: str, allow_unregistered: bool) -> list:
    """校验下沉夹具: 返回错误列表 (空 = 通过)。fixture 为仓库相对路径。"""
    errors = []
    fpath = ROOT / fixture
    if not fpath.is_file():
        errors.append(f"夹具不存在: {fixture}")
        return errors
    try:
        rel = fpath.resolve().relative_to(NEG_DIR.resolve())
        if rel.parent != Path("."):
            errors.append(f"夹具不在负例目录顶层: {fixture}")
    except ValueError:
        errors.append(f"夹具不在负例目录 tests/test_physics_negative/ 下: {fixture}")
        return errors
    sidecar = fpath.with_suffix(".expected")
    if not sidecar.is_file():
        errors.append(f"夹具缺少 .expected sidecar: {sidecar.relative_to(ROOT)} "
                      "(负例没有断言等于没有测试)")
    if not allow_unregistered:
        name = fpath.stem
        if name not in required_negative_names():
            errors.append(
                f"夹具 {name} 未登记进 tests/test_physics_fixture_registry.sh 的 "
                "REQUIRED_NEGATIVE 必备清单 —— 未登记的夹具被误删时只会静默消失, "
                "不算完成下沉 (先登记, 或过渡期用 --allow-unregistered)")
    return errors


def photo_convention_notice(photo: str, model_id: str, step: int, code: str) -> str:
    """照片命名约定核对 (仅提示, 不阻断)。"""
    if is_url(photo):
        return ""
    canonical = f"docs/reports/qa_photos/{model_id}/fail_step{step:02d}_{code}.jpg"
    legacy = re.compile(rf"assets/failures/{code}_{re.escape(model_id)}_\d+\.(jpg|jpeg|png)$")
    if photo == canonical or legacy.search(photo):
        return ""
    return (f"提示: 照片路径不符合归档约定, 建议 {canonical} "
            "(PHYSICAL_REVIEW_USER_GUIDE.md §7) 或 assets/failures/<编码>_<模型id>_<序号>.jpg "
            "(BUILD_VERIFICATION.md §4)")


def cmd_add(args) -> int:
    code = args.code.upper()
    if code not in FAILURE_CODES:
        print(f"错误: 失效编码 {args.code} 非法, 必须是 " + "/".join(sorted(FAILURE_CODES)),
              file=sys.stderr)
        return 2
    if args.step < 0:
        print("错误: --step 必须 >= 0 (0 = 成品固定动作阶段)", file=sys.stderr)
        return 2
    try:
        day = date.fromisoformat(args.date) if args.date else date.today()
    except ValueError:
        print(f"错误: --date 必须是 ISO 8601 日期 (YYYY-MM-DD): {args.date}", file=sys.stderr)
        return 2

    model_path = MODELS_DIR / f"{args.model}.json"
    if not model_path.is_file():
        print(f"错误: 模型不在库: {model_path.relative_to(ROOT)} "
              "(失效必须挂到在库模型; 模型改名/下架请先更新账本)", file=sys.stderr)
        return 2
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"错误: 模型 JSON 无法解析: {model_path}: {exc}", file=sys.stderr)
        return 2
    step_count = len(model.get("steps", []))
    if args.step > step_count:
        print(f"警告: 步骤号 {args.step} 超出该模型步骤数 {step_count} (仍登记, 请复核)")

    fixture_sunk, fixture_path = False, None
    if args.sunk_fixture:
        errs = validate_fixture(args.sunk_fixture, args.allow_unregistered)
        if errs:
            for e in errs:
                print(f"错误: {e}", file=sys.stderr)
            return 2
        fixture_sunk, fixture_path = True, args.sunk_fixture

    notice = photo_convention_notice(args.photo, args.model, args.step, code)
    if notice:
        print(notice)
    if not is_url(args.photo) and not (ROOT / args.photo).is_file():
        print(f"警告: 照片文件暂不在仓库: {args.photo} (可后补; check 会持续提醒)")

    reg = load_registry(args.registry)
    dup = [e for e in reg["failures"]
           if e.get("model_id") == args.model and e.get("step") == args.step
           and e.get("code") == code]
    if dup:
        print(f"提示: 已存在 {len(dup)} 条同模型同步骤同编码登记 ({dup[0]['failure_id']} 等) "
              "—— 复发按新条目登记是对的 (复发次数是季度复盘的输入), 误重复请手工确认")

    entry = {
        "failure_id": next_failure_id(reg),
        "model_id": args.model,
        "step": args.step,
        "code": code,
        "photo": args.photo,
        "date": day.isoformat(),
        "tester": args.tester or "",
        "notes": args.notes or "",
        "fixture_sunk": fixture_sunk,
        "fixture_path": fixture_path,
        "sunk_at": day.isoformat() if fixture_sunk else None,
    }
    reg["failures"].append(entry)
    save_registry(args.registry, reg)

    info = FAILURE_CODES[code]
    print(f"已登记 {entry['failure_id']}: {args.model} 第 {args.step} 步 "
          f"{code} ({info['name']})")
    if fixture_sunk:
        print(f"  已下沉 L1 夹具: {fixture_path}")
    elif info["sink"] == "L1":
        print(f"  下一步 (必做): 该编码首个能发现的层是 {info['layer']}, 应拦截规则为 "
              f"{info['rule']} —— 按 docs/PHYSICAL_CALIBRATION_WORKFLOW.md 第 4 步"
              "提炼最小复现负例夹具并 mark-sunk")
    elif info["sink"] == "L1-警告":
        print(f"  建议: 评估缓解性下沉 ({info['rule']}), warning 级夹具")
    elif info["sink"] == "L2":
        print("  归 L2 仿真管线; 管线落地前可评估 L1 代理夹具 (长链/高墙预警)")
    else:
        print(f"  该编码不可规则化 ({info['rule']}); 累计 >= {QUARTERLY_REVIEW_THRESHOLD} 次"
              "将触发季度复盘立项信号 (check 自动盘点)")
    return 0


def cmd_mark_sunk(args) -> int:
    reg = load_registry(args.registry)
    entry = next((e for e in reg["failures"] if e.get("failure_id") == args.failure_id), None)
    if entry is None:
        print(f"错误: 账本中没有登记项 {args.failure_id} (用 list 查看现有编号)", file=sys.stderr)
        return 2
    errs = validate_fixture(args.fixture, args.allow_unregistered)
    if errs:
        for e in errs:
            print(f"错误: {e}", file=sys.stderr)
        return 2
    entry["fixture_sunk"] = True
    entry["fixture_path"] = args.fixture
    entry["sunk_at"] = date.today().isoformat()
    save_registry(args.registry, reg)
    print(f"{args.failure_id} 已标记下沉: {args.fixture}")
    print("  收尾自查: 夹具在 REQUIRED_NEGATIVE 已登记; 本地重跑负例回归确认夹具确实被拒 "
          "(见 docs/PHYSICAL_CALIBRATION_WORKFLOW.md 第 5 步)")
    return 0


def _sink_status(entry: dict) -> str:
    if entry.get("fixture_sunk"):
        return f"已下沉 -> {entry.get('fixture_path')}"
    sink = FAILURE_CODES.get(entry.get("code"), {}).get("sink")
    if sink == "L1":
        return "待下沉 (L1 必做)"
    if sink == "L1-警告":
        return "待评估 (缓解性 warning 夹具)"
    if sink == "L2":
        return "归 L2 管线 (未落地)"
    return "不可规则化 (计数复盘)"


def cmd_list(args) -> int:
    reg = load_registry(args.registry)
    entries = reg["failures"]
    if args.model:
        entries = [e for e in entries if e.get("model_id") == args.model]
    if args.code:
        entries = [e for e in entries if e.get("code") == args.code.upper()]
    if args.pending_sink:
        entries = [e for e in entries if not e.get("fixture_sunk")
                   and FAILURE_CODES.get(e.get("code"), {}).get("sink") == "L1"]

    if args.as_json:
        out = []
        for e in entries:
            item = dict(e)
            item["sink_status"] = _sink_status(e)
            item["code_name"] = FAILURE_CODES.get(e.get("code"), {}).get("name", "?")
            out.append(item)
        print(json.dumps({"count": len(out), "failures": out}, ensure_ascii=False, indent=2))
        return 0

    print(f"== 实物失效登记账本 ({args.registry.name}, 共 {len(entries)} 条"
          + (", 已过滤" if len(entries) != len(reg["failures"]) else "") + ") ==")
    if not entries:
        print("(空 —— 尚无登记; 实搭失效后用 add 子命令入账)")
        return 0
    for e in entries:
        info = FAILURE_CODES.get(e.get("code"), {})
        print(f"{e.get('failure_id'):<8} {e.get('date', '?'):<11} "
              f"{e.get('model_id'):<28} 第{e.get('step'):>3} 步  "
              f"{e.get('code')} {info.get('name', '?')}")
        print(f"         照片: {e.get('photo')}")
        print(f"         下沉: {_sink_status(e)}"
              + (f"  复核人: {e['tester']}" if e.get("tester") else ""))
        if e.get("notes"):
            print(f"         备注: {e['notes']}")
    return 0


def cmd_check(args) -> int:
    reg = load_registry(args.registry)
    errors, warnings = [], []
    pending_sink, seen_ids = [], set()
    unsinkable_counts = {}

    for e in reg["failures"]:
        fid = e.get("failure_id", "?")
        if fid in seen_ids:
            errors.append(f"{fid}: failure_id 重复")
        seen_ids.add(fid)

        code = e.get("code")
        info = FAILURE_CODES.get(code)
        if info is None:
            errors.append(f"{fid}: 失效编码非法: {code}")
            continue

        for field in ("model_id", "photo", "date"):
            if not e.get(field):
                errors.append(f"{fid}: 缺少必填字段 {field}")
        if not isinstance(e.get("step"), int) or e.get("step", -1) < 0:
            errors.append(f"{fid}: step 必须是 >= 0 的整数")

        model_id = e.get("model_id")
        if model_id and not (MODELS_DIR / f"{model_id}.json").is_file():
            errors.append(f"{fid}: 模型不在库: {model_id} (模型改名/下架须同步账本)")

        photo = e.get("photo") or ""
        if photo and not is_url(photo) and not (ROOT / photo).is_file():
            warnings.append(f"{fid}: 照片文件不在仓库: {photo} (待后补, 或改登记 QA 工单链接)")

        if e.get("fixture_sunk"):
            fixture = e.get("fixture_path")
            if not fixture:
                errors.append(f"{fid}: fixture_sunk=true 但没有 fixture_path")
            else:
                for msg in validate_fixture(fixture, allow_unregistered=False):
                    errors.append(f"{fid}: {msg}")
        else:
            if info["sink"] == "L1":
                pending_sink.append(e)
            elif info["sink"] is None:
                unsinkable_counts[code] = unsinkable_counts.get(code, 0) + 1

    print(f"== 账本完整性检查 ({args.registry.name}, {len(reg['failures'])} 条) ==")
    for msg in errors:
        print(f"[错误] {msg}")
    for msg in warnings:
        print(f"[警告] {msg}")

    if pending_sink:
        print(f"\n-- 待下沉 L1 夹具 ({len(pending_sink)} 条, 该拒未拒 = L1 规则缺口) --")
        for e in pending_sink:
            info = FAILURE_CODES[e["code"]]
            print(f"  {e['failure_id']}  {e['model_id']} 第 {e['step']} 步  "
                  f"{e['code']} {info['name']}  应拦截: {info['rule']}")

    review = {c: n for c, n in unsinkable_counts.items() if n >= QUARTERLY_REVIEW_THRESHOLD}
    if review:
        print(f"\n-- 季度复盘立项信号 (仅 L3 编码累计 >= {QUARTERLY_REVIEW_THRESHOLD} 次) --")
        for c, n in sorted(review.items()):
            print(f"  {c} {FAILURE_CODES[c]['name']}: {n} 次 —— 按 BUILD_VERIFICATION.md §4 "
                  "维护要求, 立项评估能否规则化下沉到 L1/L2")

    if errors:
        print(f"\n[失败] 账本存在 {len(errors)} 处完整性错误")
        return 1
    if args.fail_on_pending_sink and pending_sink:
        print(f"\n[失败] 存在 {len(pending_sink)} 条 L1 必下沉而未下沉的失效 "
              "(--fail-on-pending-sink 生效)")
        return 1
    print(f"\n[通过] 账本完整 ({len(warnings)} 条警告, 待下沉 {len(pending_sink)} 条"
          + (" —— 默认仅报告" if pending_sink else "") + ")")
    return 0


def cmd_codes(_args) -> int:
    print("== 失效编码速查 (定义以 BUILD_VERIFICATION.md §4 为准) ==")
    for code in sorted(FAILURE_CODES):
        info = FAILURE_CODES[code]
        sink = {"L1": "下沉 L1 夹具 (必做)", "L1-警告": "缓解性下沉 (warning 夹具)",
                "L2": "归 L2 仿真管线", None: "不可规则化 (计数复盘)"}[info["sink"]]
        print(f"{code}  {info['name']:<14} 首发现层: {info['layer']:<10} {sink}")
        print(f"      应拦截/缓解: {info['rule']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="实物失效登记账本 (登记/下沉跟踪/完整性门禁), "
                    "闭环见 docs/PHYSICAL_CALIBRATION_WORKFLOW.md")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY,
                        help=f"账本路径 (默认 {DEFAULT_REGISTRY.relative_to(ROOT)})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="登记一次实物失效")
    p_add.add_argument("--model", required=True, help="模型 id (data/models/<id>.json)")
    p_add.add_argument("--step", required=True, type=int,
                       help="教程步骤号 (0 = 成品固定动作阶段: 敲击/提起/拆解重搭)")
    p_add.add_argument("--code", required=True, help="失效编码 F01~F12")
    p_add.add_argument("--photo", required=True,
                       help="失效照片: 仓库相对路径或 QA 工单附件 URL")
    p_add.add_argument("--tester", default="", help="复核人")
    p_add.add_argument("--notes", default="", help="现象一句话")
    p_add.add_argument("--date", default=None, help="失效日期 YYYY-MM-DD (默认今天)")
    p_add.add_argument("--sunk-fixture", default=None,
                       help="登记时已有对应负例夹具 (tests/test_physics_negative/*.json)")
    p_add.add_argument("--allow-unregistered", action="store_true",
                       help="允许夹具暂未进 REQUIRED_NEGATIVE 必备清单 (仅限过渡期)")
    p_add.set_defaults(func=cmd_add)

    p_sunk = sub.add_parser("mark-sunk", help="把登记项标记为已下沉 L1 夹具")
    p_sunk.add_argument("failure_id", help="登记编号, 如 PF-0001")
    p_sunk.add_argument("--fixture", required=True,
                        help="负例夹具路径 (tests/test_physics_negative/*.json)")
    p_sunk.add_argument("--allow-unregistered", action="store_true",
                        help="允许夹具暂未进 REQUIRED_NEGATIVE 必备清单 (仅限过渡期)")
    p_sunk.set_defaults(func=cmd_mark_sunk)

    p_list = sub.add_parser("list", help="列出账本")
    p_list.add_argument("--model", default=None, help="按模型 id 过滤")
    p_list.add_argument("--code", default=None, help="按失效编码过滤")
    p_list.add_argument("--pending-sink", action="store_true",
                        help="只看 L1 必下沉而未下沉的条目")
    p_list.add_argument("--json", action="store_true", dest="as_json", help="机器可读输出")
    p_list.set_defaults(func=cmd_list)

    p_check = sub.add_parser("check", help="账本完整性门禁 (CI 挂接用)")
    p_check.add_argument("--fail-on-pending-sink", action="store_true",
                         help="存在 L1 必下沉而未下沉项时退出码 1 (默认仅报告)")
    p_check.set_defaults(func=cmd_check)

    p_codes = sub.add_parser("codes", help="打印 F01~F12 失效编码速查表")
    p_codes.set_defaults(func=cmd_codes)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
