#include "studio_backend.hpp"

#include <QDate>
#include <QDateTime>
#include <algorithm>
#include <cstdint>
#include <exception>
#include <map>
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

/// 成就墙徽章档位定义 (QT-4, UI_UX_SPEC.md §4.5: 成就只与搭建行为
/// 挂钩, 按完成模型数分档)。first_model_completed 与完成链路写入
/// 存档的成就 id 同名 (completeBuild / 教程视口 / GL 版三处同一
/// 口径); 其余档位按已完成模型数在展示层判定达成 —— 数据源仍是
/// 同一份进度存档, 不新增写库触发点 (触发统一收口留待成就系统
/// 完整落地, 见 QT_UI_PLAN.md QT-4)。
struct AchievementDef {
    const char* id;
    const char* emoji;
    const char* name;
    const char* condition;    ///< 一句话达成条件 (未解锁时展示, §7.1)
    int completed_threshold;  ///< 达成所需的已完成模型数
};
constexpr AchievementDef kAchievementDefs[] = {
    {"first_model_completed", "🏗️", "首搭达成", "完成第 1 个模型", 1},
    {"three_models_completed", "🏘️", "小小建造家", "完成 3 个模型", 3},
    {"ten_models_completed", "🏰", "建造能手", "完成 10 个模型", 10},
    {"thirty_models_completed", "🌟", "磁力片大师", "完成 30 个模型", 30},
};

/// unix 秒 -> "8月20日" (今年) / "2025年8月20日" (往年); 无记录返回空串。
QString dayText(std::int64_t unix_seconds) {
    if (unix_seconds <= 0) return {};
    const QDateTime t = QDateTime::fromSecsSinceEpoch(unix_seconds);
    return t.toString(t.date().year() == QDate::currentDate().year()
                          ? QStringLiteral("M月d日")
                          : QStringLiteral("yyyy年M月d日"));
}

