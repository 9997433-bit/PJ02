# =============================================================
# MagTile Studio - Qt 6 商用桌面界面 (QML)
#
# 仅在根目录 -DMAGTILE_BUILD_QT=ON 时进入本目录 (默认 OFF, 不装 Qt
# 也能完整构建其余目标)。Qt 体量巨大不适合 FetchContent, 统一走
# find_package 使用系统 / 自装 Qt (>= 6.4); 未找到时给出安装指引。
# 界面规范见 docs/UI_UX_SPEC.md, 迁移计划见 docs/QT_UI_PLAN.md。
# =============================================================

# OpenGL 组件: QT-3 教程视口 (QQuickFramebufferObject) 依赖
# QOpenGLFramebufferObject; 随 qt6-base-dev 一并安装, 无额外依赖。
find_package(Qt6 6.4 QUIET COMPONENTS Core Gui Qml Quick QuickControls2 OpenGL)
if(NOT Qt6_FOUND)
    message(FATAL_ERROR
        "MAGTILE_BUILD_QT=ON 但未找到 Qt 6 (>= 6.4, 组件 Core/Gui/Qml/Quick/QuickControls2/OpenGL)。\n"
        "安装方式:\n"
        "  Ubuntu/Debian: sudo apt install qt6-base-dev qt6-declarative-dev \\\n"
        "      qml6-module-qtquick qml6-module-qtquick-controls qml6-module-qtquick-layouts \\\n"
        "      qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtqml-workerscript\n"
        "  macOS:         brew install qt   (随后 -DCMAKE_PREFIX_PATH=$(brew --prefix qt))\n"
        "  Windows:       Qt 官方在线安装器 (选 MSVC 2022 64-bit + Qt Quick),\n"
        "                 配置时 -DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64\n"
        "或保持默认 -DMAGTILE_BUILD_QT=OFF 跳过 Qt 界面, CLI/GL/测试目标完全不受影响。")
endif()

# QtTextToSpeech (步骤朗读 §4.2, QT-4): 可选组件 —— 未安装时应用
# 照常构建, 朗读静默降级 (TtsBackend available=false, 界面温和提示)
find_package(Qt6 6.4 QUIET COMPONENTS TextToSpeech)
if(NOT TARGET Qt6::TextToSpeech)
    message(STATUS
        "MagTile: 未找到 Qt6TextToSpeech, Qt 界面朗读降级为静默。"
        "安装后重新配置即可启用: sudo apt install qt6-speech-dev "
        "qt6-speech-speechd-plugin (Ubuntu/Debian); macOS/Windows 随官方 Qt 附带。")
endif()

# AUTOMOC/AUTORCC/AUTOUIC 等 Qt 项目标准设置 (仅作用于本目录)
qt_standard_project_setup()

qt_add_executable(magtile_studio_qt
    src/main.cpp
    src/library_model.cpp
    src/library_filter_model.cpp
    src/studio_backend.cpp
    src/inventory_backend.cpp
    src/parent_gate_backend.cpp
    src/settings_backend.cpp
    src/tts_backend.cpp
    src/tutorial_viewport.cpp
)

# qmltyperegistrar 生成的注册文件以 <tutorial_viewport.hpp> 形式包含
# QML_ELEMENT 类型头, 须把 src/ 挂进目标包含路径
target_include_directories(magtile_studio_qt PRIVATE src)

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
        qml/CelebrationPage.qml
        qml/ProgressPage.qml
        qml/AchievementsPage.qml
        qml/InventoryPage.qml
        qml/ParentGatePage.qml
        qml/ParentAreaPage.qml
        qml/SettingsPage.qml
        qml/SubscriptionPage.qml
        qml/BigButton.qml
        qml/FilterChip.qml
        qml/Theme.qml
)

target_link_libraries(magtile_studio_qt PRIVATE
    magtile_core
    magtile_render_scene    # 3D 教程视口场景渲染 (与 GL 版共用, QT-3)
    magtile_warnings
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::OpenGL
)

