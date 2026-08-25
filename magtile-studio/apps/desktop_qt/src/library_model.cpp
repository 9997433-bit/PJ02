#include "library_model.hpp"

#include <QString>
#include <utility>

namespace magtile::qtui {

namespace {

QString fromUtf8(const std::string& s) { return QString::fromUtf8(s.c_str(), static_cast<int>(s.size())); }

}  // namespace

LibraryModel::LibraryModel(QObject* parent) : QAbstractListModel(parent) {}

int LibraryModel::rowCount(const QModelIndex& parent) const {
    return parent.isValid() ? 0 : static_cast<int>(rows_.size());
}

QVariant LibraryModel::data(const QModelIndex& index, int role) const {
    if (!index.isValid() || index.row() < 0 || index.row() >= static_cast<int>(rows_.size())) {
        return {};
    }
    const LibraryRow& row = rows_[static_cast<std::size_t>(index.row())];
    const core::ModelCatalogEntry& e = row.entry;
    switch (role) {
        case ModelIdRole: return fromUtf8(e.id);
        case NameRole: return fromUtf8(e.name);
        case NameEnRole: return fromUtf8(e.name_en);
        case DescriptionRole: return fromUtf8(e.description);
        case DifficultyRole: return e.difficulty;
        case PiecesRole: return e.total_pieces;
        case StepsRole: return e.step_count;
        case ThemeRole: return fromUtf8(e.theme());
        case StatusRole: return row.status;
        case CurrentStepRole: return row.current_step;
        case FavoritedRole: return row.favorited;
        case Core9OnlyRole: return row.core9_only;
        case CanBuildRole: return row.can_build;
        case MissingTotalRole: return row.missing_total;
        case BomKnownRole: return row.bom_known;
        default: return {};
    }
}

QHash<int, QByteArray> LibraryModel::roleNames() const {
    return {
        {ModelIdRole, "modelId"},
        {NameRole, "name"},
        {NameEnRole, "nameEn"},
        {DescriptionRole, "description"},
        {DifficultyRole, "difficulty"},
        {PiecesRole, "pieces"},
        {StepsRole, "steps"},
        {ThemeRole, "theme"},
        {StatusRole, "status"},
        {CurrentStepRole, "currentStep"},
        {FavoritedRole, "favorited"},
        {Core9OnlyRole, "core9Only"},
        {CanBuildRole, "canBuild"},
        {MissingTotalRole, "missingTotal"},
        {BomKnownRole, "bomKnown"},
    };
}

void LibraryModel::resetRows(std::vector<LibraryRow> rows) {
    beginResetModel();
    rows_ = std::move(rows);
    endResetModel();
}

const LibraryRow* LibraryModel::findRow(const std::string& model_id) const noexcept {
    for (const LibraryRow& row : rows_) {
        if (row.entry.id == model_id) return &row;
    }
    return nullptr;
}

void LibraryModel::setFavorited(const std::string& model_id, bool favorited) {
    for (std::size_t i = 0; i < rows_.size(); ++i) {
        if (rows_[i].entry.id != model_id) continue;
        if (rows_[i].favorited == favorited) return;
        rows_[i].favorited = favorited;
        const QModelIndex idx = index(static_cast<int>(i));
        emit dataChanged(idx, idx, {FavoritedRole});
        return;
    }
}

}  // namespace magtile::qtui