/// 累计游玩时长 -> "用时 23 分钟" 式温和摘要; 不足 1 分钟返回空串
/// (界面直接隐藏, 不显示 "0 分钟" 这类扫兴数字)。
QString playText(std::int64_t play_seconds) {
    if (play_seconds < 60) return {};
    const std::int64_t minutes = play_seconds / 60;
    if (minutes < 60) return QStringLiteral("用时 %1 分钟").arg(minutes);
    return QStringLiteral("用时 %1 小时 %2 分").arg(minutes / 60).arg(minutes % 60);
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
    free_model_count_ = 0;
    in_progress_count_ = 0;
    completed_count_ = 0;
    favorite_count_ = 0;
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
        // 免费层 (COMMERCIAL_PLAN §2.1): 与 CLI / GL 版同一共享判定
        // core::isFreeTierModel (目录 tags 含「免费」); 非免费模型卡片
        // 显示「订阅解锁」角标, 详情页「开始搭建」改走家长门后的订阅页
        row.is_free = core::isFreeTierModel(row.entry);
        if (row.is_free) ++free_model_count_;

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
        if (row.favorited) ++favorite_count_;
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

    // 已点亮徽章计数 (首页统计卡片 / 成就墙页脚): 与 achievementsList
    // 同一判定 (completed_count_ 已定格, 此处直接复用列表结果)
    achievement_count_ = 0;
    for (const QVariant& badge : achievementsList()) {
        if (badge.toMap().value(QStringLiteral("unlocked")).toBool()) ++achievement_count_;
    }

    if (status_message_.isEmpty()) {
        // 目录缺失/为空不抛异常 (loadModelCatalog 返回空表), 此处按
        // 0 模型给温和的"准备中"文案, 不说"已就绪 0 个"这种自相矛盾话
        // (模型库空态界面配套提供「再试一次」重试入口)
        if (rows.empty()) {
            status_message_ = QStringLiteral("模型库正在准备中 (目录 %1 里暂时没有模型)")
                                  .arg(QString::fromStdString(data_dir_.string()));
        } else {
            status_message_ = QStringLiteral("模型库已就绪: %1 个模型 · 共 %2 片")
                                  .arg(rows.size())
                                  .arg(total_pieces_);
        }
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
        if (row != nullptr && favorited != current) {
            // 收藏计数增量维护 (favoriteCount 属性): 进度页/首页统计即时刷新
            favorite_count_ += favorited ? 1 : -1;
            emit catalogChanged();
        }
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
    detail.insert(QStringLiteral("isFree"), row->is_free);
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
    // 已完成的模型「再搭一次」从头开始 (否则会直接落在最后一步的
    // 完成状态上); 进行中的照旧断点续搭。完成时刻在存档中只增不减,
    // 重搭不会丢掉 ✓ 已完成徽标。
    const int resume_step =
        row->status == LibraryModel::StatusCompleted ? 0 : row->current_step;
    emit buildRequested(fromUtf8(row->entry.id), fromUtf8(row->entry.name), resume_step,
                        row->entry.step_count);
}

void StudioBackend::completeBuild(const QString& model_id) {
    const std::string id = model_id.toStdString();
    const LibraryRow* row = library_model_.findRow(id);
    if (row == nullptr) return;
    // 庆祝页数据先于 reload 定格 (reload 会重建行, row 指针随即失效)
    const QString name = fromUtf8(row->entry.name);
    const int pieces = row->entry.total_pieces;
    const int steps = row->entry.step_count;

    if (store_ != nullptr) {
        try {
            // 与 GL 版完成口径一致 (src/app/main.cpp): 进度推到最后
            // 一步 + 记完成时刻 (首次不覆盖) + 首次完成成就
            store_->saveProgress(id, steps, 0);
            store_->markCompleted(id);
            if (!store_->isAchievementUnlocked("first_model_completed")) {
                store_->unlockAchievement("first_model_completed");
            }
        } catch (const progress::ProgressError&) {
            // 落盘失败不打断庆祝 (P3 零挫败): 完成状态下次会话再补
        }
    }

    reload();  // ✓ 徽标 / 已完成计数 / 「继续上次」即刻刷新
    emit buildCompleted(fromUtf8(id), name, pieces, steps);
}

QString StudioBackend::modelFilePath(const QString& model_id) const {
    const LibraryRow* row = library_model_.findRow(model_id.toStdString());
    if (row == nullptr) return {};
    return QString::fromStdString(row->entry.file.string());
}

QVariantList StudioBackend::achievementsList() const {
    // 存档成就快照 (id -> 首次解锁时刻); 存档不可用/读取失败时按
    // 空处理 (P3 零挫败: 成就墙照常展示, 只是全部未点亮)
    std::map<std::string, std::int64_t> unlocked;
    if (store_ != nullptr) {
        try {
            for (const progress::Achievement& a : store_->listAchievements()) {
                unlocked.emplace(a.id, a.unlocked_at);
            }
        } catch (const progress::ProgressError&) {
        }
    }

    QVariantList list;
    for (const AchievementDef& def : kAchievementDefs) {
        const auto it = unlocked.find(def.id);
        const bool reached = it != unlocked.end() || completed_count_ >= def.completed_threshold;
        QVariantMap item;
        item.insert(QStringLiteral("achievementId"), QString::fromUtf8(def.id));
        item.insert(QStringLiteral("emoji"), QString::fromUtf8(def.emoji));
        item.insert(QStringLiteral("name"), QString::fromUtf8(def.name));
        item.insert(QStringLiteral("condition"), QString::fromUtf8(def.condition));
        item.insert(QStringLiteral("unlocked"), reached);
        QString when;
        if (it != unlocked.end() && it->second > 0) {
            when = QStringLiteral("解锁于 %1").arg(dayText(it->second));
        } else if (reached) {
            when = QStringLiteral("已达成");
        }
        item.insert(QStringLiteral("unlockedText"), when);
        list.append(item);
        if (it != unlocked.end()) unlocked.erase(it);
    }
    // 存档中额外解锁的成就 (未来新增触发点): 通用徽章补列, 永不缺席
    for (const auto& [id, at] : unlocked) {
        QVariantMap item;
        item.insert(QStringLiteral("achievementId"), fromUtf8(id));
        item.insert(QStringLiteral("emoji"), QStringLiteral("🏅"));
        item.insert(QStringLiteral("name"), fromUtf8(id));
        item.insert(QStringLiteral("condition"), QString());
        item.insert(QStringLiteral("unlocked"), true);
        item.insert(QStringLiteral("unlockedText"),
                    at > 0 ? QStringLiteral("解锁于 %1").arg(dayText(at))
                           : QStringLiteral("已达成"));
        list.append(item);
    }
    return list;
}

QVariantList StudioBackend::inProgressList() const {
    QVariantList list;
    if (store_ == nullptr) return list;
    try {
        for (const progress::Progress& p : store_->listInProgress()) {
            const LibraryRow* row = library_model_.findRow(p.model_id);
            // 与首页「继续上次」同口径: 只列已真正开动且仍在库中的模型
            if (row == nullptr || p.current_step <= 0 || p.isCompleted()) continue;
            QVariantMap item;
            item.insert(QStringLiteral("modelId"), fromUtf8(row->entry.id));
            item.insert(QStringLiteral("name"), fromUtf8(row->entry.name));
            item.insert(QStringLiteral("currentStep"), p.current_step);
            item.insert(QStringLiteral("stepCount"), row->entry.step_count);
            item.insert(QStringLiteral("playText"), playText(p.play_seconds));
            list.append(item);
        }
    } catch (const progress::ProgressError&) {
        // 读取失败按空列表处理 (界面显示温和空态)
    }
    return list;
}

QVariantList StudioBackend::completedList() const {
    QVariantList list;
    if (store_ == nullptr) return list;
    try {
        for (const progress::Progress& p : store_->listCompleted()) {
            const LibraryRow* row = library_model_.findRow(p.model_id);
            // 已不在库中的模型不再展示; 完成判定与徽标口径一致 (isCompleted)
            if (row == nullptr || !p.isCompleted()) continue;
            QVariantMap item;
            item.insert(QStringLiteral("modelId"), fromUtf8(row->entry.id));
            item.insert(QStringLiteral("name"), fromUtf8(row->entry.name));
            item.insert(QStringLiteral("pieces"), row->entry.total_pieces);
            QStringList meta;
            if (const QString day = dayText(p.completed_at); !day.isEmpty()) {
                meta << QStringLiteral("%1 完成").arg(day);
            }
            if (const QString play = playText(p.play_seconds); !play.isEmpty()) {
                meta << play;
            }
            item.insert(QStringLiteral("metaText"), meta.join(QStringLiteral(" · ")));
            list.append(item);
        }
    } catch (const progress::ProgressError&) {
    }
    return list;
}

QVariantList StudioBackend::favoritesList() const {
    QVariantList list;
    for (const LibraryRow& row : library_model_.rows()) {
        if (!row.favorited) continue;
        QVariantMap item;
        item.insert(QStringLiteral("modelId"), fromUtf8(row.entry.id));
        item.insert(QStringLiteral("name"), fromUtf8(row.entry.name));
        item.insert(QStringLiteral("status"), row.status);
        list.append(item);
    }
    return list;
}

}  // namespace magtile::qtui
