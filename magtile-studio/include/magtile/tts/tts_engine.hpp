#pragma once

// =============================================================
// MagTile Studio - TTS 语音朗读引擎 (商用 stub)
//
// UI_UX_SPEC.md §4.2: 每条步骤说明可朗读; 4-6 岁启蒙模式进入
// 步骤自动朗读; 切换步骤自动停止旧朗读, 无叠音。
// SECURITY_AND_PRIVACY.md §5: 只用系统 TTS, 不引入第三方语音 SDK。
//
// 分层设计:
//   - ITtsEngine: 纯逻辑抽象接口, 上层 (教程会话 / CLI) 只依赖它;
//   - NullTts: 静音实现, 记录朗读调用供无声环境与单元测试观察;
//   - createSystemTts(): 探测系统朗读能力 —— Linux 上依次寻找
//     espeak-ng / espeak / spd-say 命令行朗读器, 找到即以子进程
//     方式朗读; 找不到 (或非 Linux 平台) 静音降级为 NullTts,
//     调用方永远拿到可用对象, 无需判空。
// 后续 (M3): Windows SAPI / macOS AVSpeech / Android TextToSpeech
// 原生后端接入同一接口。
// =============================================================

#include <memory>
#include <optional>
#include <string>
#include <string_view>

namespace magtile::tts {

/// 朗读引擎抽象接口: 一次只朗读一段文本 (进入新步骤即替换)。
class ITtsEngine {
public:
    virtual ~ITtsEngine() = default;

    /// 朗读一段中文文本。实现必须先停止上一段朗读再开始新朗读
    /// (无叠音铁律, UI_UX_SPEC.md §4.2); 空文本等价于 stop()。
    virtual void speak(const std::string& text_zh) = 0;

    /// 立即停止当前朗读 (退出教程 / 静音开关时调用); 幂等。
    virtual void stop() = 0;

    /// 本机是否真的能发声 (NullTts 恒为 false, 供设置页诊断展示)。
    [[nodiscard]] virtual bool available() const noexcept = 0;

    /// 后端名称 (诊断与 settings show 展示), 如 "null" / "espeak-ng"。
    [[nodiscard]] virtual std::string_view name() const noexcept = 0;
};

/// 静音引擎: 不发声, 只记录朗读调用轨迹。
/// 用途: 无 TTS 能力环境的降级实现 + 单元测试的观察替身。
class NullTts final : public ITtsEngine {
public:
    void speak(const std::string& text_zh) override;
    void stop() override;
    [[nodiscard]] bool available() const noexcept override { return false; }
    [[nodiscard]] std::string_view name() const noexcept override { return "null"; }

    // ---- 测试观察接口 ------------------------------------------------
    /// 最近一次 speak 的文本 (体现 "新朗读替换旧朗读" 语义)。
    [[nodiscard]] const std::string& lastText() const noexcept { return last_text_; }
    /// 累计 speak 次数 (空文本不计, 它等价于 stop)。
    [[nodiscard]] int speakCount() const noexcept { return speak_count_; }
    /// 当前是否 "正在朗读" (speak 置真, stop 置假)。
    [[nodiscard]] bool speaking() const noexcept { return speaking_; }

private:
    std::string last_text_;
    int speak_count_ = 0;
    bool speaking_ = false;
};

/// 探测并创建系统朗读引擎; 永不返回空指针 (无能力时返回 NullTts)。
[[nodiscard]] std::unique_ptr<ITtsEngine> createSystemTts();

/// 在 PATH 中查找可执行文件, 找到返回完整路径 (探测逻辑独立导出,
/// 便于单元测试; Windows 平台恒返回 nullopt, 不走进程后端)。
[[nodiscard]] std::optional<std::string> findExecutableInPath(std::string_view name);

}  // namespace magtile::tts
