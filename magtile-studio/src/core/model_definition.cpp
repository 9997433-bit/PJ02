#include "magtile/core/model_definition.hpp"

#include <algorithm>

namespace magtile::core {

void ModelDefinition::ensureIndex() const {
    if (tile_index_.size() == final_assembly.size()) return;
    tile_index_.clear();
    for (const auto& tile : final_assembly) {
        tile_index_.emplace(tile.id, &tile);
    }
}

const TileInstance* ModelDefinition::findTile(const std::string& tile_id) const {
    ensureIndex();
    const auto it = tile_index_.find(tile_id);
    return it != tile_index_.end() ? it->second : nullptr;
}

std::vector<const TileInstance*> ModelDefinition::tilesUpToStep(int step_count) const {
    std::vector<const TileInstance*> result;
    // 上界预留: 全部步骤累计恰好覆盖 final_assembly (加载时已校验),
    // 免去每步渲染查询路径上的多次扩容拷贝 (基准 bench_tutorial_step)。
    result.reserve(final_assembly.size());
    const int limit = std::clamp<int>(step_count, 0, static_cast<int>(steps.size()));
    for (int i = 0; i < limit; ++i) {
        for (const auto& tile_id : steps[static_cast<std::size_t>(i)].tiles_to_add) {
            if (const TileInstance* tile = findTile(tile_id)) {
                result.push_back(tile);
            }
        }
    }
    return result;
}

std::map<TileType, int> ModelDefinition::pieceCountByType() const {
    std::map<TileType, int> counts;
    for (const auto& tile : final_assembly) {
        ++counts[tile.type];
    }
    return counts;
}

}  // namespace magtile::core
