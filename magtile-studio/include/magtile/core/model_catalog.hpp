#pragma once

// =============================================================
// MagTile Studio - 模型库目录 (data/model_catalog.json)
//
// 商业版模型库界面 (magtile_app library) 的数据源: 只包含展示所需
// 的元数据, 不加载几何与教程步骤, 保证模型库启动即开 (模型本体在
// 用户点击卡片后才按需加载)。
//
// 兜底策略: 目录文件不存在时自动扫描 data/models/*.json 生成条目;
// 目录存在时也会把未登记的模型文件补录到末尾 (内容制作期新模型
// 未登记也能出现在库中); 条目缺少元数据字段时按需加载模型 JSON 补全。
// =============================================================

#include <filesystem>
#include <string>
#include <vector>

#include "magtile/core/model_definition.hpp"

namespace magtile::core {

/// 模型库目录中的一个条目 (一张"模型卡片"所需的全部元数据)。
struct ModelCatalogEntry {
    std::string id;               ///< 模型唯一标识, 与模型 JSON 的 id 一致
    std::filesystem::path file;   ///< 模型 JSON 路径 (已相对 data 目录解析)
    std::string name;             ///< 中文名称
    std::string name_en;          ///< 英文名称 (可选)
    std::string description;     ///< 中文简介
    int difficulty = ModelDefinition::kMinDifficulty;  ///< 难度 1~5
    int total_pieces = 0;         ///< 磁力片总数
    int step_count = 0;           ///< 教程步骤数
    std::vector<std::string> tags;  ///< 分类标签, 第一个为主题

    /// 主题标签 (决定卡片主题色), 无标签时归入 "未分类"。
    [[nodiscard]] const std::string& theme() const noexcept {
        static const std::string kUncategorized = "未分类";
        return tags.empty() ? kUncategorized : tags.front();
    }
};

/// 加载 data_dir/model_catalog.json 并返回全部条目 (保持文件内顺序,
/// 未登记的模型文件按文件名排序补录到末尾)。目录文件不存在时扫描
/// data_dir/models/*.json 自动生成。
/// 数据有误 (缺字段 / 引用的模型文件不存在 / id 重复) 时抛 JsonIoError。
[[nodiscard]] std::vector<ModelCatalogEntry> loadModelCatalog(
    const std::filesystem::path& data_dir);

}  // namespace magtile::core
