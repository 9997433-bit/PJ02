#include "studio_backend.hpp"

#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "magtile/core/json_io.hpp"
#include "magtile/core/model_catalog.hpp"

namespace magtile::qtui {

StudioBackend::StudioBackend(std::filesystem::path data_dir, std::filesystem::path db_file,
                             QObject* parent)
    : QObject(parent), data_dir_(std::move(data_dir)), db_file_(std::move(db_file)) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(db_file_);
    } catch (const progress::ProgressError&) {
        // 存档打不开只影响进度徽标, 模型库照常可浏览 (P3 零挫败)
        store_.reset();
    }
    reload();
}

StudioBackend::~StudioBackend() = default;

void StudioBackend::reload() {
    std::vector<LibraryRow> rows;
    total_pieces_ = 0;
    in_progress_count_ = 0;
    completed_count_ = 0;
    continue_title_.clear();

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

}  // namespace magtile::qtui
