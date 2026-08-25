#include "privacy_backend.hpp"

#include <QDateTime>
#include <QDir>
#include <QFileInfo>
#include <QSaveFile>
#include <QStandardPaths>
#include <utility>

#include "magtile/progress/data_privacy.hpp"

namespace magtile::qtui {

PrivacyBackend::PrivacyBackend(std::filesystem::path db_file, QObject* parent)
    : QObject(parent), db_file_(std::move(db_file)) {
    try {
        store_ = std::make_unique<progress::ProgressStore>(db_file_);
    } catch (const progress::ProgressError&) {
        store_.reset();  // 存档打不开只禁用导出/清除按钮, 界面温和提示
    }
}

PrivacyBackend::~PrivacyBackend() = default;

QString PrivacyBackend::dbFileText() const {
    return QString::fromStdString(db_file_.string());
}

QString PrivacyBackend::exportData(const QString& target_dir) {
    if (store_ == nullptr) return {};

    std::string payload;
    try {
        payload = progress::exportLocalDataJson(*store_);
    } catch (const progress::ProgressError&) {
        return {};  // 读库失败: 界面温和提示 "稍后再试", 不弹 "失败"
    }

    // 目标目录: 显式指定 > 文档目录 > 主目录 > 存档所在目录 (逐级退回)
    QString dir = target_dir;
    if (dir.isEmpty()) {
        dir = QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation);
    }
    if (dir.isEmpty()) {
        dir = QStandardPaths::writableLocation(QStandardPaths::HomeLocation);
    }
    if (dir.isEmpty()) {
        dir = QString::fromStdString(db_file_.parent_path().string());
    }
    if (dir.isEmpty()) dir = QStringLiteral(".");
    if (!QDir().mkpath(dir)) return {};

    // 时间戳到毫秒 + 已存在则追加序号: 多次导出互不覆盖, 家长可留多份存档
    const QString stamp =
        QDateTime::currentDateTime().toString(QStringLiteral("yyyyMMdd_HHmmss_zzz"));
    QString file_path =
        dir + QLatin1Char('/') + QStringLiteral("magtile_数据导出_%1.json").arg(stamp);
    for (int seq = 2; QFileInfo::exists(file_path); ++seq) {
        file_path = dir + QLatin1Char('/') +
                    QStringLiteral("magtile_数据导出_%1_%2.json").arg(stamp).arg(seq);
    }

    // QSaveFile 原子写入: 写一半失败不会留下残缺文件
    QSaveFile file(file_path);
    if (!file.open(QIODevice::WriteOnly)) return {};
    if (file.write(payload.data(), static_cast<qint64>(payload.size())) !=
        static_cast<qint64>(payload.size())) {
        return {};  // QSaveFile 析构自动丢弃临时文件
    }
    if (!file.commit()) return {};
    return QFileInfo(file_path).absoluteFilePath();
}

bool PrivacyBackend::clearAllData() {
    if (store_ == nullptr) return false;
    try {
        store_->clearAllData();  // 单事务原子清空, 失败不留半清状态
    } catch (const progress::ProgressError&) {
        return false;
    }
    emit dataCleared();
    return true;
}

}  // namespace magtile::qtui
