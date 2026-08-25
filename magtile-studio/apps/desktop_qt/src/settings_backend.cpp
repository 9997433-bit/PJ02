#include "settings_backend.hpp"

#include <QVariantMap>
#include <utility>

#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/ui_settings.hpp"

namespace magtile::qtui {

namespace {

QString fromView(std::string_view s) {
    return QString::fromUtf8(s.data(), static_cast<int>(s.size()));
}

}  // namespace

SettingsBackend::SettingsBackend(std::filesystem::path db_file, QObject* parent)
    : QObject(parent) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(std::move(db_file));
    } catch (const progress::ProgressError&) {
        store_.reset();  // 存档打不开只影响落盘, 设置在本次运行内仍生效
    }
    if (store_) {
        try {
            font_scale_percent_ = progress::getFontScalePercent(*store_);
            reduce_motion_ = progress::getReduceMotion(*store_);
            age_mode_ = progress::getAgeMode(*store_);
            // 首启年龄段引导判定 (QT-5, §10.1): age_mode 键非空 (CLI/GL/
            // 设置页任一处设过) 或已有完成标记, 都视作 "选过了" 不再弹
            age_onboarding_pending_ =
                !store_->getSetting(progress::kAgeModeSettingKey).has_value() &&
                !progress::getAgeOnboardingDone(*store_);
        } catch (const progress::ProgressError&) {
            // 读取失败保持默认值 (读写函数自带脏值兜底, 这里只兜 IO 异常)
        }
    }
}

SettingsBackend::~SettingsBackend() = default;

void SettingsBackend::setFontScalePercent(int percent) {
    if (!progress::isValidFontScalePercent(percent) || percent == font_scale_percent_) return;
    font_scale_percent_ = percent;
    if (store_) {
        try {
            progress::setFontScalePercent(*store_, percent);
        } catch (const progress::ProgressError&) {
            // 内存值已生效, 落盘失败温和降级
        }
    }
    emit settingsChanged();
}

void SettingsBackend::setReduceMotion(bool reduce) {
    if (reduce == reduce_motion_) return;
    reduce_motion_ = reduce;
    if (store_) {
        try {
            progress::setReduceMotion(*store_, reduce);
        } catch (const progress::ProgressError&) {
        }
    }
    emit settingsChanged();
}

QString SettingsBackend::ageModeId() const { return fromView(core::toString(age_mode_)); }

void SettingsBackend::setAgeModeId(const QString& id) {
    const auto mode = core::ageModeFromString(id.toStdString());
    if (!mode.has_value() || *mode == age_mode_) return;  // 未知标识直接忽略
    age_mode_ = *mode;
    if (store_) {
        try {
            progress::setAgeMode(*store_, *mode);
        } catch (const progress::ProgressError&) {
        }
    }
    emit settingsChanged();
}

QString SettingsBackend::ageModeLabel() const { return fromView(core::displayNameZh(age_mode_)); }

void SettingsBackend::resetToDefaults() {
    // 「清除本地数据」后的内存复位: settings 表已整体清空, 只需把
    // 内存快照拉回默认并广播 (Theme/界面绑定即时生效, 等价首次启动)
    font_scale_percent_ = 100;
    reduce_motion_ = false;
    age_mode_ = core::kDefaultAgeMode;
    emit settingsChanged();
}

void SettingsBackend::completeAgeOnboarding(const QString& ageModeId) {
    const auto mode = core::ageModeFromString(ageModeId.toStdString());
    if (!mode.has_value()) return;  // 未知标识忽略: 引导保持待完成
    age_mode_ = *mode;
    age_onboarding_pending_ = false;
    if (store_) {
        try {
            progress::setAgeMode(*store_, *mode);     // age_mode 非空 => 引导今后不再出现
            progress::setAgeOnboardingDone(*store_);  // 完成标记双保险 (ui_settings 契约)
        } catch (const progress::ProgressError&) {
            // 内存态已完成, 本次运行不再打扰; 落盘失败下次启动温和再引导一次
        }
    }
    emit settingsChanged();
}

QVariantList SettingsBackend::ageModeOptions() const {
    QVariantList options;
    for (const core::AgeMode mode :
         {core::AgeMode::Age4_6, core::AgeMode::Age7_9, core::AgeMode::Age10_12}) {
        QVariantMap option;
        option.insert(QStringLiteral("id"), fromView(core::toString(mode)));
        option.insert(QStringLiteral("label"), fromView(core::displayNameZh(mode)));
        options.push_back(option);
    }
    return options;
}

QVariantList SettingsBackend::fontScaleOptions() const {
    static constexpr const char* kLabels[] = {"标准 100%", "大 125%", "特大 150%"};
    QVariantList options;
    int index = 0;
    for (const int percent : progress::kFontScaleTiers) {
        QVariantMap option;
        option.insert(QStringLiteral("percent"), percent);
        option.insert(QStringLiteral("label"), QString::fromUtf8(kLabels[index++]));
        options.push_back(option);
    }
    return options;
}

}  // namespace magtile::qtui
