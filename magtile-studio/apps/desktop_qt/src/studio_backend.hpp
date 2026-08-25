#pragma once

// =============================================================
// MagTile Studio (Qt) - QML 后端桥
//
// Qt 外壳与 magtile_core 之间唯一的桥: 持有模型库目录与进度存档,
// 以 Q_PROPERTY 暴露给 QML (main.cpp 经 context property "studio"
// 注入)。目录 / 存档读取失败不崩溃, 以 statusMessage 温和提示
// (UI_UX_SPEC.md P3 零挫败: 界面上永不弹"失败")。
// =============================================================

#include <QObject>
#include <QString>
#include <filesystem>
#include <memory>

#include "library_model.hpp"
#include "magtile/progress/progress_store.hpp"

namespace magtile::qtui {

class StudioBackend final : public QObject {
    Q_OBJECT
    Q_PROPERTY(magtile::qtui::LibraryModel* libraryModel READ libraryModel CONSTANT)
    Q_PROPERTY(int modelCount READ modelCount NOTIFY catalogChanged)
    Q_PROPERTY(int totalPieces READ totalPieces NOTIFY catalogChanged)
    Q_PROPERTY(int inProgressCount READ inProgressCount NOTIFY catalogChanged)
    Q_PROPERTY(int completedCount READ completedCount NOTIFY catalogChanged)
    Q_PROPERTY(bool hasContinue READ hasContinue NOTIFY catalogChanged)
    Q_PROPERTY(QString continueTitle READ continueTitle NOTIFY catalogChanged)
    Q_PROPERTY(QString statusMessage READ statusMessage NOTIFY catalogChanged)
    Q_PROPERTY(QString dataDirText READ dataDirText NOTIFY catalogChanged)

public:
    StudioBackend(std::filesystem::path data_dir, std::filesystem::path db_file,
                  QObject* parent = nullptr);
    ~StudioBackend() override;

    [[nodiscard]] LibraryModel* libraryModel() noexcept { return &library_model_; }
    [[nodiscard]] int modelCount() const noexcept { return static_cast<int>(library_model_.rows().size()); }
    [[nodiscard]] int totalPieces() const noexcept { return total_pieces_; }
    [[nodiscard]] int inProgressCount() const noexcept { return in_progress_count_; }
    [[nodiscard]] int completedCount() const noexcept { return completed_count_; }
    [[nodiscard]] bool hasContinue() const noexcept { return !continue_title_.isEmpty(); }
    [[nodiscard]] QString continueTitle() const { return continue_title_; }
    [[nodiscard]] QString statusMessage() const { return status_message_; }
    [[nodiscard]] QString dataDirText() const { return QString::fromStdString(data_dir_.string()); }

    /// 重新加载模型库目录并合并进度存档 (构造时自动调用一次)。
    Q_INVOKABLE void reload();

signals:
    void catalogChanged();

private:
    std::filesystem::path data_dir_;
    std::filesystem::path db_file_;
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)

    LibraryModel library_model_;
    int total_pieces_ = 0;
    int in_progress_count_ = 0;
    int completed_count_ = 0;
    QString continue_title_;   ///< "继续上次"卡片文案, 如 "彩虹桥 · 第 3/12 步"
    QString status_message_;   ///< 页脚状态行 (加载结果或温和的降级提示)
};

}  // namespace magtile::qtui
