// =============================================================
// MagTile Studio - Qt 6 商用桌面界面入口
//
// 用法:
//   magtile_studio_qt [--data-dir DIR] [--db FILE]
//
// 默认行为与 CLI (magtile_app) 对齐:
//   - 数据目录: 优先 --data-dir; 否则从当前目录与可执行文件目录
//     逐级向上找含 tile_catalog.json 的 data/ 目录 (源码树内直接可跑);
//   - 进度存档: 与 CLI 共用同一平台默认路径 (docs/PROGRESS.md),
//     Qt 版与 GL 版看到同一份进度。
// =============================================================

#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>
#include <QUrl>
#include <cstdlib>
#include <filesystem>

#include "inventory_backend.hpp"
#include "studio_backend.hpp"

namespace fs = std::filesystem;

namespace {

/// 从 start 逐级向上查找包含 data/tile_catalog.json 的目录, 命中则返回
/// 其 data 子目录; 供源码树 / 安装树内免参数直接启动。
fs::path findDataDirUpwards(fs::path start) {
    std::error_code ec;
    for (fs::path dir = std::move(start); !dir.empty(); dir = dir.parent_path()) {
        if (fs::exists(dir / "data" / "tile_catalog.json", ec)) {
            return dir / "data";
        }
        if (dir == dir.root_path()) break;
    }
    return {};
}

/// 平台默认存档路径 —— 与 src/app/main.cpp 的 defaultProgressDbPath()
/// 保持逐字节一致, 保证 Qt 版与 CLI/GL 版共用同一份进度存档。
fs::path defaultProgressDbPath() {
#if defined(_WIN32)
    if (const char* appdata = std::getenv("APPDATA"); appdata != nullptr && *appdata != '\0') {
        return fs::path(appdata) / "MagTile" / "progress.db";
    }
#elif defined(__APPLE__)
    if (const char* home = std::getenv("HOME"); home != nullptr && *home != '\0') {
        return fs::path(home) / "Library" / "Application Support" / "MagTile" / "progress.db";
    }
#else
    if (const char* xdg = std::getenv("XDG_DATA_HOME"); xdg != nullptr && *xdg != '\0') {
        return fs::path(xdg) / "magtile" / "progress.db";
    }
    if (const char* home = std::getenv("HOME"); home != nullptr && *home != '\0') {
        return fs::path(home) / ".local" / "share" / "magtile" / "progress.db";
    }
#endif
    return fs::path("magtile_progress.db");  // 兜底: 当前目录
}

}  // namespace

int main(int argc, char* argv[]) {
    QGuiApplication app(argc, argv);
    QGuiApplication::setApplicationName(QStringLiteral("MagTile Studio"));
    QGuiApplication::setOrganizationName(QStringLiteral("MagTile"));
    QGuiApplication::setApplicationVersion(QStringLiteral("0.1.0"));

    // Basic 样式全平台一致且允许完全自绘控件背景 (儿童友好大按钮)
    QQuickStyle::setStyle(QStringLiteral("Basic"));

    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("MagTile 磁力片工坊 - Qt 桌面界面"));
    parser.addHelpOption();
    parser.addVersionOption();
    const QCommandLineOption data_dir_opt(
        QStringLiteral("data-dir"), QStringLiteral("数据目录 (含 tile_catalog.json 与 models/)"),
        QStringLiteral("DIR"));
    const QCommandLineOption db_opt(
        QStringLiteral("db"), QStringLiteral("进度存档数据库文件 (默认平台存档目录)"),
        QStringLiteral("FILE"));
    parser.addOption(data_dir_opt);
    parser.addOption(db_opt);
    parser.process(app);

    fs::path data_dir;
    if (parser.isSet(data_dir_opt)) {
        data_dir = fs::path(parser.value(data_dir_opt).toStdString());
    } else {
        data_dir = findDataDirUpwards(fs::current_path());
        if (data_dir.empty()) {
            data_dir = findDataDirUpwards(
                fs::path(QCoreApplication::applicationDirPath().toStdString()));
        }
        if (data_dir.empty()) data_dir = "data";  // 兜底: 交给 statusMessage 温和提示
    }

    const fs::path db_file = parser.isSet(db_opt)
                                 ? fs::path(parser.value(db_opt).toStdString())
                                 : defaultProgressDbPath();

    magtile::qtui::StudioBackend backend(data_dir, db_file);
    // 库存录入后端桥: 与 studio 共用同一 SQLite 存档 (多连接安全),
    // InventoryPage 保存后由 QML 调 studio.reload() 刷新「我能搭的」
    magtile::qtui::InventoryBackend inventory(data_dir, db_file);

    QQmlApplicationEngine engine;
    // Qt 6.4 的默认引擎导入路径不含 /qt/qml (6.5+ 才内置), 显式补上
    engine.addImportPath(QStringLiteral("qrc:/qt/qml"));
    engine.rootContext()->setContextProperty(QStringLiteral("studio"), &backend);
    engine.rootContext()->setContextProperty(QStringLiteral("inventory"), &inventory);

    QObject::connect(
        &engine, &QQmlApplicationEngine::objectCreationFailed, &app,
        []() { QCoreApplication::exit(1); }, Qt::QueuedConnection);
    engine.load(QUrl(QStringLiteral("qrc:/qt/qml/MagTile/Studio/qml/Main.qml")));

    return app.exec();
}
