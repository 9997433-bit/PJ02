#pragma once

// =============================================================
// MagTile Studio (Qt) - 步骤朗读后端桥 (QT-4, UI_UX_SPEC.md §4.2)
//
// QtTextToSpeech 统一封装系统语音引擎 (Windows SAPI / macOS
// AVSpeech / Linux speech-dispatcher), 不引入第三方语音 SDK
// (SECURITY_AND_PRIVACY.md §5)。构建时未找到 Qt6TextToSpeech
// 模块 (未定义 MAGTILE_QT_TTS) 或运行时无可用引擎则静默降级
// (available=false), 界面温和提示, 永不弹"失败" (P3 零挫败)。
//
// 朗读语义与 GL 版 tts::ITtsEngine 一致: speak 先停旧朗读,
// 切步/退出即打断, 保证无叠音 (§4.2)。
//
// 开关持久化契约: 总开关经 progress/ui_settings 的
// kTtsEnabledSettingKey ("tts_enabled") 落 ProgressStore settings
// 表 —— 设置页开关直接绑本类 enabled 属性 (enabledChanged 全应用
// 即时生效), 与 GL 版 / CLI 共用同一键名。自动朗读 (autoRead) 只在
// 4-6 岁启蒙模式下开启 (读 age_mode 键, 与 GL 版/CLI 同一口径),
// 其余年龄段由教程页眉 🔊 按钮手动触发。
// =============================================================

#include <QObject>
#include <QString>
#include <filesystem>
#include <memory>

#include "magtile/progress/progress_store.hpp"

#if defined(MAGTILE_QT_TTS)
class QTextToSpeech;
#endif

namespace magtile::qtui {

class TtsBackend final : public QObject {
    Q_OBJECT
    /// 系统语音引擎是否可用 (构建缺模块或运行时无引擎时 false, 静默降级)。
    Q_PROPERTY(bool available READ available NOTIFY stateChanged)
    /// 朗读总开关 (家长设置项, 持久化 "tts_enabled"; 默认开)。
    Q_PROPERTY(bool enabled READ enabled WRITE setEnabled NOTIFY enabledChanged)
    /// 是否自动朗读步骤说明: 总开关开 且 4-6 岁启蒙模式 (§4.2)。
    Q_PROPERTY(bool autoRead READ autoRead NOTIFY enabledChanged)
    /// 正在朗读中 (🔊 按钮波形动画数据源)。
    Q_PROPERTY(bool speaking READ speaking NOTIFY stateChanged)

public:
    explicit TtsBackend(std::filesystem::path db_file, QObject* parent = nullptr);
    ~TtsBackend() override;

    [[nodiscard]] bool available() const noexcept;
    [[nodiscard]] bool enabled() const noexcept { return enabled_; }
    void setEnabled(bool enabled);
    [[nodiscard]] bool autoRead() const;
    [[nodiscard]] bool speaking() const noexcept { return speaking_; }

    /// 朗读一段文字: 先停旧朗读 (无叠音 §4.2); 开关关闭或引擎
    /// 不可用时静默返回 (不弹错误)。
    Q_INVOKABLE void speak(const QString& text);

    /// 立即停止朗读 (切步 / 退出教程页时调用, 幂等)。
    Q_INVOKABLE void stop();

signals:
    void enabledChanged();
    void stateChanged();

private:
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)
    bool enabled_ = true;   ///< 内存快照: 存档不可用时开关仍在本次运行内生效
    bool speaking_ = false;
#if defined(MAGTILE_QT_TTS)
    QTextToSpeech* engine_ = nullptr;  ///< 子对象随本类析构; 无可用引擎时为空
#endif
};

}  // namespace magtile::qtui
