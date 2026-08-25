# =============================================================
# MagTile Studio — 安装布局与 CPack 打包配置 (Windows 分发)
#
# 由根 CMakeLists.txt 在非 Android 平台 include (须在 magtile_app /
# magtile_studio_qt 目标定义之后)。版本号唯一来源是根
# project(MagTileStudio VERSION x.y.z), 本文件一律通过 PROJECT_VERSION*
# 引用, 不得另行硬编码。
#
# 生成器:
#   Windows   → NSIS 安装器 + 便携 ZIP (NSIS 为当前首选, 免费且
#               windows-latest CI 镜像自带 makensis);
#               WiX/MSI 走 packaging/Product.wxs 手工路径, 或
#               `cpack -G WIX` (需安装 WiX Toolset, 配置已就位)。
#   其它平台  → TGZ 归档, 用于在 Linux/macOS CI 上冒烟验证安装规则
#               与文件清单, 不作为正式分发物 (Linux 装有 makensis 时
#               也可 `cpack -G NSIS` 冒烟 NSIS 脚本本身)。
#
# 打包数据集开关 (决定随包分发的模型库范围):
#   -DMAGTILE_PACKAGE_MODEL_SET=full     全部模型库 (默认)
#   -DMAGTILE_PACKAGE_MODEL_SET=starter  精选入门子集 (免费层 30 模型,
#                                        清单 packaging/starter_models.txt)
#   -DMAGTILE_PACKAGE_MODEL_SET=<路径>   自定义清单文件 (格式同上)
# 子集模式在安装/打包阶段调用 tools/make_data_subset.py 装配数据
# (需要 Python3), 并同步过滤 model_catalog.json —— 运行时加载器对
# "目录登记了但文件缺失" 的条目直接报错, 两者必须一致。
#
# Qt 界面 (magtile_studio_qt) 的安装规则在 apps/desktop_qt/CMakeLists.txt
# 尾部 (仅 -DMAGTILE_BUILD_QT=ON 时生效), 本文件只负责其 NSIS 快捷方式。
#
# 用法 (详见 scripts/package_windows.md):
#   cmake --build build-win --config Release
#   cd build-win && cpack -G "NSIS;ZIP" -C Release
# =============================================================

# ---- 安装布局 ---------------------------------------------------
# <安装根>/
# ├── magtile_app.exe        主程序 (CLI + GUI 一体)
# ├── magtile_studio_qt.exe  Qt 商用界面 (仅 MAGTILE_BUILD_QT=ON; 含 Qt 运行库)
# ├── data/                  磁力片形状目录 + 模型库 (full 或子集, 运行必需)
# ├── licenses/              EULA (License.rtf) + 第三方许可声明
# ├── README.md
# └── vc_redist DLLs         MSVC CRT 运行库 (/MD 构建需要)
install(TARGETS magtile_app RUNTIME DESTINATION .)
install(FILES ${PROJECT_SOURCE_DIR}/README.md DESTINATION .)
install(FILES
    ${CMAKE_CURRENT_LIST_DIR}/License.rtf
    ${CMAKE_CURRENT_LIST_DIR}/THIRD_PARTY_NOTICES.md
    DESTINATION licenses)

if(MSVC)
    set(CMAKE_INSTALL_SYSTEM_RUNTIME_DESTINATION .)
    include(InstallRequiredSystemLibraries)
endif()

# ---- 数据集: 全库 或 清单子集 ------------------------------------
set(MAGTILE_PACKAGE_MODEL_SET "full" CACHE STRING
    "打包数据集: full=全部模型库; starter=精选入门子集; 或自定义清单文件路径")

if(MAGTILE_PACKAGE_MODEL_SET STREQUAL "full")
    install(DIRECTORY ${PROJECT_SOURCE_DIR}/data/ DESTINATION data)
    message(STATUS "MagTile: 打包数据集 = full (完整模型库)")