# 朗读引擎 (可选): 找到才链接并开启编译分支, 否则 TtsBackend 静默降级
if(TARGET Qt6::TextToSpeech)
    target_link_libraries(magtile_studio_qt PRIVATE Qt6::TextToSpeech)
    target_compile_definitions(magtile_studio_qt PRIVATE MAGTILE_QT_TTS)
endif()

# 桌面应用外观: Windows 下不带控制台窗口; macOS 先不打 bundle
# (打包交由 platforms/ 与 QT_UI_PLAN.md 的发布阶段处理)
set_target_properties(magtile_studio_qt PROPERTIES
    WIN32_EXECUTABLE TRUE
    MACOSX_BUNDLE FALSE
)

# ---- Qt 侧测试 (仅 MAGTILE_BUILD_QT=ON 时注册, 详见 docs/TESTING.md) ----
if(MAGTILE_BUILD_TESTS)
    # 后端桥单元测试 (C++, 无需显示环境): 家长门桥 (过门/答错/冷却/
    # 锁定) 与设置桥 (字号三档/减少动效/年龄段) 的 SQLite 往返, 以及
    # 与 GL 版/CLI 的键名契约互通 (共用同一 SQLite 存档承诺);
    # 另覆盖模型库筛选代理的「我能搭的」空态推荐 (QT-1)
    if(EXISTS ${CMAKE_SOURCE_DIR}/tests/test_qt_backends.cpp)
        qt_add_executable(magtile_qt_backend_test
            ${CMAKE_SOURCE_DIR}/tests/test_qt_backends.cpp
            src/library_model.cpp
            src/library_filter_model.cpp
            src/parent_gate_backend.cpp
            src/settings_backend.cpp
        )
        target_include_directories(magtile_qt_backend_test PRIVATE src)
        target_link_libraries(magtile_qt_backend_test PRIVATE
            magtile_core
            magtile_warnings
            Qt6::Core
        )
        add_test(NAME qt_backend_bridges
            COMMAND magtile_qt_backend_test ${CMAKE_BINARY_DIR}/qt_backend_test.db)
    endif()

    # QML 加载冒烟 (offscreen 平台, 与显示环境无关): 默认启动 + 家长门
    # 深链各跑一次, QML 有任何加载错误进程即非零退出
    find_program(MAGTILE_QT_BASH bash)
    if(MAGTILE_QT_BASH AND EXISTS ${CMAKE_SOURCE_DIR}/tests/test_qt_smoke.sh)
        add_test(NAME qt_gui_smoke
            COMMAND ${MAGTILE_QT_BASH} ${CMAKE_SOURCE_DIR}/tests/test_qt_smoke.sh
                $<TARGET_FILE:magtile_studio_qt> ${CMAKE_SOURCE_DIR})
        set_tests_properties(qt_gui_smoke PROPERTIES TIMEOUT 120)
    endif()
endif()

# ---- 打包安装规则 (安装布局见 platforms/windows/packaging) --------
# 安装到安装根, 与 magtile_app 并列。Qt 运行库 (DLL + QML 模块) 部署:
#   - Qt >= 6.5: 官方部署 API 在 install/cpack 阶段自动收集
#     (Windows/macOS 支持; 其余平台经 NO_UNSUPPORTED_PLATFORM_ERROR
#     静默跳过, Linux TGZ 冒烟不受影响);
#   - Qt 6.4: 部署 API 尚为技术预览, 不启用 —— 打包后手动对安装目录
#     运行 windeployqt (命令见 scripts/package_windows.md 第五节)。
install(TARGETS magtile_studio_qt RUNTIME DESTINATION .)
if(Qt6_VERSION VERSION_GREATER_EQUAL 6.5)
    qt_generate_deploy_qml_app_script(
        TARGET magtile_studio_qt
        OUTPUT_SCRIPT magtile_qt_deploy_script
        NO_UNSUPPORTED_PLATFORM_ERROR
        NO_TRANSLATIONS
    )
    install(SCRIPT ${magtile_qt_deploy_script})
else()
    message(STATUS
        "MagTile: Qt ${Qt6_VERSION} < 6.5 无稳定部署 API, 打包后请手动运行 "
        "windeployqt (见 scripts/package_windows.md 第五节)")
endif()
