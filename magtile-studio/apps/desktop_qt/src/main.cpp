// =============================================================
// MagTile Studio - Qt 6 商用桌面界面入口
//
// 用法:
//   magtile_studio_qt [--data-dir DIR] [--db FILE]
//                     [--parent-gate] [--smoke-quit-ms N]
//
// 默认行为与 CLI (magtile_app) 对齐:
//   - 数据目录: 优先 --data-dir; 否则从当前目录与可执行文件目录
//     逐级向上找含 tile_catalog.json 的 data/ 目录 (源码树内直接可跑);
//   - 进度存档: 与 CLI 共用同一平台默认路径 (docs/PROGRESS.md),
//     Qt 版与 GL 版看到同一份进度与设置;
//   - --parent-gate: 启动即显示家长门 (评审 / 冒烟, 同 GL 版深链);
//   - --smoke-quit-ms: N 毫秒后自动退出 (无头 QML 加载冒烟专用);
//   - --smoke-open-model: 启动后直接进入该模型的 3D 教程 (QT-3 冒烟);
//   - --smoke-screenshot: 2.5s 后抓屏保存 PNG 并退出 (配合上一项)。
//
// 场景图后端: 3D 教程视口 (QQuickFramebufferObject) 需要 OpenGL,
// 未显式设置 QSG_RHI_BACKEND 时在此固定为 OpenGL (全平台桌面可用)。
// =============================================================

#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QSGRendererInterface>
#include <QTimer>
#include <QUrl>
#include <cstdlib>
#include <filesystem>

#include "inventory_backend.hpp"
#include "parent_gate_backend.hpp"
#include "settings_backend.hpp"
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

    // 3D 教程视口 (QQuickFramebufferObject, QT-3) 依赖 OpenGL 场景图;
    // 尊重用户显式设置的 QSG_RHI_BACKEND, 未设置时固定为 OpenGL
    if (qEnvironmentVariableIsEmpty("QSG_RHI_BACKEND")) {
        QQuickWindow::setGraphicsApi(QSGRendererInterface::OpenGL);
    }

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
    const QCommandLineOption parent_gate_opt(
        QStringLiteral("parent-gate"), QStringLiteral("启动即显示家长门 (评审/冒烟深链)"));
    const QCommandLineOption smoke_quit_opt(
        QStringLiteral("smoke-quit-ms"),
        QStringLiteral("N 毫秒后自动退出 (无头 QML 加载冒烟专用)"), QStringLiteral("N"));
    const QCommandLineOption smoke_flow_opt(
        QStringLiteral("smoke-parent-flow"),
        QStringLiteral("冒烟自动驾驶: 家长门->过门->家长中心->设置->订阅 (配合 --smoke-quit-ms)"));
    const QCommandLineOption smoke_model_opt(
        QStringLiteral("smoke-open-model"),
        QStringLiteral("启动后直接进入该模型的 3D 教程 (QT-3 视口冒烟)"), QStringLiteral("ID"));
    const QCommandLineOption smoke_shot_opt(
        QStringLiteral("smoke-screenshot"),
        QStringLiteral("2.5 秒后抓屏保存 PNG 并退出 (视口画面验证)"), QStringLiteral("FILE"));
    parser.addOption(data_dir_opt);
    parser.addOption(db_opt);
    parser.addOption(parent_gate_opt);
    parser.addOption(smoke_quit_opt);
    parser.addOption(smoke_flow_opt);
    parser.addOption(smoke_model_opt);
    parser.addOption(smoke_shot_opt);
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
    // 家长门后端桥 (§9): 题目/冷却/会话只存内存, 不接触存档
    magtile::qtui::ParentGateBackend parent_gate(parser.isSet(parent_gate_opt));
    // 设置后端桥 (§8): 字号三档/减少动效/年龄段, 与 GL 版/CLI 共库
    magtile::qtui::SettingsBackend settings(db_file);

    QQmlApplicationEngine engine;
    // Qt 6.4 的默认引擎导入路径不含 /qt/qml (6.5+ 才内置), 显式补上
    engine.addImportPath(QStringLiteral("qrc:/qt/qml"));
    engine.rootContext()->setContextProperty(QStringLiteral("studio"), &backend);
    engine.rootContext()->setContextProperty(QStringLiteral("inventory"), &inventory);
    engine.rootContext()->setContextProperty(QStringLiteral("parentGate"), &parent_gate);
    engine.rootContext()->setContextProperty(QStringLiteral("appSettings"), &settings);
    const bool smoke_flow = parser.isSet(smoke_flow_opt);
    engine.rootContext()->setContextProperty(QStringLiteral("smokeParentFlow"), smoke_flow);

    QObject::connect(
        &engine, &QQmlApplicationEngine::objectCreationFailed, &app,
        []() { QCoreApplication::exit(1); }, Qt::QueuedConnection);
    engine.load(QUrl(QStringLiteral("qrc:/qt/qml/MagTile/Studio/qml/Main.qml")));

    // QT-3 视口冒烟: 启动即路由进 3D 教程 (走与用户一致的
    // buildRequested 信号), 可选抓屏验证画面后自动退出
    if (parser.isSet(smoke_model_opt)) {
        const QString model_id = parser.value(smoke_model_opt);
        QTimer::singleShot(0, &backend,
                           [&backend, model_id]() { backend.startBuild(model_id); });
    }
    if (parser.isSet(smoke_shot_opt)) {
        const QString shot_file = parser.value(smoke_shot_opt);
        QTimer::singleShot(2500, &app, [&engine, shot_file]() {
            int exit_code = 1;
            const auto roots = engine.rootObjects();
            if (!roots.isEmpty()) {
                if (auto* window = qobject_cast<QQuickWindow*>(roots.constFirst());
                    window != nullptr && window->grabWindow().save(shot_file)) {
                    exit_code = 0;
                }
            }
            QCoreApplication::exit(exit_code);
        });
    }

    // 无头冒烟: QML 全部加载成功后按时退出 (加载失败走上面的 exit(1));
    // 自动驾驶模式下退出码由 Main.qml 的 smokeParentFlowOk 决定
    if (parser.isSet(smoke_quit_opt)) {
        bool ok = false;
        const int quit_ms = parser.value(smoke_quit_opt).toInt(&ok);
        if (ok && quit_ms > 0) {
            QTimer::singleShot(quit_ms, &app, [&engine, smoke_flow]() {
                int exit_code = 0;
                if (smoke_flow) {
                    const auto roots = engine.rootObjects();
                    exit_code = (!roots.isEmpty() &&
                                 roots.constFirst()->property("smokeParentFlowOk").toBool())
                                    ? 0
                                    : 1;
                }
                QCoreApplication::exit(exit_code);
            });
        }
    }

    return app.exec();
}
