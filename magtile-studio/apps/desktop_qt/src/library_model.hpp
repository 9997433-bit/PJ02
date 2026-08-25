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
#include <QString>
#include <QVariant>
#include <map>
#include <string>
#include <vector>

#include "magtile/core/model_catalog.hpp"
#include "magtile/core/types.hpp"

namespace magtile::qtui {

/// 一张模型卡片: 目录元数据 + 进度存档合并后的展示状态。
/// BOM 相关字段 (QT-1) 由 StudioBackend 在 reload 时对照模型 JSON
/// 与磁力片库存一次性算好, 本类只做展示。
struct LibraryRow {
    core::ModelCatalogEntry entry;
    int current_step = 0;   ///< 进行中时已到第几步 (0 = 未开始)
    int status = 0;         ///< 0 未开始 / 1 进行中 / 2 已完成 (见 Status 枚举)
    bool favorited = false;

    bool bom_known = false;   ///< 模型 JSON 成功加载, bom / core9_only 有效
    bool core9_only = false;  ///< BOM 只用核心 9 片型 (基础套装即可搭)
    bool can_build = false;   ///< 库存足够搭建 (未登记库存时恒为 false)
    int missing_total = 0;    ///< 缺片总数 (库存足够或未登记时为 0)
    std::map<core::TileType, int> bom;      ///< 片型 -> 需要数量 (BOM 清单)
    std::map<core::TileType, int> missing;  ///< 片型 -> 缺几片 (对照库存)
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
        Core9OnlyRole,      ///< bool: BOM 只用核心 9 片型
        CanBuildRole,       ///< bool: 库存足够搭建
        MissingTotalRole,   ///< int: 缺片总数
        BomKnownRole,       ///< bool: BOM 数据有效 (模型 JSON 已加载)
    };

    explicit LibraryModel(QObject* parent = nullptr);

    [[nodiscard]] int rowCount(const QModelIndex& parent = {}) const override;
    [[nodiscard]] QVariant data(const QModelIndex& index, int role) const override;
    [[nodiscard]] QHash<int, QByteArray> roleNames() const override;

    /// 整体替换数据 (目录重载后调用)。
    void resetRows(std::vector<LibraryRow> rows);
    [[nodiscard]] const std::vector<LibraryRow>& rows() const noexcept { return rows_; }

    /// 按模型 id 查找卡片; 不存在返回 nullptr (指针仅在下次 resetRows 前有效)。
    [[nodiscard]] const LibraryRow* findRow(const std::string& model_id) const noexcept;

    /// 更新单张卡片的收藏状态并发出 dataChanged (收藏切换后调用)。
    void setFavorited(const std::string& model_id, bool favorited);

private:
    std::vector<LibraryRow> rows_;
};

}  // namespace magtile::qtui
