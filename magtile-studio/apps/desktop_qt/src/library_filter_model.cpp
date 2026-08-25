#include "library_filter_model.hpp"

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
    core9_only_ = false;
    buildable_only_ = false;
    invalidateRowsFilter();
    emit filtersChanged();
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
    if (core9_only_ && !src->data(idx, LibraryModel::Core9OnlyRole).toBool()) {
        return false;
    }
    if (buildable_only_ && !src->data(idx, LibraryModel::CanBuildRole).toBool()) {
        return false;
    }
    return true;
}

}  // namespace magtile::qtui
