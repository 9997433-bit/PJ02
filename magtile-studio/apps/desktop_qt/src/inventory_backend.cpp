#include "inventory_backend.hpp"

#include <algorithm>
#include <map>
#include <string>
#include <utility>

#include "magtile/core/json_io.hpp"
#include "magtile/core/types.hpp"

namespace magtile::qtui {

namespace {

QString fromUtf8(const std::string& s) {
    return QString::fromUtf8(s.c_str(), static_cast<int>(s.size()));
}

QString fromView(std::string_view s) {
    return QString::fromUtf8(s.data(), static_cast<int>(s.size()));
}

/// 与 GL 版录入界面一致的数量上限 (纯 UI 约束, 存储层只校验 >= 0)。
constexpr int kCountMax = 999;

}  // namespace

InventoryBackend::InventoryBackend(std::filesystem::path data_dir, std::filesystem::path db_file,
                                   QObject* parent)
    : QObject(parent) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(db_file);
    } catch (const progress::ProgressError&) {
        store_.reset();  // 存档打不开只影响保存, 片型清单照常可浏览
    }
    try {
        tile_catalog_ = core::loadTileCatalog(data_dir / "tile_catalog.json");
        tile_catalog_loaded_ = tile_catalog_.size() > 0;
    } catch (const std::exception&) {
        tile_catalog_loaded_ = false;  // 退回 displayNameZh 与枚举位置分层
    }
}

InventoryBackend::~InventoryBackend() = default;

bool InventoryBackend::configured() const {
    if (!store_) return false;
    try {
        return store_->hasInventory();
    } catch (const progress::ProgressError&) {
        return false;
    }
}

int InventoryBackend::totalCount() const {
    if (!store_) return 0;
    try {
        int total = 0;
        for (const auto& [shape_id, count] : store_->getInventory()) {
            (void)shape_id;
            total += count;
        }
        return total;
    } catch (const progress::ProgressError&) {
        return 0;
    }
}

QVariantList InventoryBackend::rows() const {
    std::map<std::string, int> saved;
    if (store_) {
        try {
            saved = store_->getInventory();
        } catch (const progress::ProgressError&) {
            // 读取失败按空库存处理, 界面仍可录入
        }
    }

    QVariantList result;
    for (int i = 0; i < core::kTileTypeCount; ++i) {
        const auto type = static_cast<core::TileType>(i);
        const std::string shape_id{core::toString(type)};

        QString name_zh = fromView(core::displayNameZh(type));
        // 枚举顺序约定: 核心 9 片型在前 (types.hpp), 目录可用时以 tier 为准
        bool expansion = type >= core::TileType::Rhombus;
        if (tile_catalog_loaded_) {
            if (const core::TileShape* shape = tile_catalog_.find(type); shape != nullptr) {
                if (!shape->name_zh.empty()) name_zh = fromUtf8(shape->name_zh);
                expansion = shape->tier != "core";
            }
        }

        QVariantMap row;
        row.insert(QStringLiteral("shapeId"), fromUtf8(shape_id));
        row.insert(QStringLiteral("nameZh"), name_zh);
        row.insert(QStringLiteral("expansion"), expansion);
        const auto it = saved.find(shape_id);
        row.insert(QStringLiteral("count"), it != saved.end() ? it->second : 0);
        result.push_back(row);
    }
    return result;
}

bool InventoryBackend::save(const QVariantMap& counts) {
    if (!store_) return false;
    try {
        for (auto it = counts.constBegin(); it != counts.constEnd(); ++it) {
            const std::string shape_id = it.key().toStdString();
            if (!core::tileTypeFromString(shape_id).has_value()) continue;  // 未知标识跳过
            const int count = std::clamp(it.value().toInt(), 0, kCountMax);
            store_->setInventory(shape_id, count);
        }
    } catch (const progress::ProgressError&) {
        return false;
    }
    emit inventoryChanged();
    return true;
}

}  // namespace magtile::qtui
