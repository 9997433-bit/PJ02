#include "studio_backend.hpp"

#include <algorithm>
#include <exception>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "magtile/core/json_io.hpp"
#include "magtile/core/model_catalog.hpp"
#include "magtile/core/model_definition.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/core/types.hpp"

namespace magtile::qtui {

namespace {

QString fromUtf8(const std::string& s) {
    return QString::fromUtf8(s.c_str(), static_cast<int>(s.size()));
}

QString fromUtf8(std::string_view s) {
    return QString::fromUtf8(s.data(), static_cast<int>(s.size()));
}

}  // namespace

StudioBackend::StudioBackend(std::filesystem::path data_dir, std::filesystem::path db_file,
                             QObject* parent)
    : QObject(parent), data_dir_(std::move(data_dir)), db_file_(std::move(db_file)) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(db_file_);
    } catch (const progress::ProgressError&) {
        // 存档打不开只影响进度徽标, 模型库照常可浏览 (P3 零挫败)
        store_.reset();
    }
    library_filter_.setSourceModel(&library_model_);
    reload();
}

StudioBackend::~StudioBackend() = default;

bool StudioBackend::isCoreTile(core::TileType type) const {
    // 共享判定 (core::isCoreTile): 目录 tier 优先, 目录不可用时
    // 退回核心库内的兜底白名单 —— CLI / GL / Qt 三端同一口径。
    if (tile_catalog_loaded_) {
        return core::isCoreTile(tile_catalog_, type);
    }
    return core::isCoreTileFallback(type);
}

QString StudioBackend::shapeNameZh(core::TileType type) const {
    if (tile_catalog_loaded_) {
        if (const core::TileShape* shape = tile_catalog_.find(type)) {
            if (!shape->name_zh.empty()) return fromUtf8(shape->name_zh);
        }
    }
    return fromUtf8(core::displayNameZh(type));
}

QString StudioBackend::missingText(const LibraryRow& row) const {
    QStringList parts;
    for (const auto& [type, count] : row.missing) {
        parts << QStringLiteral("%1 片%2").arg(count).arg(shapeNameZh(type));
    }
    if (parts.isEmpty()) return {};
    return QStringLiteral("缺 ") + parts.join(QStringLiteral("、"));
}

void StudioBackend::reload() {
    std::vector<LibraryRow> rows;
    total_pieces_ = 0;
    in_progress_count_ = 0;
    completed_count_ = 0;
    continue_title_.clear();
    continue_model_id_.clear();
    themes_.clear();

    // ---- 片型目录 (core-9 分层与 BOM 中文名的数据源) ---------------------
    tile_catalog_loaded_ = false;
    try {
        tile_catalog_ = core::loadTileCatalog(data_dir_ / "tile_catalog.json");
        tile_catalog_loaded_ = true;
    } catch (const core::JsonIoError&) {
        // 目录缺失时 isCoreTile 退回代码内白名单, 界面照常可用
    }

    // ---- 磁力片库存快照 (「我能搭的」与缺片提示的数据源) ------------------
    inventory_.clear();
    inventory_configured_ = false;
    if (store_) {
        try {
            inventory_configured_ = store_->hasInventory();
            for (const auto& [shape_id, count] : store_->getInventory()) {
                if (const auto type = core::tileTypeFromString(shape_id)) {
                    inventory_[*type] = count;
                }
            }
        } catch (const progress::ProgressError&) {
            inventory_.clear();
            inventory_configured_ = false;
        }
    }

    std::vector<core::ModelCatalogEntry> entries;
    try {
        entries = core::loadModelCatalog(data_dir_);
        status_message_.clear();
    } catch (const core::JsonIoError& err) {
        status_message_ = QStringLiteral("模型库正在准备中: %1")
                              .arg(QString::fromUtf8(err.what()));
    }

    rows.reserve(entries.size());
    std::unordered_map<std::string, std::size_t> row_by_id;
    for (core::ModelCatalogEntry& entry : entries) {
        LibraryRow row;
        row.entry = std::move(entry);
        total_pieces_ += row.entry.total_pieces;

        const QString theme = fromUtf8(row.entry.theme());
        if (!themes_.contains(theme)) themes_ << theme;

        // BOM 与库存对照 (与 GL 版一致: 模型 JSON 只在 reload 时加载一次;
        // 单个模型文件有问题按 "BOM 未知 / 不可搭" 温和降级, 不影响其余卡片)
        try {
            const core::ModelDefinition model = core::loadModelDefinition(row.entry.file);
            row.bom = model.pieceCountByType();
            row.bom_known = true;
            row.core9_only = std::all_of(
                row.bom.begin(), row.bom.end(),
                [this](const auto& kv) { return isCoreTile(kv.first); });
            if (inventory_configured_) {
                for (const auto& [type, needed] : row.bom) {
                    const auto it = inventory_.find(type);
                    const int have = it == inventory_.end() ? 0 : it->second;
                    if (needed > have) {
                        row.missing[type] = needed - have;
                        row.missing_total += needed - have;
                    }
                }
                row.can_build = row.missing.empty();
            }
        } catch (const std::exception&) {
            // 模型文件问题由目录对账用例负责报告, 这里按 BOM 未知处理
        }

        if (store_) {
            try {
                if (std::optional<progress::Progress> p = store_->loadProgress(row.entry.id)) {
                    row.favorited = p->favorited;
                    if (p->isCompleted()) {
                        row.status = LibraryModel::StatusCompleted;
                        ++completed_count_;
                    } else if (p->current_step > 0) {
                        row.status = LibraryModel::StatusInProgress;
                        row.current_step = p->current_step;
                        ++in_progress_count_;
                    }
                }
            } catch (const progress::ProgressError&) {
                // 单条读取失败按未开始处理
            }
        }
        row_by_id.emplace(row.entry.id, rows.size());
        rows.push_back(std::move(row));
    }

    // "继续上次"大卡片 (UI_UX_SPEC.md §5.2): 最近游玩且仍在库中的模型
    if (store_) {
        try {
            for (const progress::Progress& p : store_->listInProgress()) {
                auto it = row_by_id.find(p.model_id);
                if (it == row_by_id.end() || p.current_step <= 0) continue;
                const LibraryRow& row = rows[it->second];
                continue_title_ = QStringLiteral("%1 · 第 %2/%3 步")
                                      .arg(QString::fromStdString(row.entry.name))
                                      .arg(p.current_step)
                                      .arg(row.entry.step_count);
                continue_model_id_ = fromUtf8(row.entry.id);
                break;
            }
        } catch (const progress::ProgressError&) {
            // 忽略: 无"继续上次"卡片即可
        }
    }

    if (status_message_.isEmpty()) {
        status_message_ = QStringLiteral("模型库已就绪: %1 个模型 · 共 %2 片")
                              .arg(rows.size())
                              .arg(total_pieces_);
        if (!store_) {
            status_message_ += QStringLiteral(" (进度存档暂不可用)");
        }
    }

    library_model_.resetRows(std::move(rows));
    emit catalogChanged();
}

