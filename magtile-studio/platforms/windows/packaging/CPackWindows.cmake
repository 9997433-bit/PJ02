# =============================================================
# MagTile Studio — 安装布局与 CPack 打包配置 (Windows 分发脚手架)
#
# 由根 CMakeLists.txt 在非 Android 平台 include (须在 magtile_app
# 目标定义之后)。版本号唯一来源是根 project(MagTileStudio VERSION x.y.z),
# 本文件一律通过 PROJECT_VERSION* 引用, 不得另行硬编码。
#
# 生成器:
#   Windows   → NSIS 安装器 + 便携 ZIP (NSIS 为当前首选, 免费且
#               windows-latest CI 镜像自带 makensis);
#               WiX/MSI 走 packaging/Product.wxs 手工路径 (见下), 或
#               `cpack -G WIX` (需安装 WiX Toolset, 配置已就位)。
#   其它平台  → TGZ 归档, 仅用于在 Linux/macOS 上冒烟验证安装规则,
#               不作为正式分发物。
#
# 用法 (详见 scripts/package_windows.md):
#   cmake --build build-win --config Release
#   cd build-win && cpack -G "NSIS;ZIP" -C Release
# =============================================================

# ---- 安装布局 ---------------------------------------------------
# <安装根>/
# ├── magtile_app.exe      主程序 (CLI + GUI 一体)
# ├── data/                磁力片形状目录 + 模型库 (运行必需)
# ├── README.md
# └── vc_redist DLLs       MSVC CRT 运行库 (/MD 构建需要)
install(TARGETS magtile_app RUNTIME DESTINATION .)
install(DIRECTORY ${PROJECT_SOURCE_DIR}/data/ DESTINATION data)
install(FILES ${PROJECT_SOURCE_DIR}/README.md DESTINATION .)

if(MSVC)
    set(CMAKE_INSTALL_SYSTEM_RUNTIME_DESTINATION .)
    include(InstallRequiredSystemLibraries)
endif()

# ---- CPack 通用元数据 (版本号取自 project() 声明) ----------------
set(CPACK_PACKAGE_NAME "MagTileStudio")
set(CPACK_PACKAGE_VENDOR "MagTile Studio Team")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "${PROJECT_DESCRIPTION}")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_VERSION_MAJOR "${PROJECT_VERSION_MAJOR}")
set(CPACK_PACKAGE_VERSION_MINOR "${PROJECT_VERSION_MINOR}")
set(CPACK_PACKAGE_VERSION_PATCH "${PROJECT_VERSION_PATCH}")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "MagTile Studio")
# 许可文本 (RTF 同时满足 NSIS 与 WiX 的许可页要求; 当前为占位文本,
# 正式发布前须替换为法务审定版本)
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_LIST_DIR}/License.rtf")
set(CPACK_RESOURCE_FILE_README "${PROJECT_SOURCE_DIR}/README.md")
# 构建产物是把源码/构建目录整个打进包里的常见事故来源, 显式关掉
set(CPACK_SOURCE_IGNORE_FILES "/build.*/;/\\\\.git/")

if(WIN32)
    set(CPACK_PACKAGE_FILE_NAME "MagTileStudio-${PROJECT_VERSION}-win64")
    set(CPACK_GENERATOR "ZIP;NSIS")

    # ---- NSIS 安装器 --------------------------------------------
    set(CPACK_NSIS_DISPLAY_NAME "MagTile Studio")
    set(CPACK_NSIS_PACKAGE_NAME "MagTile Studio")
    set(CPACK_NSIS_ENABLE_UNINSTALL_BEFORE_INSTALL ON)
    set(CPACK_NSIS_MODIFY_PATH OFF)
    # 开始菜单快捷方式直达模型库主界面; SetOutPath 保证工作目录为
    # 安装根, 使默认 --data-dir data 相对路径可用
    set(CPACK_NSIS_CREATE_ICONS_EXTRA
        "SetOutPath '$INSTDIR'
         CreateShortCut '$SMPROGRAMS\\\\$STARTMENU_FOLDER\\\\MagTile Studio.lnk' '$INSTDIR\\\\magtile_app.exe' 'library --gui'")
    set(CPACK_NSIS_DELETE_ICONS_EXTRA
        "Delete '$SMPROGRAMS\\\\$START_MENU\\\\MagTile Studio.lnk'")
    # TODO(发布前): 补充 MUI 图标/横幅素材 (packaging/icon.ico 等)
    #   set(CPACK_NSIS_MUI_ICON   "${CMAKE_CURRENT_LIST_DIR}/icon.ico")
    #   set(CPACK_NSIS_MUI_UNIICON "${CMAKE_CURRENT_LIST_DIR}/icon.ico")

    # ---- WiX / MSI (cpack -G WIX 时生效) -------------------------
    # UpgradeCode 必须永久固定 (与 Product.wxs 中一致), 才能原地升级;
    # 换掉它等于发布一个"新产品", 旧版本将无法被替换。
    set(CPACK_WIX_UPGRADE_GUID "6FE5F9D7-79A7-4829-B13A-8C3B1517CA61")
    set(CPACK_WIX_ROOT_FEATURE_TITLE "MagTile Studio")
    set(CPACK_WIX_CULTURES "zh-CN;en-US")
    # CMake ≥ 3.27 可切换 WiX v4 工具链: set(CPACK_WIX_VERSION 4)
else()
    # 非 Windows 平台仅为脚手架冒烟验证: cpack -G TGZ
    set(CPACK_PACKAGE_FILE_NAME
        "MagTileStudio-${PROJECT_VERSION}-${CMAKE_SYSTEM_NAME}")
    set(CPACK_GENERATOR "TGZ")
endif()

include(CPack)
