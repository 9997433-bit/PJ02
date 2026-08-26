#!/usr/bin/env python3
"""Generate data/physical_set_catalog.json with 40+ sets across brands.

Templates follow docs/PHYSICAL_SET_CATALOG.md; brand-specific ids use
{brand}_{slug} except generic presets (standard_102, deluxe_198, ...).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "physical_set_catalog.json"

BRANDS = ("generic", "connetix", "magformers", "magna_tiles", "playmags")

# (slug, id_for_generic, name_zh_suffix, tier_scope, pieces)
TEMPLATES = (
    ("102", "standard_102", "标准102片套装", "core", {
        "square": 36, "equilateral_triangle": 24, "right_triangle": 12,
        "isosceles_triangle": 8, "rectangle": 6, "large_square": 4,
        "window_square": 4, "door_frame": 4, "wheel_base": 4,
    }),
    ("198", "deluxe_198", "豪华198片套装", "core+expansion", {
        "square": 50, "equilateral_triangle": 36, "right_triangle": 20,
        "isosceles_triangle": 12, "rectangle": 12, "large_square": 8,
        "window_square": 8, "door_frame": 6, "wheel_base": 6,
        "rhombus": 12, "trapezoid": 8, "hexagon": 8, "sector": 12,
    }),
    ("52", "starter_52", "入门52片套装", "core", {
        "square": 18, "equilateral_triangle": 12, "right_triangle": 6,
        "isosceles_triangle": 4, "rectangle": 4, "large_square": 2,
        "window_square": 2, "door_frame": 2, "wheel_base": 2,
    }),
    ("48_geo", "expansion_geometry_48", "几何扩展48片", "core+expansion", {
        "rhombus": 12, "trapezoid": 12, "hexagon": 12, "sector": 12,
    }),
    ("24_cars", "vehicles_24", "交通主题24片", "core", {
        "wheel_base": 8, "rectangle": 8, "square": 4, "equilateral_triangle": 4,
    }),
    ("150", "family_150", "家庭150片套装", "core", {
        "square": 54, "equilateral_triangle": 36, "right_triangle": 18,
        "isosceles_triangle": 12, "rectangle": 10, "large_square": 6,
        "window_square": 6, "door_frame": 4, "wheel_base": 4,
    }),
    ("60", "mini_60", "迷你60片套装", "core", {
        "square": 22, "equilateral_triangle": 14, "right_triangle": 8,
        "isosceles_triangle": 6, "rectangle": 4, "large_square": 2,
        "window_square": 2, "door_frame": 1, "wheel_base": 1,
    }),
    ("120", "creative_120", "创意120片套装", "core+expansion", {
        "square": 32, "equilateral_triangle": 24, "right_triangle": 12,
        "isosceles_triangle": 8, "rectangle": 8, "large_square": 4,
        "window_square": 4, "door_frame": 4, "wheel_base": 4,
        "rhombus": 8, "trapezoid": 6, "hexagon": 6, "sector": 4,
    }),
)

BRAND_LABEL = {
    "generic": "通用",
    "connetix": "Connetix",
    "magformers": "Magformers",
    "magna_tiles": "Magna-Tiles",
    "playmags": "Playmags",
}


def shift_pieces(pieces: dict[str, int], brand_idx: int) -> dict[str, int]:
    """Slight per-brand histogram variation; total unchanged."""
    if brand_idx == 0:
        return dict(pieces)
    out = dict(pieces)
    keys = sorted(out.keys())
    if len(keys) < 2:
        return out
    a, b = keys[brand_idx % len(keys)], keys[(brand_idx + 1) % len(keys)]
    delta = min(2, out[a])
    if out[b] + delta <= out[b] + 2:
        out[a] -= delta
        out[b] += delta
    return out


def build_entry(brand: str, brand_idx: int, slug: str, generic_id: str,
                name_suffix: str, tier_scope: str, pieces: dict[str, int]) -> dict:
    pieces = shift_pieces(pieces, brand_idx)
    total = sum(pieces.values())
    set_id = generic_id if brand == "generic" else f"{brand}_{slug}"
    label = BRAND_LABEL[brand]
    name_zh = f"{label}{name_suffix}" if brand != "generic" else name_suffix
    return {
        "id": set_id,
        "brand": brand,
        "name_zh": name_zh,
        "name_en": name_zh,
        "piece_count_label": total,
        "tier_scope": tier_scope,
        "ui_preset_label_zh": name_zh,
        "description_zh": (
            f"{label}常见盒装口径 (近似值, 见 PHYSICAL_SET_CATALOG.md §5); "
            f"{'仅核心9片型' if tier_scope == 'core' else '含扩展片型'}。"
        ),
        "pieces": pieces,
    }


def main() -> None:
    sets = []
    for brand_idx, brand in enumerate(BRANDS):
        for slug, generic_id, name_suffix, tier_scope, pieces in TEMPLATES:
            sets.append(build_entry(brand, brand_idx, slug, generic_id,
                                    name_suffix, tier_scope, pieces))
    catalog = {
        "schema_version": 1,
        "comment": (
            "实物磁力片套装目录: 用户勾选家里拥有的盒装套装 → 按片型求和得到 "
            "tile_inventory → 现有 canBuild / inventory match 直接可用。"
        ),
        "sets": sets,
    }
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    by_brand: dict[str, int] = {}
    for s in sets:
        by_brand[s["brand"]] = by_brand.get(s["brand"], 0) + 1
    print(f"Wrote {len(sets)} sets to {OUT}")
    for b, n in sorted(by_brand.items()):
        print(f"  {b}: {n}")


if __name__ == "__main__":
    main()
