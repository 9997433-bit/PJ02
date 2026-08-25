#pragma once

// =============================================================
// MagTile Studio (Qt) - 磁力片库存录入后端桥
//
// InventoryPage.qml 与 magtile_core 库存 API 之间的桥: 读写
// ProgressStore 的 tile_inventory 表 (与 CLI `inventory set` /
// GL 版录入界面共用同一 SQLite, docs/UI_UX_SPEC.md §10)。
// 独立于 StudioBackend, 保存后由 QML 调 studio.reload() 刷新
// 「我能搭的」徽标与筛选 (SQLite 同库多连接安全)。
// 存档打不开只降级不崩溃 (P3 零挫败): save 返回 false, 界面照常
// 可浏览片型清单。
// =============================================================

#include <QObject>
#include <QVariantList>
#include <QVariantMap>
#include <filesystem>
#include <memory>

#include "magtile/core/tile_catalog.hpp"
#include "magtile/progress/progress_store.hpp"

namespace magtile::qtui {

class InventoryBackend final : public QObject {
    Q_OBJECT
    /// 是否已登记过库存 (含 0 数量的 "明确没有"; onboarding 判定)。
    Q_PROPERTY(bool configured READ configured NOTIFY inventoryChanged)
    /// 已登记的磁力片总数。
    Q_PROPERTY(int totalCount READ totalCount NOTIFY inventoryChanged)

public:
    InventoryBackend(std::filesystem::path data_dir, std::filesystem::path db_file,
                     QObject* parent = nullptr);
    ~InventoryBackend() override;

    [[nodiscard]] bool configured() const;
    [[nodiscard]] int totalCount() const;

    /// 全部片型一行一项 (录入界面数据源), 按 TileType 枚举顺序
    /// (核心 9 片型在前): {shapeId, nameZh, expansion, count}。
    /// 中文名与 core/expansion 分层以 data/tile_catalog.json 为准,
    /// 目录不可用时退回 core::displayNameZh 与枚举位置。
    Q_INVOKABLE QVariantList rows() const;

    /// 保存库存 (shapeId -> count 的完整快照): 数量夹到 [0, 999],
    /// 未知片型标识跳过。成功返回 true 并发 inventoryChanged;
    /// 存档不可用或写入失败返回 false (界面温和提示, 不弹"失败")。
    Q_INVOKABLE bool save(const QVariantMap& counts);

signals:
    void inventoryChanged();

private:
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)
    core::TileCatalog tile_catalog_;
    bool tile_catalog_loaded_ = false;
};

}  // namespace magtile::qtui
