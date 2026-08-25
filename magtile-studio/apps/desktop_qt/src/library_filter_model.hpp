#pragma once

// =============================================================
// MagTile Studio (Qt) - 模型库筛选代理 (QT-1)
//
// 包在 LibraryModel 外面的 QSortFilterProxyModel: 难度 / 主题 /
// 「免费模型」(免费层标签) /「只用核心 9 片」/「我能搭的」(对照
// 磁力片库存的 canBuild) 五个筛选维度, 对应 UI_UX_SPEC.md §5.1
// 侧栏。筛选条件由 QML 侧直接读写属性; 数据角色 (isFree /
// core9Only / canBuild) 由 StudioBackend 在 reload 时算好, 本类
// 只做行过滤, 不碰磁盘。
// =============================================================

#include <QSortFilterProxyModel>
#include <QString>
#include <QVariantList>

namespace magtile::qtui {

class LibraryFilterModel final : public QSortFilterProxyModel {
    Q_OBJECT
    /// 难度筛选: 0 = 全部, 1~5 = 只看对应星级。
    Q_PROPERTY(int difficulty READ difficulty WRITE setDifficulty NOTIFY filtersChanged)
    /// 主题筛选: 空串 = 全部, 否则精确匹配卡片主题。
    Q_PROPERTY(QString theme READ theme WRITE setTheme NOTIFY filtersChanged)
    /// 「免费模型」: 只看免费层 (目录 tags 含「免费」, COMMERCIAL_PLAN §2.1)。
    Q_PROPERTY(bool freeOnly READ freeOnly WRITE setFreeOnly NOTIFY filtersChanged)
    /// 只看基础套装 (核心 9 片型) 就能搭的模型。
    Q_PROPERTY(bool core9Only READ core9Only WRITE setCore9Only NOTIFY filtersChanged)
    /// 「我能搭的」: 只看磁力片库存足够的模型 (未登记库存时由界面禁用)。
    Q_PROPERTY(bool buildableOnly READ buildableOnly WRITE setBuildableOnly NOTIFY filtersChanged)
    /// 是否有任一筛选条件生效 (空态文案与「清除筛选」按钮用)。
    Q_PROPERTY(bool hasActiveFilters READ hasActiveFilters NOTIFY filtersChanged)
    /// 筛选后的卡片数 (QML 空态判定用)。
    Q_PROPERTY(int count READ count NOTIFY countChanged)

public:
    explicit LibraryFilterModel(QObject* parent = nullptr);

    [[nodiscard]] int difficulty() const noexcept { return difficulty_; }
    void setDifficulty(int difficulty);

    [[nodiscard]] QString theme() const { return theme_; }
    void setTheme(const QString& theme);

    [[nodiscard]] bool freeOnly() const noexcept { return free_only_; }
    void setFreeOnly(bool on);

    [[nodiscard]] bool core9Only() const noexcept { return core9_only_; }
    void setCore9Only(bool on);

    [[nodiscard]] bool buildableOnly() const noexcept { return buildable_only_; }
    void setBuildableOnly(bool on);

    [[nodiscard]] bool hasActiveFilters() const noexcept {
        return difficulty_ != 0 || !theme_.isEmpty() || free_only_ || core9_only_ ||
               buildable_only_;
    }

    [[nodiscard]] int count() const { return rowCount(); }

    /// 一键回到「全部」(空态页「换个条件试试」按钮)。
    Q_INVOKABLE void clearFilters();

    /// 「我能搭的」筛选空态推荐 (UI_UX_SPEC.md §5.2): 无视其他筛选
    /// 条件, 从全部卡片中挑库存足够搭建 (canBuild) 的模型, 按难度
    /// 升序 (同难度片数少者优先) 取前 max_count 个。每项含
    /// {modelId, name, difficulty, pieces, theme}; 未登记库存或
    /// 没有可搭模型时返回空列表 (界面退回普通空态文案)。
    Q_INVOKABLE QVariantList recommendBuildable(int max_count) const;

signals:
    void filtersChanged();
    void countChanged();

protected:
    [[nodiscard]] bool filterAcceptsRow(int source_row,
                                        const QModelIndex& source_parent) const override;

private:
    int difficulty_ = 0;
    QString theme_;
    bool free_only_ = false;
    bool core9_only_ = false;
    bool buildable_only_ = false;
};

}  // namespace magtile::qtui
