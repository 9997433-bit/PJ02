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

# 渲染后端开关: 第一阶段默认关闭, 落地 GLFW + OpenGL 后开启
option(MAGTILE_BUILD_GL_RENDERER "构建 GLFW + OpenGL 渲染后端 (需要 GLFW)" OFF)
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
)
target_include_directories(magtile_core
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)
target_link_libraries(magtile_core PRIVATE magtile_warnings)

# ---- 命令行应用 -------------------------------------------------
add_executable(magtile_app src/app/main.cpp)
target_link_libraries(magtile_app PRIVATE magtile_core magtile_warnings)

# ---- 测试: 用示例模型跑完整质检流程 -----------------------------
if(MAGTILE_BUILD_TESTS)
    enable_testing()
    add_test(NAME validate_castle_foundation_01
        COMMAND magtile_app validate
            ${CMAKE_CURRENT_SOURCE_DIR}/data/models/castle_foundation_01.json
            --data-dir ${CMAKE_CURRENT_SOURCE_DIR}/data)
    add_test(NAME print_tile_catalog
        COMMAND magtile_app catalog --data-dir ${CMAKE_CURRENT_SOURCE_DIR}/data)
    add_test(NAME tutorial_walkthrough
        COMMAND magtile_app tutorial
            ${CMAKE_CURRENT_SOURCE_DIR}/data/models/castle_foundation_01.json
            --data-dir ${CMAKE_CURRENT_SOURCE_DIR}/data)
endif()
