# =============================================================
# MagTile Studio - 磁力片搭建教程应用
# 构建要求: CMake >= 3.20, 支持 C++20 的编译器
#   (MSVC 2022 / Clang 14+ / GCC 11+, 覆盖 Windows / macOS / Linux)
# =============================================================
cmake_minimum_required(VERSION 3.20)

project(MagTileStudio
    VERSION 0.1.0
    DESCRIPTION "MagTile Studio - Magnetic tile building tutorial application"
    LANGUAGES C CXX)  # C 仅用于编译 third_party/sqlite3 amalgamation

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# 渲染后端开关: 默认开启; 无显示环境的纯 CI 可用 -DMAGTILE_BUILD_GL_RENDERER=OFF
# 关闭后不需要网络与 X11/Wayland 开发库, CLI 功能完全不受影响。
option(MAGTILE_BUILD_GL_RENDERER "构建 GLFW + OpenGL 渲染后端 (GLFW/ImGui 经 FetchContent 获取)" ON)
option(MAGTILE_BUILD_TESTS "构建并注册 CTest 用例" ON)

# Qt 6 商用桌面界面 (apps/desktop_qt, QML): 默认关闭, 不安装 Qt 也能
# 完整构建其余目标。开启需系统安装 Qt >= 6.4 (依赖清单与迁移计划见
# docs/QT_UI_PLAN.md); 未找到 Qt 时给出带安装指引的明确报错。
option(MAGTILE_BUILD_QT "构建 Qt 6 + QML 商用桌面界面 (需系统 Qt >= 6.4, 见 docs/QT_UI_PLAN.md)" OFF)

