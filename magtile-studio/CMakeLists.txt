# =============================================================
# MagTile Studio - 磁力片搭建教程应用
# 构建要求: CMake >= 3.20, 支持 C++20 的编译器
#   (MSVC 2022 / Clang 14+ / GCC 11+, 覆盖 Windows / macOS / Linux)
# =============================================================
cmake_minimum_required(VERSION 3.20)

project(MagTileStudio
    VERSION 0.1.0
    DESCRIPTION "MagTile Studio - Magnetic tile building tutorial application"
    LANGUAGES CXX)

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

# ---- 编译警告 --------------------------------------------------
add_library(magtile_warnings INTERFACE)
if(MSVC)
    target_compile_options(magtile_warnings INTERFACE /W4 /utf-8)
else()
    target_compile_options(magtile_warnings INTERFACE -Wall -Wextra -Wpedantic)
endif()

# ---- 核心库: core + physics + tutorial + render 接口 -----------
add_library(magtile_core STATIC
    src/core/types.cpp
    src/core/model_definition.cpp
    src/core/tile_catalog.cpp
    src/core/json_io.cpp
    src/physics/geometry.cpp
    src/physics/physics_validator.cpp
    src/tutorial/tutorial_engine.cpp
    src/render/null_renderer.cpp
    src/render/orbit_camera.cpp
)
target_include_directories(magtile_core
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)
target_link_libraries(magtile_core PRIVATE magtile_warnings)

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
        src/render/gl/gl_api.cpp
        src/render/gl/gl_renderer.cpp
    )
    target_link_libraries(magtile_render_gl
        PUBLIC magtile_core
        PRIVATE magtile_imgui glfw magtile_warnings
    )
    # 链接方可据此宏启用 --gui 代码路径
    target_compile_definitions(magtile_render_gl PUBLIC MAGTILE_HAS_GL_RENDERER=1)
endif()

# ---- 命令行应用 -------------------------------------------------
add_executable(magtile_app src/app/main.cpp)
target_link_libraries(magtile_app PRIVATE magtile_core magtile_warnings)
if(MAGTILE_BUILD_GL_RENDERER)
    target_link_libraries(magtile_app PRIVATE magtile_render_gl)
endif()

# ---- 测试 (详见 docs/TESTING.md) --------------------------------
if(MAGTILE_BUILD_TESTS)
    enable_testing()

    set(MAGTILE_DATA_DIR  ${CMAKE_CURRENT_SOURCE_DIR}/data)
    set(MAGTILE_TESTS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/tests)

    add_test(NAME print_tile_catalog
        COMMAND magtile_app catalog --data-dir ${MAGTILE_DATA_DIR})

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

    # 脚本类测试 (bash): 模型库全量质检 / 教程完整性 / 物理负例
    find_program(MAGTILE_BASH bash)
    if(MAGTILE_BASH)
        # 全量质检: 逐一 validate + 报告片数步数 + 拒绝 < 40 片的小模型
        add_test(NAME all_models_quality_gate
            COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_all_models.sh
                $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR} 40)

        # 教程完整性: 静态逐步累加走查 + CLI 教程引擎实际跑一遍
        add_test(NAME tutorial_integrity
            COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_tutorial_integrity.sh
                $<TARGET_FILE:magtile_app> ${CMAKE_CURRENT_SOURCE_DIR})

        # 物理负例: 这些夹具物理上不成立, validate 必须以非零退出码拒绝,
        # 且必须报出对应的错误码 (由 test_physics_negative.sh 断言)。
        foreach(pair IN ITEMS
                "floating_tile\;floating_tile"
                "unstable_cantilever\;unstable_center_of_mass"
                "overlapping_tiles\;tile_overlap")
            list(GET pair 0 fixture_name)
            list(GET pair 1 expected_code)
            add_test(NAME physics_negative_${fixture_name}
                COMMAND ${MAGTILE_BASH} ${MAGTILE_TESTS_DIR}/test_physics_negative.sh
                    $<TARGET_FILE:magtile_app> ${MAGTILE_DATA_DIR}
                    ${MAGTILE_TESTS_DIR}/test_physics_negative/${fixture_name}.json
                    ${expected_code})
        endforeach()
    else()
        message(WARNING "MagTile: 未找到 bash, 跳过脚本类测试注册")
    endif()

    # 反平凡检查 (Python): 拒绝片数过少 / 形状单一 / 纯平面的敷衍模型
    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(Python3_Interpreter_FOUND)
        add_test(NAME anti_trivial_models
            COMMAND ${Python3_EXECUTABLE} ${MAGTILE_TESTS_DIR}/test_anti_trivial.py
                ${MAGTILE_DATA_DIR}/models)
    else()
        message(WARNING "MagTile: 未找到 Python3, 跳过反平凡模型检查注册")
    endif()
endif()
