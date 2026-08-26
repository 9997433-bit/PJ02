#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 实物套装目录校验 (ctest: physical_set_catalog)
#
# 检查项:
#   tools/verify_physical_set_catalog.py 对 data/physical_set_catalog.json
#   与 data/tile_catalog.json 的结构守卫 (片型存在 / 计数 >= 0 /
#   套装 id 唯一 / 合计与 piece_count_label 一致 / tier_scope 一致)。
#
# 用法:
#   tests/test_physical_set_catalog.sh [项目根]
# =============================================================
set -u

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
PYTHON="${PYTHON:-python3}"

if ! "$PYTHON" "$ROOT/tools/verify_physical_set_catalog.py" \
        --catalog "$ROOT/data/tile_catalog.json" \
        --physical "$ROOT/data/physical_set_catalog.json"; then
    echo "实物套装目录校验失败" >&2
    exit 1
fi

echo "实物套装目录校验通过"
exit 0