else()
    if(MAGTILE_PACKAGE_MODEL_SET STREQUAL "starter")
        set(_magtile_model_manifest "${CMAKE_CURRENT_LIST_DIR}/starter_models.txt")
    else()
        set(_magtile_model_manifest "${MAGTILE_PACKAGE_MODEL_SET}")
        if(NOT IS_ABSOLUTE "${_magtile_model_manifest}")
            set(_magtile_model_manifest "${PROJECT_SOURCE_DIR}/${_magtile_model_manifest}")
        endif()
    endif()
    if(NOT EXISTS "${_magtile_model_manifest}")
        message(FATAL_ERROR
            "MAGTILE_PACKAGE_MODEL_SET=${MAGTILE_PACKAGE_MODEL_SET}: 清单文件不存在 "
            "(${_magtile_model_manifest})。可选值: full / starter / 清单文件路径。")
    endif()

    # 子集装配脚本需要 Python3 (Windows: VS 自带的或 python.org 均可)
    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(NOT Python3_Interpreter_FOUND)
        message(FATAL_ERROR
            "MAGTILE_PACKAGE_MODEL_SET=${MAGTILE_PACKAGE_MODEL_SET} 需要 Python3 "
            "运行 tools/make_data_subset.py; 请安装 Python3 或改用 "
            "-DMAGTILE_PACKAGE_MODEL_SET=full。")
    endif()

    # 配置期快速校验: 清单里的模型必须真实存在, 拼写错误当场失败,
    # 不要拖到打包阶段才炸。完整校验 (含目录登记一致性) 由脚本负责。
    file(STRINGS "${_magtile_model_manifest}" _magtile_manifest_lines)
    set(_magtile_manifest_missing "")
    set(_magtile_subset_count 0)
    foreach(_magtile_line IN LISTS _magtile_manifest_lines)
        string(REGEX REPLACE "#.*" "" _magtile_line "${_magtile_line}")
        string(STRIP "${_magtile_line}" _magtile_line)
        if(_magtile_line STREQUAL "")
            continue()
        endif()
        math(EXPR _magtile_subset_count "${_magtile_subset_count} + 1")
        if(NOT EXISTS "${PROJECT_SOURCE_DIR}/data/models/${_magtile_line}.json")
            list(APPEND _magtile_manifest_missing "${_magtile_line}")
        endif()
    endforeach()
    if(_magtile_manifest_missing)
        message(FATAL_ERROR
            "打包清单 ${_magtile_model_manifest} 引用了不存在的模型: "
            "${_magtile_manifest_missing}")
    endif()
    message(STATUS
        "MagTile: 打包数据集 = 模型子集 (${_magtile_subset_count} 个, 清单 ${_magtile_model_manifest})")

    # 清单或目录变化时自动触发重新配置, 防止用旧配置打出过期的包
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${_magtile_model_manifest}"
        "${PROJECT_SOURCE_DIR}/data/model_catalog.json")

    # 安装/打包阶段装配子集: 直接产出到安装前缀的 data/, 每次 install
    # 都重新装配 (脚本会整体重建输出目录), 不存在过期 staging 问题。
    install(CODE "
        set(_magtile_subset_dest \"\$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/data\")
        message(STATUS \"MagTile: 装配模型子集 -> \${_magtile_subset_dest}\")
        execute_process(
            COMMAND \"${Python3_EXECUTABLE}\" \"${PROJECT_SOURCE_DIR}/tools/make_data_subset.py\"
                --data-dir \"${PROJECT_SOURCE_DIR}/data\"
                --manifest \"${_magtile_model_manifest}\"
                --out-dir \"\${_magtile_subset_dest}\"
            RESULT_VARIABLE _magtile_subset_rc)
        if(NOT _magtile_subset_rc EQUAL 0)
            message(FATAL_ERROR \"MagTile: 模型子集装配失败 (make_data_subset.py 退出码 \${_magtile_subset_rc})\")
        endif()
    ")
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

# ---- NSIS 安装器 -------------------------------------------------
# 与平台无关地配置 (Linux 装 makensis 也能 `cpack -G NSIS` 冒烟脚本),
# 但只有 Windows 把 NSIS 列入默认生成器。
set(CPACK_NSIS_DISPLAY_NAME "MagTile Studio")
set(CPACK_NSIS_PACKAGE_NAME "MagTile Studio")
set(CPACK_NSIS_ENABLE_UNINSTALL_BEFORE_INSTALL ON)
set(CPACK_NSIS_MODIFY_PATH OFF)
# 开始菜单快捷方式直达模型库主界面; SetOutPath 保证工作目录为
# 安装根, 使默认 --data-dir data 相对路径可用。Qt 界面在构建时
# 追加第二个快捷方式。
set(_magtile_nsis_create_icons
    "SetOutPath '$INSTDIR'
     CreateShortCut '$SMPROGRAMS\\\\$STARTMENU_FOLDER\\\\MagTile Studio.lnk' '$INSTDIR\\\\magtile_app.exe' 'library --gui'")
set(_magtile_nsis_delete_icons
    "Delete '$SMPROGRAMS\\\\$START_MENU\\\\MagTile Studio.lnk'")
if(TARGET magtile_studio_qt)
    string(APPEND _magtile_nsis_create_icons "
     CreateShortCut '$SMPROGRAMS\\\\$STARTMENU_FOLDER\\\\MagTile Studio (Qt).lnk' '$INSTDIR\\\\magtile_studio_qt.exe'")
    string(APPEND _magtile_nsis_delete_icons "
     Delete '$SMPROGRAMS\\\\$START_MENU\\\\MagTile Studio (Qt).lnk'")
endif()
set(CPACK_NSIS_CREATE_ICONS_EXTRA "${_magtile_nsis_create_icons}")
set(CPACK_NSIS_DELETE_ICONS_EXTRA "${_magtile_nsis_delete_icons}")
# TODO(发布前): 补充 MUI 图标/横幅素材 (packaging/icon.ico 等)
#   set(CPACK_NSIS_MUI_ICON   "${CMAKE_CURRENT_LIST_DIR}/icon.ico")
#   set(CPACK_NSIS_MUI_UNIICON "${CMAKE_CURRENT_LIST_DIR}/icon.ico")

# ---- WiX / MSI (cpack -G WIX 时生效) ------------------------------
# UpgradeCode 必须永久固定 (与 Product.wxs 中一致), 才能原地升级;
# 换掉它等于发布一个"新产品", 旧版本将无法被替换。
set(CPACK_WIX_UPGRADE_GUID "6FE5F9D7-79A7-4829-B13A-8C3B1517CA61")
set(CPACK_WIX_ROOT_FEATURE_TITLE "MagTile Studio")
set(CPACK_WIX_CULTURES "zh-CN;en-US")
# CMake ≥ 3.27 可切换 WiX v4 工具链: set(CPACK_WIX_VERSION 4)

if(WIN32)
    set(CPACK_PACKAGE_FILE_NAME "MagTileStudio-${PROJECT_VERSION}-win64")
    set(CPACK_GENERATOR "ZIP;NSIS")
else()
    # 非 Windows 平台仅为脚手架冒烟验证: cpack -G TGZ
    set(CPACK_PACKAGE_FILE_NAME
        "MagTileStudio-${PROJECT_VERSION}-${CMAKE_SYSTEM_NAME}")
    set(CPACK_GENERATOR "TGZ")
endif()

include(CPack)
