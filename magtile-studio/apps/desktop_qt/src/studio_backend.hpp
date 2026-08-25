#pragma once

// =============================================================
// MagTile Studio (Qt) - QML 后端桥
//
// Qt 外壳与 magtile_core 之间唯一的桥: 持有模型库目录与进度存档,
// 以 Q_PROPERTY 暴露给 QML (main.cpp 经 context property "studio"
// 注入)。目录 / 存档读取失败不崩溃, 以 statusMessage 温和提示
// (UI_UX_SPEC.md P3 零挫败: 界面上永不弹"失败")。
//
// QT-1 扩展: reload 时逐个加载模型 JSON 计算 BOM, 对照片型目录
// (tile_catalog.json 的 tier) 得出「只用核心 9 片」, 对照磁力片
// 库存 (ProgressStore::getInventory) 得出「我能搭的」与缺片清单;
// 详情页经 modelDetail / bomForModel 读取, 「开始搭建」经
// startBuild 发出 buildRequested 信号 —— QT-3 教程视口就绪后由
// 同一信号路由进真教程, QML 侧路由无需再改。
// =============================================================

#include <QObject>
#include <QString>
#include <QStringList>
#include <QVariantList>
#include <QVariantMap>
#include <filesystem>
#include <map>
#include <memory>
#include <string>

#include "library_filter_model.hpp"
#include "library_model.hpp"
#include "magtile/core/tile_catalog.hpp"
#include "magtile/progress/progress_store.hpp"

namespace magtile::qtui {

class StudioBackend final : public QObject {
    Q_OBJECT
    Q_PROPERTY(magtile::qtui::LibraryModel* libraryModel READ libraryModel CONSTANT)
    Q_PROPERTY(magtile::qtui::LibraryFilterModel* libraryFilter READ libraryFilter CONSTANT)
    Q_PROPERTY(int modelCount READ modelCount NOTIFY catalogChanged)
    Q_PROPERTY(int totalPieces READ totalPieces NOTIFY catalogChanged)
    Q_PROPERTY(int inProgressCount READ inProgressCount NOTIFY catalogChanged)
    Q_PROPERTY(int completedCount READ completedCount NOTIFY catalogChanged)
    Q_PROPERTY(bool hasContinue READ hasContinue NOTIFY catalogChanged)
    Q_PROPERTY(QString continueTitle READ continueTitle NOTIFY catalogChanged)
    Q_PROPERTY(QString continueModelId READ continueModelId NOTIFY catalogChanged)
    Q_PROPERTY(QString statusMessage READ statusMessage NOTIFY catalogChanged)
    Q_PROPERTY(QString dataDirText READ dataDirText NOTIFY catalogChanged)
    /// 进度存档数据库路径 (QT-3 教程视口共用同一 SQLite)。
    Q_PROPERTY(QString dbFileText READ dbFileText CONSTANT)
    /// 家庭磁力片库存是否已登记 (未登记时「我能搭的」筛选由界面禁用并引导)。
    Q_PROPERTY(bool inventoryConfigured READ inventoryConfigured NOTIFY catalogChanged)
    /// 免费层模型数 (目录 tags 含「免费」, COMMERCIAL_PLAN.md §2.1 免费 30):
    /// 订阅页 (QT-5) 的「免费 vs 全库」对比数据源, 与 QA 红线工具同一口径。
    Q_PROPERTY(int freeModelCount READ freeModelCount NOTIFY catalogChanged)
    /// 全部主题 (按目录出现顺序去重), 主题筛选器数据源。
    Q_PROPERTY(QStringList themes READ themes NOTIFY catalogChanged)
    /// 收藏的模型数 (QT-4 进度页「我的收藏」与首页温和统计卡片)。
    Q_PROPERTY(int favoriteCount READ favoriteCount NOTIFY catalogChanged)
    /// 已点亮的成就徽章数 (QT-4 成就墙, 判定口径同 achievementsList)。
    Q_PROPERTY(int achievementCount READ achievementCount NOTIFY catalogChanged)

public:
    StudioBackend(std::filesystem::path data_dir, std::filesystem::path db_file,
                  QObject* parent = nullptr);
    ~StudioBackend() override;

    [[nodiscard]] LibraryModel* libraryModel() noexcept { return &library_model_; }
    [[nodiscard]] LibraryFilterModel* libraryFilter() noexcept { return &library_filter_; }
    [[nodiscard]] int modelCount() const noexcept { return static_cast<int>(library_model_.rows().size()); }
    [[nodiscard]] int totalPieces() const noexcept { return total_pieces_; }
    [[nodiscard]] int inProgressCount() const noexcept { return in_progress_count_; }
    [[nodiscard]] int completedCount() const noexcept { return completed_count_; }
    [[nodiscard]] bool hasContinue() const noexcept { return !continue_title_.isEmpty(); }
    [[nodiscard]] QString continueTitle() const { return continue_title_; }
    [[nodiscard]] QString continueModelId() const { return continue_model_id_; }
    [[nodiscard]] QString statusMessage() const { return status_message_; }
    [[nodiscard]] QString dataDirText() const { return QString::fromStdString(data_dir_.string()); }
    [[nodiscard]] QString dbFileText() const { return QString::fromStdString(db_file_.string()); }
    [[nodiscard]] bool inventoryConfigured() const noexcept { return inventory_configured_; }
    [[nodiscard]] int freeModelCount() const noexcept { return free_model_count_; }
    [[nodiscard]] QStringList themes() const { return themes_; }
    [[nodiscard]] int favoriteCount() const noexcept { return favorite_count_; }
    [[nodiscard]] int achievementCount() const noexcept { return achievement_count_; }