# ---- Android 交叉编译 (NDK 工具链文件会定义 ANDROID) -------------
# 用法见 platforms/android/README.md。手机端不使用桌面 GL 后端
# (GLFW) 也无法跑 CTest, 强制关闭; 只产出 magtile_core + JNI 共享库。
# Qt 桌面外壳同理不参与 Android 构建 (平板走 Compose, 见平台架构文档)。
if(ANDROID)
    set(MAGTILE_BUILD_GL_RENDERER OFF CACHE BOOL "" FORCE)
    set(MAGTILE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(MAGTILE_BUILD_QT OFF CACHE BOOL "" FORCE)
endif()

# ---- 编译警告 --------------------------------------------------
add_library(magtile_warnings INTERFACE)
if(MSVC)
    target_compile_options(magtile_warnings INTERFACE /W4 /utf-8)
else()
    target_compile_options(magtile_warnings INTERFACE -Wall -Wextra -Wpedantic)
endif()

# ---- SQLite3 (third_party 内嵌 amalgamation, 进度存档用) ---------
# 全平台 (含 Android NDK) 统一自编译, 不依赖系统安装的 sqlite 开发包。
add_library(magtile_sqlite3 STATIC third_party/sqlite3/sqlite3.c)
target_include_directories(magtile_sqlite3 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/third_party/sqlite3)
target_compile_definitions(magtile_sqlite3 PRIVATE
    SQLITE_THREADSAFE=1            # 未来 GUI + 同步线程并发访问
    SQLITE_OMIT_LOAD_EXTENSION=1   # 不用扩展加载, 同时免去 -ldl 依赖
    SQLITE_OMIT_DEPRECATED=1
    SQLITE_DQS=0                   # 禁止双引号字符串 (SQL 书写错误尽早暴露)
    SQLITE_DEFAULT_MEMSTATUS=0
)
find_package(Threads REQUIRED)
target_link_libraries(magtile_sqlite3 PUBLIC Threads::Threads)
if(UNIX)
    target_link_libraries(magtile_sqlite3 PUBLIC m)
endif()

# ---- 核心库: core + physics + tutorial + render 接口 + progress --
add_library(magtile_core STATIC
    src/core/types.cpp
    src/core/age_mode.cpp
    src/core/model_definition.cpp
    src/core/tile_catalog.cpp
    src/core/json_io.cpp
    src/core/model_catalog.cpp
    src/core/parent_gate.cpp
    src/physics/geometry.cpp
    src/physics/physics_validator.cpp
    src/progress/progress_store.cpp
    src/progress/achievements.cpp
    src/progress/data_privacy.cpp
    src/progress/age_settings.cpp
    src/progress/ui_settings.cpp
    src/progress/subscription_settings.cpp
    src/billing/fake_billing_client.cpp
    src/billing/store_billing_client.cpp
    src/tts/tts_engine.cpp
    src/tutorial/tutorial_engine.cpp
    src/render/null_renderer.cpp
    src/render/orbit_camera.cpp
)
target_include_directories(magtile_core
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)
target_link_libraries(magtile_core PRIVATE magtile_warnings magtile_sqlite3)

# ---- 无窗口 GL 磁力片场景渲染器 ----------------------------------
# 只画场景不建窗口 (gl_scene_renderer.cpp + 自研 GL 加载器), 零外部
# 依赖; 供 GLFW/ImGui 外壳、Qt 教程视口 (QQuickFramebufferObject,
# QT-3) 与 Android 教程视口 (GLSurfaceView + GLES3, 着色器版本头
# 运行时选择) 共用同一份 3D 绘制实现。
if(MAGTILE_BUILD_GL_RENDERER OR MAGTILE_BUILD_QT OR ANDROID)
    add_library(magtile_render_scene STATIC
        src/render/gl/gl_api.cpp
        src/render/gl/gl_scene_renderer.cpp
    )
    target_link_libraries(magtile_render_scene
        PUBLIC magtile_core
        PRIVATE magtile_warnings
    )
endif()

# ---- GLFW + OpenGL 4.1 渲染后端 ---------------------------------
if(MAGTILE_BUILD_GL_RENDERER)
    include(FetchContent)

    # GLFW: 优先使用系统安装 (发行版打包 / brew / vcpkg), 否则联网获取
    find_package(glfw3 3.3 QUIET)
    if(NOT glfw3_FOUND)
        message(STATUS "MagTile: 未找到系统 GLFW, 通过 FetchContent 获取 3.4")
        set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
        set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
        set(GLFW_INSTALL OFF CACHE BOOL "" FORCE)
        # Linux: 缺少 Wayland 开发工具时退回仅 X11, 避免构建硬失败
        if(UNIX AND NOT APPLE)
            find_program(MAGTILE_WAYLAND_SCANNER wayland-scanner)
            if(NOT MAGTILE_WAYLAND_SCANNER)
                set(GLFW_BUILD_WAYLAND OFF CACHE BOOL "" FORCE)
                message(STATUS "MagTile: 未找到 wayland-scanner, GLFW 仅启用 X11 后端")
            endif()
        endif()
        FetchContent_Declare(glfw
            GIT_REPOSITORY https://github.com/glfw/glfw.git
            GIT_TAG 3.4
            GIT_SHALLOW TRUE)
        FetchContent_MakeAvailable(glfw)
    endif()

    # Dear ImGui: 教程 HUD (无自带构建脚本, 直接编译其源码)
    FetchContent_Declare(imgui
        GIT_REPOSITORY https://github.com/ocornut/imgui.git
        GIT_TAG v1.91.9b
        GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(imgui)

    add_library(magtile_imgui STATIC
        ${imgui_SOURCE_DIR}/imgui.cpp
        ${imgui_SOURCE_DIR}/imgui_draw.cpp
        ${imgui_SOURCE_DIR}/imgui_tables.cpp
        ${imgui_SOURCE_DIR}/imgui_widgets.cpp
        ${imgui_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
        ${imgui_SOURCE_DIR}/backends/imgui_impl_opengl3.cpp
    )
    target_include_directories(magtile_imgui PUBLIC
        ${imgui_SOURCE_DIR}
        ${imgui_SOURCE_DIR}/backends
    )
    # 不引入系统 GL 头: ImGui 的 GL3 后端自带加载器, 本项目用自研加载器
    target_compile_definitions(magtile_imgui PUBLIC GLFW_INCLUDE_NONE)
    target_link_libraries(magtile_imgui PUBLIC glfw)

    add_library(magtile_render_gl STATIC
        src/render/gl/gl_renderer.cpp
        src/render/gl/stb_image_impl.cpp   # stb_image 实现单元 (缩略图 PNG 解码)
    )
    target_include_directories(magtile_render_gl PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/third_party)
    target_link_libraries(magtile_render_gl
        PUBLIC magtile_core magtile_render_scene
        PRIVATE magtile_imgui glfw magtile_warnings
    )
    # 链接方可据此宏启用 --dev-gui 代码路径 (GL/ImGui 内部开发工具)
    target_compile_definitions(magtile_render_gl PUBLIC MAGTILE_HAS_GL_RENDERER=1)
endif()

# ---- 命令行应用 (桌面; Android 由 platforms/android 提供 JNI 外壳) ----
if(NOT ANDROID)
    add_executable(magtile_app src/app/main.cpp)
    target_link_libraries(magtile_app PRIVATE magtile_core magtile_warnings)
    if(MAGTILE_BUILD_GL_RENDERER)
        target_link_libraries(magtile_app PRIVATE magtile_render_gl)
    endif()
endif()

# ---- Qt 6 商用桌面界面 (QML 外壳, 复用 magtile_core) --------------
# 与 GL/ImGui 后端并存: GL 版继续承担 3D 教程与冒烟测试,
# Qt 版承载商用界面 (首页/模型库/家长门...), 迁移路线见 docs/QT_UI_PLAN.md。
# CTest 须在进入子目录前启用, 子目录内注册的用例 (qt_backend_bridges /
# qt_gui_smoke) 才会被收进测试清单。
if(MAGTILE_BUILD_TESTS)
    enable_testing()
endif()
if(MAGTILE_BUILD_QT)
    add_subdirectory(apps/desktop_qt)
endif()

# ---- 平台外壳 (Android JNI 共享库 / Windows 打包资产) -------------
# 按存在性引入, 平台外壳资产分批合入期间仓库始终可配置。
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/platforms/CMakeLists.txt)
    add_subdirectory(platforms)
endif()

# ---- 安装与打包 (CPack; Windows 安装器) ---------------------------
# 版本号唯一来源是顶部 project(VERSION x.y.z), 打包配置一律引用
# PROJECT_VERSION。Windows 产出 NSIS 安装器 + 便携 ZIP (WiX/MSI 见
# platforms/windows/packaging/Product.wxs); 其它桌面平台产出 TGZ
# 仅作安装规则冒烟。随包模型库范围由 -DMAGTILE_PACKAGE_MODEL_SET
# 控制 (full / starter / 自定义清单), 包形态由 -DMAGTILE_PACKAGE_QT_ONLY
# 控制 (默认 magtile_app 与 Qt 界面并存, ON 时只装 Qt 界面)。
# 用法详见 scripts/package_windows.md 与 scripts/package_qt_desktop.md。
if(NOT ANDROID)
    include(platforms/windows/packaging/CPackWindows.cmake)
endif()

# ---- 测试 (详见 docs/TESTING.md) --------------------------------
if(MAGTILE_BUILD_TESTS)
    enable_testing()

    set(MAGTILE_DATA_DIR  ${CMAKE_CURRENT_SOURCE_DIR}/data)
    set(MAGTILE_TESTS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/tests)

    add_test(NAME print_tile_catalog
        COMMAND magtile_app catalog --data-dir ${MAGTILE_DATA_DIR})

    # 进度存档回归测试 (C++): 保存/读取往返、完成/收藏/成就/库存、
    # 跨连接持久化与重置删除, 详见 tests/test_progress_roundtrip.cpp
    if(EXISTS ${MAGTILE_TESTS_DIR}/test_progress_roundtrip.cpp)
        add_executable(magtile_progress_test tests/test_progress_roundtrip.cpp)
        target_link_libraries(magtile_progress_test PRIVATE magtile_core magtile_warnings)
        add_test(NAME progress_roundtrip
            COMMAND magtile_progress_test ${CMAKE_CURRENT_BINARY_DIR}/progress_roundtrip_test.db)
    endif()

    # 成就解锁统一收口回归测试 (C++): 档位表契约 (1/3/10/30 升序)、
    # 首次完成解锁、重复完成幂等不覆盖、分档边界 3/10/30、老档补录
    # 与跨连接持久化, 详见 tests/test_achievements.cpp
    if(EXISTS ${MAGTILE_TESTS_DIR}/test_achievements.cpp)
        add_executable(magtile_achievements_test tests/test_achievements.cpp)
        target_link_libraries(magtile_achievements_test PRIVATE magtile_core magtile_warnings)
        add_test(NAME achievements_unlock
            COMMAND magtile_achievements_test ${CMAKE_CURRENT_BINARY_DIR}/achievements_unlock_test.db)
    endif()

    # 跨端进度存档互通回归测试 (C++, E2E-17 自动化载体): Qt/GL/CLI/
    # Android 共用 SQLite 存档的 settings 键契约 (age_mode /
    # onboarding_age_done / subscription_active / subscription_product_id
    # 编译期 static_assert + 落盘键值对账) + 完成记录/成就解锁经第二条
    # 连接按 Qt 读取口径回读, 详见 tests/test_cross_platform_progress.cpp
    if(EXISTS ${MAGTILE_TESTS_DIR}/test_cross_platform_progress.cpp)
        add_executable(magtile_cross_platform_test tests/test_cross_platform_progress.cpp)
        target_link_libraries(magtile_cross_platform_test PRIVATE magtile_core magtile_warnings)
        add_test(NAME cross_platform_progress
            COMMAND magtile_cross_platform_test ${CMAKE_CURRENT_BINARY_DIR}/cross_platform_progress_test.db)
    endif()

    # 进度存档 CLI 冒烟: 空库 list 必须正常退出 (同时覆盖建库建表路径)
    add_test(NAME progress_cli_smoke
        COMMAND magtile_app progress list --db ${CMAKE_CURRENT_BINARY_DIR}/progress_cli_smoke.db)

    # 家长门单元测试 (C++): 题目生成域、中文大写数字转换/解析、
    # 验证逻辑、冷却状态机、内存会话有效期 (SECURITY_AND_PRIVACY.md §6.2
    # 要求家长门组件独立可复用并单元测试)
    if(EXISTS ${MAGTILE_TESTS_DIR}/test_parent_gate.cpp)
        add_executable(magtile_parent_gate_test tests/test_parent_gate.cpp)
        target_link_libraries(magtile_parent_gate_test PRIVATE magtile_core magtile_warnings)
        add_test(NAME parent_gate COMMAND magtile_parent_gate_test)
    endif()

    # 计费适配层单元测试 (C++): BillingClient 抽象 + FakeBillingClient
    # 付费闭环 (未订阅锁付费模型 / 假购买解锁 / 恢复购买 / 订阅状态
    # settings 表持久化契约) 与 StoreBillingClient 空实现档语义
    # (COMMERCIAL_PLAN §2.2; 不接任何真实商店 SDK / 密钥)
    if(EXISTS ${MAGTILE_TESTS_DIR}/test_billing.cpp)
        add_executable(magtile_billing_test tests/test_billing.cpp)
        target_link_libraries(magtile_billing_test PRIVATE magtile_core magtile_warnings)
        add_test(NAME billing
            COMMAND magtile_billing_test ${CMAKE_CURRENT_BINARY_DIR}/billing_test.db)
    endif()

    # 年龄分层与 TTS 单元测试 (C++): AgeMode 字符串/周岁映射、
    # 年龄段设置的 SQLite 持久化 (含脏值兜底)、NullTts 无叠音语义、
    # 系统 TTS 探测与静音降级 (UI_UX_SPEC.md §2 / §4.2 儿童 UX stub)
    if(EXISTS ${MAGTILE_TESTS_DIR}/test_age_tts.cpp)
        add_executable(magtile_age_tts_test tests/test_age_tts.cpp)
        target_link_libraries(magtile_age_tts_test PRIVATE magtile_core magtile_warnings)
        add_test(NAME age_tts
            COMMAND magtile_age_tts_test ${CMAKE_CURRENT_BINARY_DIR}/age_tts_test.db)
    endif()

    # 教程步进性能基准 (C++ microbench): 对小/中/大三个代表模型逐步
    # 计时 nextStep / goToStep + 渲染层每步查询, 输出每步 ms 与 P95;
    # 任一步中位数或 P95 超出预算 (默认 500ms/步) 即退出码 1。
    # 无 GPU 的 CI 不受影响 (纯 CPU); 负载不稳的环境可用
    # MAGTILE_BENCH_BUDGET_MS 放宽或 MAGTILE_BENCH_SKIP=1 跳过 (退出码
    # 77 = SKIP)。详见 docs/TESTING.md 3.16 节。
    if(EXISTS ${MAGTILE_TESTS_DIR}/bench_tutorial_step.cpp)
        add_executable(magtile_bench_tutorial tests/bench_tutorial_step.cpp)
        target_link_libraries(magtile_bench_tutorial PRIVATE magtile_core magtile_warnings)
        add_test(NAME bench_tutorial_step
            COMMAND magtile_bench_tutorial
                ${MAGTILE_DATA_DIR}/models/beach_hut_01.json
                ${MAGTILE_DATA_DIR}/models/castle_foundation_01.json
                ${MAGTILE_DATA_DIR}/models/skyscraper_01.json)
        set_tests_properties(bench_tutorial_step PROPERTIES SKIP_RETURN_CODE 77)
    endif()

    # 模型库目录对账: model_catalog.json 卡片元数据 (名称/难度/片数/步数)
    # 必须与模型文件一致, 防止商业版模型库界面展示信息漂移
    add_test(NAME library_catalog_check
        COMMAND magtile_app library --data-dir ${MAGTILE_DATA_DIR}
            --db ${CMAKE_CURRENT_BINARY_DIR}/library_cli_smoke.db)

    # 每个模型单独注册 validate / tutorial 用例, 便于精确定位失败模型。
    # CONFIGURE_DEPENDS: 新增模型 JSON 时自动重新 glob, 无需手工改 CMake。
    file(GLOB MAGTILE_MODEL_FILES CONFIGURE_DEPENDS ${MAGTILE_DATA_DIR}/models/*.json)
    foreach(model_file IN LISTS MAGTILE_MODEL_FILES)
        get_filename_component(model_name ${model_file} NAME_WE)
        add_test(NAME validate_${model_name}
            COMMAND magtile_app validate ${model_file} --data-dir ${MAGTILE_DATA_DIR})
        add_test(NAME tutorial_${model_name}
            COMMAND magtile_app tutorial ${model_file} --data-dir ${MAGTILE_DATA_DIR})
    endforeach()

    # 弱磁严格档回归 (--profile strict): 旗舰模型必须在 strict_consumer
    # 档位 (悬挂额定 120g/单位边长 + 安全系数 0.7, 面向磁力较弱的品牌与
    # 磁力衰减的旧片) 下依然全绿 —— 保证核心内容换弱磁品牌也搭得起来,
    # 参数依据见 docs/PHYSICS_RULES.md 第 5 节 "宁严勿松"。
    foreach(flagship IN ITEMS castle_foundation_01 eiffel_tower_01 tokyo_tower_01)
        add_test(NAME validate_strict_${flagship}
            COMMAND magtile_app validate ${MAGTILE_DATA_DIR}/models/${flagship}.json
                --data-dir ${MAGTILE_DATA_DIR} --profile strict)
    endforeach()

    # 脚本类测试 (bash): 模型库全量质检 / 教程完整性 / 物理负例
    # 各脚本按存在性注册, 便于测试资产分批合入时仓库始终可配置。
    find_program(MAGTILE_BASH bash)
    if(MAGTILE_BASH)
        # 全量质检: 逐一 validate + 报告片数步数 + 拒绝 < 40 片的小模型
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_all_models.sh)
            add_test(NAME all_models_quality_gate
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_all_models.sh
                    $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR} 40)
        endif()

        # 教程完整性: 静态逐步累加走查 + CLI 教程引擎实际跑一遍
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_tutorial_integrity.sh)
            add_test(NAME tutorial_integrity
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_tutorial_integrity.sh
                    $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR})
        endif()

        # 磁力片库存 CLI: set/show/match 全流程 + 非法输入拒绝 +
        # BOM 匹配边界 (满配全库能搭 / 全 0 库存能搭数为 0)
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_inventory_cli.sh)
            add_test(NAME inventory_cli
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_inventory_cli.sh
                    $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR})
        endif()

        # 物理负例: 这些夹具物理上不成立 (或数据非法), validate 必须
        # 按各夹具旁 .expected sidecar 声明的级别报告 —— error 级以
        # 非零退出码拒绝, warning 级零退出但必须输出 [警告] 行 (断言
        # 由 test_physics_negative.sh 执行)。覆盖几何规则 R1~R4 (穿地/
        # 悬空/错位半搭/断开装配/倾覆/穿插)、静力与工艺规则 R5~R7
        # (悬挂超重/悬挂链过长/悬臂超限/封闭腔/顺序不可放)、R8 结构
        # 冗余 (单点失效/无环拓扑/无桁架高墙超限)、数据层 (非法片型)
        # 与教程中间态 (成品合法但半成品倾倒), 对应真实搭建中 "照着
        # 图纸搭却掉下来" 的失败模式 (部分由 tools/generate_test_models.py
        # 生成, 详见其 docstring)。夹具按目录 glob 自动注册, 新增负例
        # 只需放入 JSON + sidecar 后重新配置; 套件完整性 (必备清单/
        # sidecar 对应/正例非空) 由 physics_fixture_registry 关卡把守,
        # 误删夹具会让该关卡变红而不是让用例静默消失。
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_physics_fixture_registry.sh)
            add_test(NAME physics_fixture_registry
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_physics_fixture_registry.sh
                    ${MAGTILE_TESTS_DIR})
        endif()
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_physics_negative.sh)
            file(GLOB MAGTILE_NEGATIVE_FIXTURES CONFIGURE_DEPENDS
                ${MAGTILE_TESTS_DIR}/test_physics_negative/*.json)
            foreach(fixture_file IN LISTS MAGTILE_NEGATIVE_FIXTURES)
                get_filename_component(fixture_name ${fixture_file} NAME_WE)
                add_test(NAME physics_negative_${fixture_name}
                    COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_physics_negative.sh
                        $<TARGET_FILE:magtile_app> ${MAGTILE_DATA_DIR} ${fixture_file})
            endforeach()
        endif()

        # 档位参数文案回归 (2026-08-25 strict 巡检回填): R5 悬挂超重
        # 文案的安全系数必须跟随实际档位 (default 80% / strict 70%),
        # 不得硬编码 —— 防止内容作者按错误文案反推预算。
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_strict_profile_message.sh)
            add_test(NAME strict_profile_message
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_strict_profile_message.sh
                    $<TARGET_FILE:magtile_app> ${MAGTILE_DATA_DIR}
                    ${MAGTILE_TESTS_DIR}/test_physics_negative/hanging_chain_overload.json)
        endif()

        # 物理正例: 处于承载预算之内的合法结构, validate 必须放行
        # (防止 R5/R6 静力规则矫枉过正, 误杀磁力片的常规玩法)。
        # 执行器额外断言输出包含 "可发布" 结论, 确保走到完整校验流程的成功出口。
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_physics_positive.sh)
            file(GLOB MAGTILE_POSITIVE_FIXTURES CONFIGURE_DEPENDS
                ${MAGTILE_TESTS_DIR}/test_physics_positive/*.json)
            foreach(fixture_file IN LISTS MAGTILE_POSITIVE_FIXTURES)
                get_filename_component(fixture_name ${fixture_file} NAME_WE)
                add_test(NAME physics_positive_${fixture_name}
                    COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_physics_positive.sh
                        $<TARGET_FILE:magtile_app> ${MAGTILE_DATA_DIR} ${fixture_file})
            endforeach()
        endif()

        # 设置 CLI 冒烟: set-age 写入 -> show 从同一数据库回读出启蒙模式
        # (覆盖 settings 命令解析、年龄映射与 SQLite 往返)
        add_test(NAME settings_cli_smoke
            COMMAND ${MAGTILE_BASH} -c
                "$<TARGET_FILE:magtile_app> settings set-age 4 --db ${CMAKE_CURRENT_BINARY_DIR}/settings_cli_smoke.db && $<TARGET_FILE:magtile_app> settings show --db ${CMAKE_CURRENT_BINARY_DIR}/settings_cli_smoke.db | grep -q 启蒙模式")

        # 跨端存档 CLI 读取对账 (E2E-17 自动化载体, 与 cross_platform_progress
        # 同一写入端): C++ 写入端构造样例存档 (年龄段/订阅/引导/完成/成就)
        # 后, 真实 CLI 二进制从同一 SQLite 读出完成记录、成就 id 与年龄段
        # 展示名 —— 验证 "一端写 → CLI 读" 的互通链路 (独立 db 文件,
        # 与 C++ 用例并行跑不互踩)
        if(TARGET magtile_cross_platform_test)
            add_test(NAME cross_platform_progress_cli
                COMMAND ${MAGTILE_BASH} -c
                    "$<TARGET_FILE:magtile_cross_platform_test> ${CMAKE_CURRENT_BINARY_DIR}/cross_platform_cli.db >/dev/null && $<TARGET_FILE:magtile_app> progress list --db ${CMAKE_CURRENT_BINARY_DIR}/cross_platform_cli.db | grep -q rainbow_bridge_01 && $<TARGET_FILE:magtile_app> progress list --db ${CMAKE_CURRENT_BINARY_DIR}/cross_platform_cli.db | grep -q three_models_completed && $<TARGET_FILE:magtile_app> settings show --db ${CMAKE_CURRENT_BINARY_DIR}/cross_platform_cli.db | grep -q 启蒙模式")
        endif()

        # 步骤朗读开关 CLI: set-tts on/off/1/0 与 show 对 "tts_enabled"
        # 键的读写 (默认开 / 跨进程持久化 / 非法值退出码 2 / 终端教程
        # --tts 遵守总开关), 与图形版页眉开关 / Qt 版设置页同一契约
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_settings_tts_cli.sh)
            add_test(NAME settings_tts_cli
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_settings_tts_cli.sh
                    $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR})
        endif()

        # 模型库 GUI 冒烟: 无头渲染模型库界面截图 + --open 深链教程会话
        # 并校验进度存档写入; 无显示环境自动降级为链接检查。
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_library_smoke.sh AND MAGTILE_BUILD_GL_RENDERER)
            add_test(NAME library_gui_smoke
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_library_smoke.sh
                    $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR})
            set_tests_properties(library_gui_smoke PROPERTIES TIMEOUT 300)
        endif()

        # 库存图形录入冒烟: 无头渲染录入界面截图 + --smoke-inventory
        # 自动驾驶经图形路径保存库存, 校验 CLI inventory show/match 从
        # 同一 SQLite 读到 (图形与 CLI 共库承诺); 无显示环境自动降级。
        if(EXISTS ${MAGTILE_TESTS_DIR}/test_inventory_gui.sh AND MAGTILE_BUILD_GL_RENDERER)
            add_test(NAME inventory_gui_smoke
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_inventory_gui.sh
                    $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR})
            set_tests_properties(inventory_gui_smoke PROPERTIES TIMEOUT 300)
        endif()
    else()
        message(WARNING "MagTile: 未找到 bash, 跳过脚本类测试注册")
    endif()

    # 反平凡检查 (Python): 拒绝片数过少 / 形状单一 / 纯平面的敷衍模型
    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(Python3_Interpreter_FOUND AND EXISTS ${MAGTILE_TESTS_DIR}/test_anti_trivial.py)
        add_test(NAME anti_trivial_models
            COMMAND ${Python3_EXECUTABLE} ${MAGTILE_TESTS_DIR}/test_anti_trivial.py
                ${MAGTILE_DATA_DIR}/models)
    endif()

    # 模型逻辑质检 (Python): 步骤粒度 (1~12 片/步)、中文说明、教程与成品
    # 对账、难度与片数区间匹配、BOM 备料清单一致性
    if(Python3_Interpreter_FOUND AND EXISTS ${MAGTILE_TESTS_DIR}/test_model_logic.py)
        add_test(NAME model_logic_gate
            COMMAND ${Python3_EXECUTABLE} ${MAGTILE_TESTS_DIR}/test_model_logic.py
                ${MAGTILE_DATA_DIR}/models)
    endif()

    # 逐步装配质检 (Python): 逐片零差错承诺 P1~P8 (docs/MODEL_QUALITY.md):
    # 片 id 唯一、每片恰好放置一次、高亮只引用已放置片、成品与教程严格
    # 集合对账 (无孤儿/无幽灵)、逐片空间连续性 (接地或磁力吸合)、
    # 步骤序号连续。纯数据层检查, 不依赖构建产物, 全库秒级。
    if(Python3_Interpreter_FOUND AND EXISTS ${MAGTILE_TESTS_DIR}/test_step_assembly.py)
        add_test(NAME step_assembly_gate
            COMMAND ${Python3_EXECUTABLE} ${MAGTILE_TESTS_DIR}/test_step_assembly.py
                ${MAGTILE_DATA_DIR}/models
                --catalog ${MAGTILE_DATA_DIR}/tile_catalog.json)
    endif()

    # 模型库唯一性 (Python): 结构签名 (WL 连接图指纹 + 片形直方图 +
    # 步骤节奏) 两两比对, sim > 0.85 判为换皮克隆并拒绝入库 (P10)
    if(Python3_Interpreter_FOUND AND EXISTS ${MAGTILE_TESTS_DIR}/test_library_uniqueness.py)
        add_test(NAME library_uniqueness_gate
            COMMAND ${Python3_EXECUTABLE} ${MAGTILE_TESTS_DIR}/test_library_uniqueness.py
                ${MAGTILE_DATA_DIR}/models
                --catalog ${MAGTILE_DATA_DIR}/tile_catalog.json)
    endif()
endif()
