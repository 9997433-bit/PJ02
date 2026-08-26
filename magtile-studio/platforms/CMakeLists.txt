# =============================================================
# MagTile Studio - 平台外壳分发
#   android/  Android NDK 交叉编译时构建 JNI 共享库
#   windows/  打包资产与文档; 其 packaging/CPackWindows.cmake 由根
#             CMakeLists 在非 Android 平台 include (CPack 安装器脚手架)
# =============================================================

if(ANDROID)
    add_subdirectory(android)
endif()
