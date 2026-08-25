#pragma once

// =============================================================
// MagTile Studio (Qt) - 隐私与数据后端桥
//
// 家长中心「隐私与数据」区与 ProgressStore 之间的桥, 落实
// SECURITY_AND_PRIVACY.md §3 / §4 (COPPA C4 · 《规定》Z8):
// 家长可查看、导出、删除全部本地数据。
//   - exportData(): 全部本地数据 (进度/成就/库存/设置) 经
//     progress::exportLocalDataJson 序列化为家长可读的 JSON,
//     原子写入系统「文档」目录 (逐级温和退回主目录 / 存档目录),
//     返回文件完整路径 (失败返回空串, 界面温和提示不弹「失败」);
//   - clearAllData(): ProgressStore::clearAllData 单事务原子清空
//     四张表, 成功后发 dataCleared —— 界面据此温和回到首次启动
//     状态 (studio.reload + appSettings/tts resetToDefaults +
//     锁定家长会话退回首页)。
// 两个操作都只可能出现在家长门之后 (家长中心本身在门后), 清除
// 另有界面层二次确认 (§6.1「数据操作」)。独立于其他桥 (SQLite
// 同库多连接安全); 存档打不开只降级不崩溃 (P3 零挫败)。
// =============================================================

#include <QObject>
#include <QString>
#include <filesystem>
#include <memory>

#include "magtile/progress/progress_store.hpp"

namespace magtile::qtui {

class PrivacyBackend final : public QObject {
    Q_OBJECT
    /// 存档是否可用 (不可用时导出/清除按钮由界面温和禁用)。
    Q_PROPERTY(bool storeAvailable READ storeAvailable CONSTANT)
    /// 本机存档文件完整路径 (「数据存在哪」展示用, §3 透明可审计)。
    Q_PROPERTY(QString dbFileText READ dbFileText CONSTANT)

public:
    explicit PrivacyBackend(std::filesystem::path db_file, QObject* parent = nullptr);
    ~PrivacyBackend() override;

    [[nodiscard]] bool storeAvailable() const noexcept { return store_ != nullptr; }
    [[nodiscard]] QString dbFileText() const;

    /// 导出全部本地数据为 JSON 文件, 返回完整路径; 失败返回空串。
    /// target_dir 为空时用系统「文档」目录 (缺省退回主目录, 再退回
    /// 存档目录); 文件名带时间戳 (精确到毫秒), 多次导出互不覆盖。
    Q_INVOKABLE QString exportData(const QString& target_dir = QString());

    /// 清除全部本地数据 (进度/成就/库存/设置, 单事务原子执行)。
    /// 成功返回 true 并发 dataCleared; 温和回到首次状态由界面完成。
    Q_INVOKABLE bool clearAllData();

signals:
    /// 本地数据已清除 (界面据此刷新模型库 / 重置设置 / 退回首页)。
    void dataCleared();

private:
    std::filesystem::path db_file_;
    std::unique_ptr<progress::ProgressStore> store_;  ///< 打开失败时为空 (只降级不崩溃)
};

}  // namespace magtile::qtui
