# =============================================================
# MagTile Studio - Android JNI 共享库 (脚手架)
#
# 产物: libmagtile_core.so = 静态 magtile_core + JNI 包装层。
# 两种进入方式 (详见本目录 README.md):
#   1. 由仓库根 CMakeLists.txt 经 add_subdirectory(platforms) 进入
#      (使用 NDK 工具链文件交叉编译整个仓库时);
#   2. 由 Gradle externalNativeBuild 直接指向本文件 (独立入口)。
# =============================================================
cmake_minimum_required(VERSION 3.22)

# 独立入口 (Gradle) 时需要自行声明 project 并挂载仓库根目录。
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
    project(MagTileStudioAndroid LANGUAGES CXX)
endif()

if(NOT ANDROID)
    # 本目录只在 NDK 工具链下有意义 (工具链文件会定义 ANDROID)。
    message(STATUS "MagTile: 未检测到 Android NDK 工具链, 跳过 platforms/android")
    return()
endif()

if(NOT TARGET magtile_core)
    # 桌面渲染后端 (GLFW/ImGui) 与 CTest 不适用于 Android, 强制关闭。
    set(MAGTILE_BUILD_GL_RENDERER OFF CACHE BOOL "" FORCE)
    set(MAGTILE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../.. magtile_root)
endif()

# 独立入口时, 上面的 add_subdirectory 会经根目录的
# add_subdirectory(platforms) 重入本文件并完成 JNI 目标定义,
# 此处直接结束, 避免重复定义 magtile_android。
if(TARGET magtile_android)
    return()
endif()

# NDK 默认已开启 -fPIC, 这里显式声明以防宿主侧配置覆盖。
set_target_properties(magtile_core PROPERTIES POSITION_INDEPENDENT_CODE ON)

add_library(magtile_android SHARED
    jni/magtile_jni.cpp
)
# Kotlin 侧以 System.loadLibrary("magtile_core") 加载, 故产物命名为
# libmagtile_core.so (与桌面静态库 libmagtile_core.a 互不冲突)。
set_target_properties(magtile_android PROPERTIES OUTPUT_NAME magtile_core)
# nlohmann/json: listModels() 序列化模型库目录为 JSON 字符串
target_include_directories(magtile_android
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../../third_party
)
target_link_libraries(magtile_android
    PRIVATE
        magtile_core
        magtile_warnings
        log     # __android_log_print
)
