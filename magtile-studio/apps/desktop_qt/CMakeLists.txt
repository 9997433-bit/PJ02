# =============================================================
# MagTile Studio - Qt 6 商用桌面界面 (QML)
#
# 仅在根目录 -DMAGTILE_BUILD_QT=ON 时进入本目录 (默认 OFF, 不装 Qt
# 也能完整构建其余目标)。Qt 体量巨大不适合 FetchContent, 统一走
# find_package 使用系统 / 自装 Qt (>= 6.4); 未找到时给出安装指引。
# 界面规范见 docs/UI_UX_SPEC.md, 迁移计划见 docs/QT_UI_PLAN.md。
# =============================================================

find_package(Qt6 6.4 QUIET COMPONENTS Core Gui Qml Quick QuickControls2)
if(NOT Qt6_FOUND)
    message(FATAL_ERROR
        "MAGTILE_BUILD_QT=ON 但未找到 Qt 6 (>= 6.4, 组件 Core/Gui/Qml/Quick/QuickControls2)。\n"
        "安装方式:\n"
        "  Ubuntu/Debian: sudo apt install qt6-base-dev qt6-declarative-dev \\\n"
        "      qml6-module-qtquick qml6-module-qtquick-controls qml6-module-qtquick-layouts \\\n"
        "      qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtqml-workerscript\n"
        "  macOS:         brew install qt   (随后 -DCMAKE_PREFIX_PATH=$(brew --prefix qt))\n"
        "  Windows:       Qt 官方在线安装器 (选 MSVC 2022 64-bit + Qt Quick),\n"
        "                 配置时 -DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64\n"
        "或保持默认 -DMAGTILE_BUILD_QT=OFF 跳过 Qt 界面, CLI/GL/测试目标完全不受影响。")
endif()

# AUTOMOC/AUTORCC/AUTOUIC 等 Qt 项目标准设置 (仅作用于本目录)
qt_standard_project_setup()

qt_add_executable(magtile_studio_qt
    src/main.cpp
    src/library_model.cpp
    src/library_filter_model.cpp
    src/studio_backend.cpp
)

# Theme.qml 是设计令牌单例 (pragma Singleton), 需在 qmldir 中登记为 singleton
set_source_files_properties(qml/Theme.qml PROPERTIES QT_QML_SINGLETON_TYPE TRUE)

# 显式固定资源前缀为 /qt/qml (Qt 6.5+ 的默认值; 6.4 默认是 /,
# 固定后配合 main.cpp 的 addImportPath 在两代 Qt 上行为一致)
qt_add_qml_module(magtile_studio_qt
    URI MagTile.Studio
    VERSION 1.0
    RESOURCE_PREFIX /qt/qml
    QML_FILES
        qml/Main.qml
        qml/HomePage.qml
        qml/LibraryPage.qml
        qml/DetailPage.qml
        qml/TutorialPage.qml
        qml/BigButton.qml
        qml/FilterChip.qml
        qml/Theme.qml
)

target_link_libraries(magtile_studio_qt PRIVATE
    magtile_core
    magtile_warnings
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
)

# 桌面应用外观: Windows 下不带控制台窗口; macOS 先不打 bundle
# (打包交由 platforms/ 与 QT_UI_PLAN.md 的发布阶段处理)
set_target_properties(magtile_studio_qt PROPERTIES
    WIN32_EXECUTABLE TRUE
    MACOSX_BUNDLE FALSE
)
