#include "library_filter_model.hpp"

#include <QVariantMap>
#include <algorithm>
#include <vector>

#include "library_model.hpp"

namespace magtile::qtui {

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
        const QModelIndex& idx = buildable[static_cast<std::size_t>(i)];
        QVariantMap item;
        item.insert(QStringLiteral("modelId"), src->data(idx, LibraryModel::ModelIdRole));
        item.insert(QStringLiteral("name"), src->data(idx, LibraryModel::NameRole));
        item.insert(QStringLiteral("difficulty"), src->data(idx, LibraryModel::DifficultyRole));
        item.insert(QStringLiteral("pieces"), src->data(idx, LibraryModel::PiecesRole));
        item.insert(QStringLiteral("theme"), src->data(idx, LibraryModel::ThemeRole));
        recommendations.push_back(item);
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
