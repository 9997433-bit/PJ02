#include "magtile/tts/tts_engine.hpp"

#include <cstdlib>
#include <filesystem>
#include <utility>
#include <vector>

#if defined(__linux__)
#include <csignal>
#include <fcntl.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace magtile::tts {

// ---- NullTts ------------------------------------------------------

void NullTts::speak(const std::string& text_zh) {
    if (text_zh.empty()) {  // 空文本等价于 stop (接口契约)
        stop();
        return;
    }
    last_text_ = text_zh;  // 直接替换: 无叠音语义在静音实现同样成立
    ++speak_count_;
    speaking_ = true;
}

void NullTts::stop() { speaking_ = false; }

// ---- PATH 探测 ------------------------------------------------------

std::optional<std::string> findExecutableInPath(std::string_view name) {
#if defined(_WIN32)
    // Windows 走 SAPI 原生后端 (M3), 不做命令行朗读器探测
    (void)name;
    return std::nullopt;
#else
    const char* path_env = std::getenv("PATH");
    if (path_env == nullptr || *path_env == '\0' || name.empty()) return std::nullopt;

    std::string_view remaining = path_env;
    while (!remaining.empty()) {
        const std::size_t colon = remaining.find(':');
        const std::string_view dir =
            colon == std::string_view::npos ? remaining : remaining.substr(0, colon);
        remaining = colon == std::string_view::npos ? std::string_view{}
                                                    : remaining.substr(colon + 1);
        if (dir.empty()) continue;

        const std::filesystem::path candidate = std::filesystem::path(dir) / name;
        std::error_code ec;
        if (std::filesystem::is_regular_file(candidate, ec) &&
            ::access(candidate.c_str(), X_OK) == 0) {
            return candidate.string();
        }
    }
    return std::nullopt;
#endif
}

// ---- Linux 子进程后端 (espeak-ng / espeak / spd-say) -----------------

#if defined(__linux__)
namespace {

/// 以子进程运行命令行朗读器: 进程存活期即朗读期, stop = 终止子进程。
/// espeak(-ng) 边合成边发声, SIGTERM 立即静音, 完美契合该模型;
/// spd-say 以 -w (等待朗读完成) 运行, 同样可被终止打断。
class ProcessTts final : public ITtsEngine {
public:
    ProcessTts(std::string program_path, std::vector<std::string> base_args,
               std::string backend_name)
        : program_path_(std::move(program_path)),
          base_args_(std::move(base_args)),
          backend_name_(std::move(backend_name)) {}

    ~ProcessTts() override { stop(); }

    void speak(const std::string& text_zh) override {
        stop();  // 无叠音铁律: 先停旧朗读 (UI_UX_SPEC.md §4.2)
        if (text_zh.empty()) return;

        const pid_t pid = ::fork();
        if (pid < 0) return;  // fork 失败: 静默降级, 朗读不能阻断教程
        if (pid == 0) {
            // 子进程: 朗读器自身的诊断输出重定向到 /dev/null,
            // 不污染应用的中文终端界面
            const int dev_null = ::open("/dev/null", O_WRONLY);
            if (dev_null >= 0) {
                ::dup2(dev_null, STDOUT_FILENO);
                ::dup2(dev_null, STDERR_FILENO);
                ::close(dev_null);
            }
            std::vector<char*> argv;
            argv.push_back(const_cast<char*>(program_path_.c_str()));
            for (const std::string& arg : base_args_) {
                argv.push_back(const_cast<char*>(arg.c_str()));
            }
            argv.push_back(const_cast<char*>(text_zh.c_str()));
            argv.push_back(nullptr);
            ::execv(program_path_.c_str(), argv.data());
            ::_exit(127);  // exec 失败: 立即退出子进程, 不回流应用逻辑
        }
        child_pid_ = pid;
    }

    void stop() override {
        if (child_pid_ <= 0) return;
        // 已自然读完则直接回收; 仍在朗读则终止后回收 —— 两条路径
        // 都必须 waitpid, 否则子进程沦为僵尸
        if (::waitpid(child_pid_, nullptr, WNOHANG) == 0) {
            ::kill(child_pid_, SIGTERM);
            ::waitpid(child_pid_, nullptr, 0);
        }
        child_pid_ = -1;
    }

    [[nodiscard]] bool available() const noexcept override { return true; }
    [[nodiscard]] std::string_view name() const noexcept override { return backend_name_; }

private:
    std::string program_path_;
    std::vector<std::string> base_args_;
    std::string backend_name_;
    pid_t child_pid_ = -1;  ///< 正在朗读的子进程; -1 = 空闲
};

}  // namespace
#endif  // __linux__

std::unique_ptr<ITtsEngine> createSystemTts() {
#if defined(__linux__)
    // 优先 espeak-ng (中文语音 cmn), 其次老版 espeak (zh);
    // 最后 speech-dispatcher 客户端 spd-say (走系统语音服务)
    if (auto path = findExecutableInPath("espeak-ng"); path.has_value()) {
        return std::make_unique<ProcessTts>(
            *path, std::vector<std::string>{"-v", "cmn"}, "espeak-ng");
    }
    if (auto path = findExecutableInPath("espeak"); path.has_value()) {
        return std::make_unique<ProcessTts>(
            *path, std::vector<std::string>{"-v", "zh"}, "espeak");
    }
    if (auto path = findExecutableInPath("spd-say"); path.has_value()) {
        // -w: 等待朗读完成再退出, 使 "进程存活期 = 朗读期" 成立
        return std::make_unique<ProcessTts>(
            *path, std::vector<std::string>{"-l", "zh", "-w"}, "spd-say");
    }
#endif
    return std::make_unique<NullTts>();  // 无朗读能力: 静音降级
}

}  // namespace magtile::tts