    /// 重新加载模型库目录并合并进度存档 (构造时自动调用一次)。
    Q_INVOKABLE void reload();

    /// 切换收藏状态并更新卡片; 返回切换后的状态 (存档不可用时状态不变)。
    Q_INVOKABLE bool toggleFavorite(const QString& model_id);

    /// 模型详情页数据快照 (键: found/modelId/name/nameEn/description/
    /// difficulty/pieces/steps/theme/status/currentStep/favorited/
    /// bomKnown/core9Only/canBuild/missingTotal/missingText)。
    /// 模型不存在时只含 found=false。
    Q_INVOKABLE QVariantMap modelDetail(const QString& model_id) const;

    /// 模型 BOM 清单 (详情页 §5.4): 每项 {shapeName, needed, have,
    /// missing, isCore}; have/missing 仅在库存已登记时有意义。
    Q_INVOKABLE QVariantList bomForModel(const QString& model_id) const;

    /// 「开始搭建」入口: 发出 buildRequested 供路由层跳转教程。
    /// QT-3 之前由 Main.qml 路由到占位 TutorialPage; 视口就绪后同一
    /// 信号改接真 3D 教程, 详情页与路由契约不变。
    Q_INVOKABLE void startBuild(const QString& model_id);

    /// 教程完成入口 (QT-4): 写存档完成状态 (进度推到最后一步 +
    /// markCompleted + 首次完成成就, 与 GL 版同一口径), 刷新模型库
    /// 徽标, 再发 buildCompleted 供 Main.qml 路由到完成庆祝页。
    /// QT-3 视口就绪前由占位教程页「模拟完成」按钮触发 (冒烟),
    /// 就绪后由视口 finished 状态触发, 信号契约不变。
    Q_INVOKABLE void completeBuild(const QString& model_id);

    /// 模型 JSON 文件路径 (QT-3 教程视口按需加载模型本体用);
    /// 未知模型返回空串 (视口温和降级)。
    Q_INVOKABLE QString modelFilePath(const QString& model_id) const;

    // ---- 进度页 / 成就墙数据 (QT-4, UI_UX_SPEC.md §7) -----------------

    /// 成就墙徽章列表: 每项 {achievementId, emoji, name, condition,
    /// unlocked, unlockedText}。徽章档位只与搭建行为挂钩 (§4.5, 按
    /// 完成模型数); 未解锁项由界面按灰色剪影 + 一句话达成条件展示
    /// (不显示进度百分比, §7.1 防焦虑)。存档中额外解锁的成就 id
    /// (未来新增触发点) 以通用徽章补列在末尾, 永不缺席。
    Q_INVOKABLE QVariantList achievementsList() const;

    /// 进行中作品列表 (按最近游玩倒序): 每项 {modelId, name,
    /// currentStep, stepCount, playText}; 只列已真正开动 (step > 0)
    /// 且仍在库中的模型, 与首页「继续上次」同口径。
    Q_INVOKABLE QVariantList inProgressList() const;

    /// 已完成作品列表 (按完成时间倒序): 每项 {modelId, name, pieces,
    /// metaText}; metaText 为 "8月20日 完成 · 用时 23 分钟" 式摘要。
    Q_INVOKABLE QVariantList completedList() const;

    /// 收藏的模型列表 (按目录顺序): 每项 {modelId, name, status}
    /// (status 同 LibraryModel::Status)。
    Q_INVOKABLE QVariantList favoritesList() const;

signals:
    void catalogChanged();
    /// 「开始搭建」请求 (current_step: 0 = 从头开始, >0 = 从断点继续)。
    void buildRequested(const QString& modelId, const QString& modelName, int currentStep,
                        int stepCount);
    /// 教程完成 (QT-4): Main.qml 据此路由到完成庆祝页 (§6.2)。
    void buildCompleted(const QString& modelId, const QString& modelName, int pieces,
                        int stepCount);

private:
    /// 片型是否属于核心 9 片 (基础套装): 以 data/tile_catalog.json 的
    /// tier 标注为准, 目录不可用时退回代码内白名单 (两处必须一致)。
    [[nodiscard]] bool isCoreTile(core::TileType type) const;
    /// 片型中文名: 片型目录的 name_zh 优先, 缺省退回 core::displayNameZh。
    [[nodiscard]] QString shapeNameZh(core::TileType type) const;
    /// 缺片提示文案, 如 "缺 4 片正方形、2 片长方形"; 不缺时为空串。
    [[nodiscard]] QString missingText(const LibraryRow& row) const;

    std::filesystem::path data_dir_;
    std::filesystem::path db_file_;
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)

    LibraryModel library_model_;
    LibraryFilterModel library_filter_;
    core::TileCatalog tile_catalog_;
    bool tile_catalog_loaded_ = false;
    std::map<core::TileType, int> inventory_;  ///< 已登记库存快照 (按片型)
    bool inventory_configured_ = false;
    QStringList themes_;
    int total_pieces_ = 0;
    int free_model_count_ = 0;
    int in_progress_count_ = 0;
    int completed_count_ = 0;
    int favorite_count_ = 0;      ///< 收藏的模型数 (reload 统计, 收藏切换时增量维护)
    int achievement_count_ = 0;   ///< 已点亮徽章数 (判定口径同 achievementsList)
    QString continue_title_;      ///< "继续上次"卡片文案, 如 "彩虹桥 · 第 3/12 步"
    QString continue_model_id_;   ///< "继续上次"对应的模型 id (直达详情/教程)
    QString status_message_;      ///< 页脚状态行 (加载结果或温和的降级提示)
};

}  // namespace magtile::qtui