bool StudioBackend::toggleFavorite(const QString& model_id) {
    const std::string id = model_id.toStdString();
    const LibraryRow* row = library_model_.findRow(id);
    const bool current = row != nullptr && row->favorited;
    if (!store_) return current;  // 存档不可用: 状态不变, 不弹"失败"
    try {
        const bool favorited = store_->toggleFavorite(id);
        library_model_.setFavorited(id, favorited);
        return favorited;
    } catch (const progress::ProgressError&) {
        return current;
    }
}

QVariantMap StudioBackend::modelDetail(const QString& model_id) const {
    QVariantMap detail;
    const LibraryRow* row = library_model_.findRow(model_id.toStdString());
    if (row == nullptr) {
        detail.insert(QStringLiteral("found"), false);
        return detail;
    }
    const core::ModelCatalogEntry& e = row->entry;
    detail.insert(QStringLiteral("found"), true);
    detail.insert(QStringLiteral("modelId"), fromUtf8(e.id));
    detail.insert(QStringLiteral("name"), fromUtf8(e.name));
    detail.insert(QStringLiteral("nameEn"), fromUtf8(e.name_en));
    detail.insert(QStringLiteral("description"), fromUtf8(e.description));
    detail.insert(QStringLiteral("difficulty"), e.difficulty);
    detail.insert(QStringLiteral("pieces"), e.total_pieces);
    detail.insert(QStringLiteral("steps"), e.step_count);
    detail.insert(QStringLiteral("theme"), fromUtf8(e.theme()));
    detail.insert(QStringLiteral("status"), row->status);
    detail.insert(QStringLiteral("currentStep"), row->current_step);
    detail.insert(QStringLiteral("favorited"), row->favorited);
    detail.insert(QStringLiteral("bomKnown"), row->bom_known);
    detail.insert(QStringLiteral("core9Only"), row->core9_only);
    detail.insert(QStringLiteral("canBuild"), row->can_build);
    detail.insert(QStringLiteral("missingTotal"), row->missing_total);
    detail.insert(QStringLiteral("missingText"), missingText(*row));
    return detail;
}

QVariantList StudioBackend::bomForModel(const QString& model_id) const {
    QVariantList bom;
    const LibraryRow* row = library_model_.findRow(model_id.toStdString());
    if (row == nullptr || !row->bom_known) return bom;
    for (const auto& [type, needed] : row->bom) {
        const auto have_it = inventory_.find(type);
        const auto missing_it = row->missing.find(type);
        QVariantMap item;
        item.insert(QStringLiteral("shapeName"), shapeNameZh(type));
        item.insert(QStringLiteral("needed"), needed);
        item.insert(QStringLiteral("have"),
                    have_it == inventory_.end() ? 0 : have_it->second);
        item.insert(QStringLiteral("missing"),
                    missing_it == row->missing.end() ? 0 : missing_it->second);
        item.insert(QStringLiteral("isCore"), isCoreTile(type));
        bom.append(item);
    }
    return bom;
}

void StudioBackend::startBuild(const QString& model_id) {
    const LibraryRow* row = library_model_.findRow(model_id.toStdString());
    if (row == nullptr) return;
    emit buildRequested(fromUtf8(row->entry.id), fromUtf8(row->entry.name), row->current_step,
                        row->entry.step_count);
}

}  // namespace magtile::qtui
