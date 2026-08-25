#include "tts_backend.hpp"

#include <utility>

#include "magtile/core/age_mode.hpp"
#include "magtile/progress/age_settings.hpp"
#include "magtile/progress/ui_settings.hpp"

#if defined(MAGTILE_QT_TTS)
#include <QTextToSpeech>
#endif

namespace magtile::qtui {

TtsBackend::TtsBackend(std::filesystem::path db_file, QObject* parent) : QObject(parent) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(db_file);
        enabled_ = progress::getTtsEnabled(*store_);
    } catch (const progress::ProgressError&) {
        // 存档打不开只影响开关持久化, 朗读本身照常可用 (P3 零挫败)
        store_.reset();
    }

#if defined(MAGTILE_QT_TTS)
    if (!QTextToSpeech::availableEngines().isEmpty()) {
        engine_ = new QTextToSpeech(this);
        connect(engine_, &QTextToSpeech::stateChanged, this, [this](QTextToSpeech::State state) {
            const bool now_speaking = (state == QTextToSpeech::Speaking);
            if (now_speaking != speaking_) {
                speaking_ = now_speaking;
            }
            // 引擎进入 Error 时 available 同步翻转, 界面据此温和降级
            emit stateChanged();
        });
    }
#endif
}

TtsBackend::~TtsBackend() { stop(); }

bool TtsBackend::available() const noexcept {
#if defined(MAGTILE_QT_TTS)
    return engine_ != nullptr;
#else
    return false;
#endif
}

void TtsBackend::setEnabled(bool enabled) {
    if (enabled == enabled_) return;
    enabled_ = enabled;
    if (!enabled) stop();
    if (store_ != nullptr) {
        try {
            progress::setTtsEnabled(*store_, enabled);
        } catch (const progress::ProgressError&) {
            // 落盘失败不打断: 开关仍在本次运行内生效
        }
    }
    emit enabledChanged();
}

bool TtsBackend::autoRead() const {
    if (!enabled_ || !available()) return false;
    // 4-6 岁启蒙模式进入步骤自动朗读 (§4.2); 与 GL 版/CLI 读同一个
    // age_mode 键。每次现读存档: 设置页改年龄段后无需重启即生效。
    if (store_ == nullptr) return false;
    try {
        return progress::getAgeMode(*store_) == core::AgeMode::Age4_6;
    } catch (const progress::ProgressError&) {
        return false;
    }
}

void TtsBackend::speak(const QString& text) {
    if (!enabled_ || text.trimmed().isEmpty()) return;
#if defined(MAGTILE_QT_TTS)
    if (engine_ == nullptr) return;
    engine_->stop();  // 无叠音 (§4.2): 新朗读前先停旧朗读
    engine_->say(text);
#endif
}

void TtsBackend::stop() {
#if defined(MAGTILE_QT_TTS)
    if (engine_ != nullptr) engine_->stop();
#endif
}

}  // namespace magtile::qtui
