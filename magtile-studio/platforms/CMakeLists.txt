# =============================================================
# MagTile Studio - 平台外壳分发
#   android/  Android NDK 交叉编译时构建 JNI 共享库
#   windows/  仅含打包脚本与文档, 不参与 CMake 构建
# =============================================================

if(ANDROID)
    add_subdirectory(android)
endif()
