#pragma once

// =============================================================
// MagTile Studio (Qt) - 模型库列表模型
//
// 把 magtile_core 的模型库目录 (core::loadModelCatalog) 连同进度
// 存档状态包装成 QAbstractListModel, 供 QML GridView 直接消费。
// 数据填充由 StudioBackend 负责 (本类只做展示, 不碰磁盘)。
// =============================================================

#include <QAbstractListModel>
#include <QByteArray>
#include <QHash>
#include <QVariant>
#include <vector>

#include "magtile/core/model_catalog.hpp"

namespace magtile::qtui {

/// 一张模型卡片: 目录元数据 + 进度存档合并后的展示状态。
struct LibraryRow {
    core::ModelCatalogEntry entry;
    int current_step = 0;   ///< 进行中时已到第几步 (0 = 未开始)
    int status = 0;         ///< 0 未开始 / 1 进行中 / 2 已完成 (见 Status 枚举)
    bool favorited = false;
};

class LibraryModel final : public QAbstractListModel {
    Q_OBJECT

public:
    /// 卡片状态 (与 LibraryRow::status 对应), QML 侧经 role "status" 读取。
    enum Status { StatusNew = 0, StatusInProgress = 1, StatusCompleted = 2 };
    Q_ENUM(Status)

    enum Role {
        ModelIdRole = Qt::UserRole + 1,
        NameRole,
        NameEnRole,
        DescriptionRole,
        DifficultyRole,
        PiecesRole,
        StepsRole,
        ThemeRole,
        StatusRole,
        CurrentStepRole,
        FavoritedRole,
    };

    explicit LibraryModel(QObject* parent = nullptr);

    [[nodiscard]] int rowCount(const QModelIndex& parent = {}) const override;
    [[nodiscard]] QVariant data(const QModelIndex& index, int role) const override;
    [[nodiscard]] QHash<int, QByteArray> roleNames() const override;

    /// 整体替换数据 (目录重载后调用)。
    void resetRows(std::vector<LibraryRow> rows);
    [[nodiscard]] const std::vector<LibraryRow>& rows() const noexcept { return rows_; }

private:
    std::vector<LibraryRow> rows_;
};

}  // namespace magtile::qtui
