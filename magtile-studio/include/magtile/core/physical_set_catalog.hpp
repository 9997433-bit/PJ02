#pragma once

// =============================================================
// MagTile Studio - 实物磁力片套装目录
// 从 data/physical_set_catalog.json 加载常见套装 BOM, 供库存录入
// 快捷预填 (UI_UX_SPEC.md §10.2)。多套装选中时按片型求和合并。
// =============================================================

#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace magtile::core {

/// 一种市售实物套装 (品牌 + 名称 + 片数 + BOM)。
struct PhysicalSet {
    std::string id;                         ///< 稳定标识, 如 "standard_102"
    std::string brand;                      ///< 品牌/系列, 如 "generic"
    std::string name;                       ///< 展示名 (name_zh)
    int total_pieces = 0;                   ///< 标称总片数 (piece_count_label)
    std::string tier_scope;                 ///< core / core+expansion
    std::string ui_preset_label;            ///< 录入界面快捷按钮文案 (可选)
    std::map<std::string, int> bom;         ///< 片型标识 -> 数量 (pieces)
};

/// 全部可用实物套装目录。
class PhysicalSetCatalog {
public:
    void addSet(PhysicalSet set);

    [[nodiscard]] const PhysicalSet* find(const std::string& id) const noexcept;
    [[nodiscard]] std::size_t size() const noexcept { return sets_.size(); }
    [[nodiscard]] const std::vector<PhysicalSet>& sets() const noexcept { return sets_; }

private:
    std::vector<PhysicalSet> sets_;
};

/// 从 data/physical_set_catalog.json 加载套装目录。
[[nodiscard]] PhysicalSetCatalog loadPhysicalSetCatalog(const std::filesystem::path& file);

/// 合并多个套装的 BOM (未知 id 跳过; 同片型数量相加)。
[[nodiscard]] std::map<std::string, int> mergePhysicalSetBom(const PhysicalSetCatalog& catalog,
                                                             const std::vector<std::string>& set_ids);

}  // namespace magtile::core
