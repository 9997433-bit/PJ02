#pragma once

// =============================================================
// MagTile Studio (Qt) - 设置页后端桥
//
// SettingsPage.qml 与 ProgressStore settings 表之间的桥: 字号三档
// 与减少动效 (progress/ui_settings) + 年龄段模式 (progress/
// age_settings) 的类型化读写 —— 与 GL 版 / CLI (`settings
// set-age`) 共用同一 SQLite 存档与键名契约 (UI_UX_SPEC.md §8)。
// 独立于 StudioBackend (SQLite 同库多连接安全)。存档打不开只降级
// 不崩溃 (P3 零挫败): 设置仍在当前运行内生效, 只是不落盘, 界面
// 据 storeAvailable 温和提示。
// =============================================================

#include <QObject>
#include <QString>
#include <QVariantList>
#include <filesystem>
#include <memory>

#include "magtile/core/age_mode.hpp"
#include "magtile/progress/progress_store.hpp"

namespace magtile::qtui {

class SettingsBackend final : public QObject {
    Q_OBJECT
    /// 字号缩放档位: 100 / 125 / 150 (%) (UI_UX_SPEC.md §4.7 三档)。
    Q_PROPERTY(int fontScalePercent READ fontScalePercent WRITE setFontScalePercent
                   NOTIFY settingsChanged)
    /// 减少动效 (开启后全应用动效时长归零)。
    Q_PROPERTY(bool reduceMotion READ reduceMotion WRITE setReduceMotion NOTIFY settingsChanged)
    /// 年龄段模式持久化标识 ("age_4_6" / "age_7_9" / "age_10_12"),
    /// 与 CLI `settings set-age` / GL 版启蒙布局读的是同一个键。
    Q_PROPERTY(QString ageModeId READ ageModeId WRITE setAgeModeId NOTIFY settingsChanged)
    /// 当前年龄段的中文展示名, 如 "7-9 岁 · 标准模式"。
    Q_PROPERTY(QString ageModeLabel READ ageModeLabel NOTIFY settingsChanged)
    /// 存档是否可用 (不可用时界面温和提示 "本次调整只在这次运行内有效")。
    Q_PROPERTY(bool storeAvailable READ storeAvailable CONSTANT)

public:
    explicit SettingsBackend(std::filesystem::path db_file, QObject* parent = nullptr);
    ~SettingsBackend() override;

    [[nodiscard]] int fontScalePercent() const noexcept { return font_scale_percent_; }
    void setFontScalePercent(int percent);
    [[nodiscard]] bool reduceMotion() const noexcept { return reduce_motion_; }
    void setReduceMotion(bool reduce);
    [[nodiscard]] QString ageModeId() const;
    void setAgeModeId(const QString& id);
    [[nodiscard]] QString ageModeLabel() const;
    [[nodiscard]] bool storeAvailable() const noexcept { return store_ != nullptr; }

    /// 年龄段三档选项 (设置页数据源): {id, label} 按启蒙/标准/进阶顺序。
    Q_INVOKABLE QVariantList ageModeOptions() const;

    /// 字号三档选项 (设置页数据源): {percent, label}, 如 {125, "大 125%"}。
    Q_INVOKABLE QVariantList fontScaleOptions() const;

signals:
    void settingsChanged();

private:
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)

    // 内存快照: 存档不可用时设置仍在当前运行内生效 (P3 零挫败)
    int font_scale_percent_ = 100;
    bool reduce_motion_ = false;
    core::AgeMode age_mode_ = core::kDefaultAgeMode;
};

}  // namespace magtile::qtui
