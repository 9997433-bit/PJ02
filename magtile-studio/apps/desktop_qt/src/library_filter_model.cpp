#include "library_filter_model.hpp"

#include <QVariantMap>
#include <algorithm>
#include <cstdlib>
#include <vector>

#include "library_model.hpp"

namespace magtile::qtui {
namespace {

/// 推荐卡片数据快照 (recommendBuildable / recommendSimilar 共用键)。
QVariantMap recommendationItem(const QAbstractItemModel* src, const QModelIndex& idx) {
    QVariantMap item;
    item.insert(QStringLiteral("modelId"), src->data(idx, LibraryModel::ModelIdRole));
    item.insert(QStringLiteral("name"), src->data(idx, LibraryModel::NameRole));
    item.insert(QStringLiteral("difficulty"), src->data(idx, LibraryModel::DifficultyRole));
    item.insert(QStringLiteral("pieces"), src->data(idx, LibraryModel::PiecesRole));
    item.insert(QStringLiteral("theme"), src->data(idx, LibraryModel::ThemeRole));
    return item;
}

}  // namespace

LibraryFilterModel::LibraryFilterModel(QObject* parent) : QSortFilterProxyModel(parent) {
    // 筛选结果行数变化的全部途径都汇到 countChanged, 供 QML 空态判定
    connect(this, &QAbstractItemModel::rowsInserted, this, &LibraryFilterModel::countChanged);
    connect(this, &QAbstractItemModel::rowsRemoved, this, &LibraryFilterModel::countChanged);
    connect(this, &QAbstractItemModel::modelReset, this, &LibraryFilterModel::countChanged);
    connect(this, &QAbstractItemModel::layoutChanged, this, &LibraryFilterModel::countChanged);
}

void LibraryFilterModel::setDifficulty(int difficulty) {
    if (difficulty_ == difficulty) return;
    difficulty_ = difficulty;
    invalidateRowsFilter();
    emit filtersChanged();
}

void LibraryFilterModel::setTheme(const QString& theme) {
    if (theme_ == theme) return;
    theme_ = theme;
    invalidateRowsFilter();
    emit filtersChanged();
}

void LibraryFilterModel::setFreeOnly(bool on) {
    if (free_only_ == on) return;
    free_only_ = on;
    invalidateRowsFilter();
    emit filtersChanged();
}

void LibraryFilterModel::setCore9Only(bool on) {
    if (core9_only_ == on) return;
    core9_only_ = on;
    invalidateRowsFilter();
    emit filtersChanged();
}

void LibraryFilterModel::setBuildableOnly(bool on) {
    if (buildable_only_ == on) return;
    buildable_only_ = on;
    invalidateRowsFilter();
    emit filtersChanged();
}

void LibraryFilterModel::setSubscriptionActive(bool active) {
    if (subscription_active_ == active) return;
    subscription_active_ = active;
    // 只影响 recommendSimilar 的排除口径, 行过滤不依赖订阅状态
    emit subscriptionActiveChanged();
}

void LibraryFilterModel::clearFilters() {
    if (!hasActiveFilters()) return;
    difficulty_ = 0;
    theme_.clear();
    free_only_ = false;
    core9_only_ = false;
    buildable_only_ = false;
    invalidateRowsFilter();
    emit filtersChanged();
}

QVariantList LibraryFilterModel::recommendBuildable(int max_count) const {
    QVariantList recommendations;
    const QAbstractItemModel* src = sourceModel();
    if (src == nullptr || max_count <= 0) return recommendations;

    // canBuild 在未登记库存时恒为 false (StudioBackend::reload 口径),
    // 所以未登记库存时这里自然返回空列表
    std::vector<QModelIndex> buildable;
    for (int row = 0; row < src->rowCount(); ++row) {
        const QModelIndex idx = src->index(row, 0);
        if (src->data(idx, LibraryModel::CanBuildRole).toBool()) {
            buildable.push_back(idx);
        }
    }
    std::stable_sort(buildable.begin(), buildable.end(),
                     [src](const QModelIndex& a, const QModelIndex& b) {
                         const int diff_a = src->data(a, LibraryModel::DifficultyRole).toInt();
                         const int diff_b = src->data(b, LibraryModel::DifficultyRole).toInt();
                         if (diff_a != diff_b) return diff_a < diff_b;
                         return src->data(a, LibraryModel::PiecesRole).toInt() <
                                src->data(b, LibraryModel::PiecesRole).toInt();
                     });

    const int count = std::min(max_count, static_cast<int>(buildable.size()));
    for (int i = 0; i < count; ++i) {
        recommendations.push_back(
            recommendationItem(src, buildable[static_cast<std::size_t>(i)]));
    }
    return recommendations;
}

QVariantList LibraryFilterModel::recommendSimilar(const QString& model_id,
                                                  int max_count) const {
    QVariantList recommendations;
    const QAbstractItemModel* src = sourceModel();
    if (src == nullptr || max_count <= 0) return recommendations;

    // 刚完成模型的难度作为「相近」基准; 目录中找不到 (极端: 目录热更
    // 后被下架) 时 has_base=false, 排序退回难度升序口径
    int base_difficulty = 0;
    bool has_base = false;
    std::vector<QModelIndex> candidates;
    for (int row = 0; row < src->rowCount(); ++row) {
        const QModelIndex idx = src->index(row, 0);
        if (src->data(idx, LibraryModel::ModelIdRole).toString() == model_id) {
            base_difficulty = src->data(idx, LibraryModel::DifficultyRole).toInt();
            has_base = true;
            continue;  // 刚完成的模型自身不进推荐
        }
        if (!src->data(idx, LibraryModel::CanBuildRole).toBool()) continue;
        // 庆祝页点卡直接开搭 (startBuild 无订阅拦截), 未解锁的订阅内容
        // 在此拦下 (§11); 订阅生效后与免费层同权进推荐 (计费适配层口径)
        if (!subscription_active_ && !src->data(idx, LibraryModel::FreeRole).toBool()) continue;
        candidates.push_back(idx);
    }

    std::stable_sort(
        candidates.begin(), candidates.end(),
        [src, base_difficulty, has_base](const QModelIndex& a, const QModelIndex& b) {
            const int diff_a = src->data(a, LibraryModel::DifficultyRole).toInt();
            const int diff_b = src->data(b, LibraryModel::DifficultyRole).toInt();
            if (has_base) {
                // 同难度最先、±1 次之, 候选不足时距离更远的自然垫后 (放宽难度)
                const int dist_a = std::abs(diff_a - base_difficulty);
                const int dist_b = std::abs(diff_b - base_difficulty);
                if (dist_a != dist_b) return dist_a < dist_b;
            }
            // 同距离取更轻松的一档 (P3 零挫败), 同难度片数少者优先
            if (diff_a != diff_b) return diff_a < diff_b;
            return src->data(a, LibraryModel::PiecesRole).toInt() <
                   src->data(b, LibraryModel::PiecesRole).toInt();
        });

    const int count = std::min(max_count, static_cast<int>(candidates.size()));
    for (int i = 0; i < count; ++i) {
        recommendations.push_back(
            recommendationItem(src, candidates[static_cast<std::size_t>(i)]));
    }
    return recommendations;
}

bool LibraryFilterModel::filterAcceptsRow(int source_row,
                                          const QModelIndex& source_parent) const {
    const QAbstractItemModel* src = sourceModel();
    if (src == nullptr) return true;
    const QModelIndex idx = src->index(source_row, 0, source_parent);

    if (difficulty_ != 0 && src->data(idx, LibraryModel::DifficultyRole).toInt() != difficulty_) {
        return false;
    }
    if (!theme_.isEmpty() && src->data(idx, LibraryModel::ThemeRole).toString() != theme_) {
        return false;
    }
    if (free_only_ && !src->data(idx, LibraryModel::FreeRole).toBool()) {
        return false;
    }
    if (core9_only_ && !src->data(idx, LibraryModel::Core9OnlyRole).toBool()) {
        return false;
    }
    if (buildable_only_ && !src->data(idx, LibraryModel::CanBuildRole).toBool()) {
        return false;
    }
    return true;
}

}  // namespace magtile::qtui
