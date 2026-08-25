# =============================================================
# MagTile Studio — Windows Qt 安装包实机冒烟脚本 (QT-6)
#
# 在 Windows 构建机上一键走完 "检测环境 -> 构建 -> 测试 -> CPack ->
# windeployqt -> 包内清单断言 -> 无头启动冒烟" 全链路, 与操作手册
# scripts/package_qt_desktop.md 的第三/四/五/九节逐条对应;
# 实机验收清单 (人工项: 干净机器安装/双击/进教程) 见该手册第十一节。
#
# 用法 (仓库根目录执行; PowerShell 5.1 与 pwsh 7 均可):
#   powershell -ExecutionPolicy Bypass -File scripts\smoke_qt_windows.ps1 `
#       -QtDir C:\Qt\6.7.2\msvc2022_64
#
#   常用参数:
#     -QtDir <路径>    Qt 套件根 (含 bin\qmake.exe); 缺省自动扫描
#                      C:\Qt\6.*\msvc*_64 取最高版本
#     -BuildDir <路径> 构建目录 (默认 build-win-qt-smoke)
#     -QtOnly          打 Qt-only 包 (-DMAGTILE_PACKAGE_QT_ONLY=ON,
#                      包内无 magtile_app, 包名 -qt 后缀)
#     -ModelSet <值>   full / starter / 自定义清单路径 (默认 full)
#     -Generator <值>  CMake 生成器 (默认 "Visual Studio 17 2022")
#     -SkipTests       跳过 ctest (仅打包链路排障时用)
#     -DryRun          不构建不打包: 输出环境检测报告 + 将执行的命令
#                      计划, 并对"清单断言逻辑"用模拟包目录自检
#                      (含故意抽掉 qwindows.dll 的失败注入)。
#                      Linux/macOS 的 pwsh 上也可运行本模式。
#
# 退出码: 0 = 全部通过; 非 0 = 任一环节失败 (信息见末尾 FAILED 行)。
# =============================================================

[CmdletBinding()]
param(
    [string]$QtDir = "",
    [string]$BuildDir = "build-win-qt-smoke",
    [switch]$QtOnly,
    [string]$ModelSet = "full",
    [string]$Generator = "Visual Studio 17 2022",
    [switch]$SkipTests,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Windows PowerShell 5.1 没有 $IsWindows 自动变量, 统一用环境变量判断
$script:OnWindows = ($env:OS -eq 'Windows_NT')
$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Write-Step([string]$Msg) { Write-Host "`n==> $Msg" -ForegroundColor Cyan }
function Write-Ok([string]$Msg)   { Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Bad([string]$Msg)  { Write-Host "  [!!] $Msg" -ForegroundColor Red }
function Write-Info([string]$Msg) { Write-Host "  $Msg" }

function Fail([string]$Msg) {
    Write-Host "`nFAILED: $Msg" -ForegroundColor Red
    exit 1
}

# 外部命令封装: 回显命令行, 非零退出码即失败
function Invoke-Checked([string]$Desc, [string]$Exe, [string[]]$CmdArgs) {
    Write-Info "$ $Exe $($CmdArgs -join ' ')"
    & $Exe @CmdArgs
    if ($LASTEXITCODE -ne 0) { Fail "$Desc 失败 (退出码 $LASTEXITCODE)" }
}

# ---------------------------------------------------------------
# 环境检测 (第一节): cmake/cpack/Qt 套件/windeployqt/NSIS/VS/Python
# DryRun 下缺什么只报告不失败; 实跑下缺必需项当场失败。
# ---------------------------------------------------------------
function Find-InPath([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Find-QtKit([string]$Preferred) {
    if ($Preferred) {
        $qmake = Join-Path $Preferred 'bin\qmake.exe'
        if (-not $script:OnWindows) { $qmake = Join-Path $Preferred 'bin/qmake' }
        if (Test-Path $qmake) { return (Resolve-Path $Preferred).Path }
        return $null
    }
    if (-not $script:OnWindows) { return $null }
    # 官方安装器默认布局: C:\Qt\<版本>\msvc*_64
    $roots = @('C:\Qt')
    if ($env:QTDIR) { $roots = @($env:QTDIR) + $roots }
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        $kits = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^6\.' } |
            Sort-Object { [version]$_.Name } -Descending
        foreach ($ver in $kits) {
            $msvc = Get-ChildItem -Path $ver.FullName -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '^msvc.*_64$' } | Select-Object -First 1
            if ($msvc -and (Test-Path (Join-Path $msvc.FullName 'bin\qmake.exe'))) {
                return $msvc.FullName
            }
        }
    }
    return $null
}

function Get-QtVersion([string]$Kit) {
    $qmake = Join-Path $Kit 'bin\qmake.exe'
    if (-not $script:OnWindows) { $qmake = Join-Path $Kit 'bin/qmake' }
    $raw = (& $qmake -query QT_VERSION 2>$null)
    if ($LASTEXITCODE -eq 0 -and $raw) { return [version]($raw.Trim()) }
    return $null
}

function Find-Nsis {
    $p = Find-InPath 'makensis'
    if ($p) { return $p }
    if ($script:OnWindows) {
        foreach ($pf in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
            if (-not $pf) { continue }
            $cand = Join-Path $pf 'NSIS\makensis.exe'
            if (Test-Path $cand) { return $cand }
        }
    }
    return $null
}

function Find-VisualStudio {
    if (-not $script:OnWindows) { return $null }
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) { return $null }
    $path = & $vswhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath 2>$null
    if ($path) { return ($path | Select-Object -First 1) }
    return $null
}

# ---------------------------------------------------------------
# 包内清单断言 (第五/九节口径): 对"解包后的安装目录"逐项核对。
# 返回失败项字符串数组 (空 = 通过); DryRun 自检与实跑共用本函数。
#   -RequireQtRuntime: Qt 运行库应已在目录内 (windeployqt 之后 /
#                      Qt >= 6.5 自动部署包) 时置 $true
# ---------------------------------------------------------------
function Test-PackageManifest {
    param(
        [Parameter(Mandatory)][string]$Root,
        [bool]$IsQtOnly,
        [int]$ExpectedModelCount,   # <=0 表示只要求 >=1 且目录一致
        [bool]$RequireQtRuntime,
        [bool]$RequireCrt = $true
    )
    $bad = @()
    function local:Need([string]$Rel) {
        if (-not (Test-Path (Join-Path $Root $Rel))) { return $Rel }
        return $null
    }

    # -- 应用本体与随包文件 --
    $core = @('magtile_studio_qt.exe', 'README.md',
              'licenses/License.rtf', 'licenses/THIRD_PARTY_NOTICES.md',
              'data/tile_catalog.json', 'data/model_catalog.json')
    foreach ($rel in $core) { $m = Need $rel; if ($m) { $bad += "缺少 $m" } }
    if ($IsQtOnly) {
        if (Test-Path (Join-Path $Root 'magtile_app.exe')) {
            $bad += 'Qt-only 包内不应存在 magtile_app.exe'
        }
    } else {
        $m = Need 'magtile_app.exe'; if ($m) { $bad += "缺少 $m (并存包)" }
    }

    # -- 数据目录: 模型数量 + 目录登记一致性 (登记了就必须存在) --
    $modelsDir = Join-Path $Root 'data/models'
    $models = @()
    if (Test-Path $modelsDir) {
        $models = @(Get-ChildItem $modelsDir -Filter '*.json' -File)
    } else { $bad += '缺少 data/models/' }
    if ($ExpectedModelCount -gt 0 -and $models.Count -ne $ExpectedModelCount) {
        $bad += "data/models 应有 $ExpectedModelCount 个模型, 实际 $($models.Count)"
    } elseif ($ExpectedModelCount -le 0 -and $models.Count -lt 1) {
        $bad += 'data/models 为空'
    }
    $thumbsDir = Join-Path $Root 'data/thumbnails'
    if (-not (Test-Path $thumbsDir) -or
        @(Get-ChildItem $thumbsDir -Filter '*.png' -File -ErrorAction SilentlyContinue).Count -lt 1) {
        $bad += 'data/thumbnails 缺失或为空'
    }
    $catalogPath = Join-Path $Root 'data/model_catalog.json'
    if (Test-Path $catalogPath) {
        try {
            $catalog = Get-Content $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $entries = @($catalog.models)
            foreach ($e in $entries) {
                if (-not (Test-Path (Join-Path $Root "data/$($e.file)"))) {
                    $bad += "目录登记的模型文件缺失: data/$($e.file) (加载器会当场报错)"
                }
            }
            if ($ExpectedModelCount -gt 0 -and $entries.Count -ne $ExpectedModelCount) {
                $bad += "model_catalog.json 应恰登记 $ExpectedModelCount 条 (子集须同步过滤), 实际 $($entries.Count)"
            }
        } catch { $bad += "model_catalog.json 解析失败: $($_.Exception.Message)" }
    }

    # -- Qt 运行库 (windeployqt / Qt >= 6.5 自动部署之后) --
    if ($RequireQtRuntime) {
        foreach ($dll in @('Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Qml.dll',
                           'Qt6Quick.dll', 'Qt6QuickControls2.dll', 'Qt6OpenGL.dll')) {
            $m = Need $dll; if ($m) { $bad += "缺少 Qt 运行库 $m" }
        }
        $m = Need 'platforms/qwindows.dll'
        if ($m) { $bad += '缺少平台插件 platforms/qwindows.dll (启动即报 "no Qt platform plugin")' }
        if (-not (Test-Path (Join-Path $Root 'qml/QtQuick'))) {
            $bad += '缺少 QML 模块树 qml/QtQuick/ (windeployqt 忘带 --qmldir 的典型症状, 启动黑屏)'
        }
        if ($RequireCrt) {
            $crt = @(Get-ChildItem $Root -Filter 'vcruntime140*.dll' -File -ErrorAction SilentlyContinue)
            if ($crt.Count -lt 1) {
                $bad += '缺少 vcruntime140*.dll (MSVC CRT; 干净机器上启动报 VCRUNTIME140 缺失)'
            }
        }
    }
    return $bad
}

function Report-Manifest($Failures, [string]$What) {
    # PowerShell 会把空/单元素数组拆散, 统一重包装再计数
    $list = @($Failures | Where-Object { $_ })
    if ($list.Count -eq 0) { Write-Ok "$What 清单断言全部通过"; return $true }
    foreach ($f in $list) { Write-Bad $f }
    return $false
}

# ---------------------------------------------------------------
# 期望模型数: full 不锁死数量 (只验目录一致性), starter/自定义清单
# 按清单行数 (去注释/空行) 精确断言
# ---------------------------------------------------------------
function Get-ExpectedModelCount([string]$Set) {
    if ($Set -eq 'full') { return 0 }
    $manifest = $Set
    if ($Set -eq 'starter') {
        $manifest = Join-Path $script:RepoRoot 'platforms/windows/packaging/starter_models.txt'
    }
    if (-not (Test-Path $manifest)) { Fail "模型清单不存在: $manifest" }
    $lines = Get-Content $manifest -Encoding UTF8 |
        ForEach-Object { ($_ -replace '#.*', '').Trim() } | Where-Object { $_ }
    return @($lines).Count
}

# ===============================================================
# 主流程
# ===============================================================
Set-Location $script:RepoRoot
Write-Host 'MagTile Studio — Windows Qt 安装包冒烟 (scripts/package_qt_desktop.md 配套)' -ForegroundColor Cyan
Write-Info "仓库根: $script:RepoRoot"
Write-Info "形态: $(if ($QtOnly) { 'Qt-only 包' } else { '并存包 (magtile_app + magtile_studio_qt)' }); 数据集: $ModelSet"

# ---- 环境检测 ----
Write-Step '环境检测 (手册第二节前置条件)'
$cmake = Find-InPath 'cmake'
$cpack = Find-InPath 'cpack'
$nsis = Find-Nsis
$vs = Find-VisualStudio
$python = Find-InPath 'python'
if (-not $python) { $python = Find-InPath 'python3' }
$qtKit = Find-QtKit $QtDir
$qtVersion = $null
$windeployqt = $null
if ($qtKit) {
    $qtVersion = Get-QtVersion $qtKit
    $wdq = Join-Path $qtKit 'bin\windeployqt.exe'
    if (Test-Path $wdq) { $windeployqt = $wdq }
}

if ($cmake) { Write-Ok "CMake: $cmake ($((& $cmake --version | Select-Object -First 1)))" } else { Write-Bad '未找到 cmake' }
if ($cpack) { Write-Ok "CPack: $cpack" } else { Write-Bad '未找到 cpack (随 CMake 安装)' }
if ($qtKit) { Write-Ok "Qt 套件: $qtKit (版本 $qtVersion)" } else { Write-Bad '未找到 Qt 套件 (-QtDir 指定, 或装到 C:\Qt\6.x\msvc*_64)' }
if ($windeployqt) { Write-Ok "windeployqt: $windeployqt" } elseif ($qtKit) { Write-Bad 'Qt 套件内未找到 windeployqt.exe' }
if ($nsis) { Write-Ok "NSIS: $nsis" } else { Write-Bad '未找到 NSIS (winget install NSIS.NSIS); 无 NSIS 时降级只打 ZIP' }
if ($vs) { Write-Ok "Visual Studio (C++ 工具集): $vs" } else { Write-Bad '未找到 VS2022 C++ 工作负载 (vswhere 未命中)' }
if ($python) { Write-Ok "Python: $python" } else { Write-Bad "未找到 Python (仅 -ModelSet starter/清单 需要)" }

$expectedModels = Get-ExpectedModelCount $ModelSet

# ---- 计划输出 (实跑与 DryRun 共用, 保证"打印的就是要跑的") ----
$configureArgs = @('-S', '.', '-B', $BuildDir, '-G', $Generator, '-A', 'x64',
                   '-DMAGTILE_BUILD_QT=ON')
if ($qtKit) { $configureArgs += "-DCMAKE_PREFIX_PATH=$($qtKit -replace '\\', '/')" }
if ($QtOnly) { $configureArgs += '-DMAGTILE_PACKAGE_QT_ONLY=ON' }
if ($ModelSet -ne 'full') { $configureArgs += "-DMAGTILE_PACKAGE_MODEL_SET=$ModelSet" }
$cpackGenerators = if ($nsis) { 'NSIS;ZIP' } else { 'ZIP' }

Write-Step '执行计划'
Write-Info "1) cmake $($configureArgs -join ' ')"
Write-Info "2) cmake --build $BuildDir --config Release --parallel"
if (-not $SkipTests) {
    Write-Info "3) ctest --test-dir $BuildDir -C Release --output-on-failure -E `"(library|inventory)_gui_smoke`""
} else { Write-Info '3) (跳过测试 -SkipTests)' }
Write-Info "4) cpack -G `"$cpackGenerators`" -C Release   (在 $BuildDir 内)"
Write-Info '5) 解压 ZIP -> smoke-staging'
if ($qtVersion -and $qtVersion -ge [version]'6.5') {
    Write-Info "6) Qt $qtVersion >= 6.5: 官方部署 API 已随 cpack 收运行库, 仅核对清单"
} else {
    Write-Info "6) Qt 6.4 路径: windeployqt --qmldir apps\desktop_qt\qml <staging>\magtile_studio_qt.exe"
}
Write-Info '7) 包内清单断言 (Qt DLL/qwindows/qml 树/data/licenses/CRT)'
Write-Info '8) 无头启动冒烟: QT_QPA_PLATFORM=offscreen magtile_studio_qt --smoke-quit-ms 1500'
Write-Info '9) (Qt 6.4) 部署后目录重压为 *-deployed.zip; NSIS 重打仍为手动步骤 (手册第五节)'

# ---- DryRun: 断言逻辑自检 (模拟包目录 + 失败注入), 不动真环境 ----
if ($DryRun) {
    Write-Step 'DryRun 自检: 用模拟包目录验证清单断言逻辑'
    $mock = Join-Path ([System.IO.Path]::GetTempPath()) "magtile_qt_smoke_mock_$PID"
    if (Test-Path $mock) { Remove-Item $mock -Recurse -Force }
    foreach ($d in @('licenses', 'data/models', 'data/thumbnails', 'platforms', 'qml/QtQuick')) {
        New-Item -ItemType Directory -Path (Join-Path $mock $d) -Force | Out-Null
    }
    foreach ($f in @('magtile_studio_qt.exe', 'magtile_app.exe', 'README.md',
                     'licenses/License.rtf', 'licenses/THIRD_PARTY_NOTICES.md',
                     'data/tile_catalog.json', 'data/models/mock_model_01.json',
                     'data/thumbnails/mock_model_01.png',
                     'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Qml.dll', 'Qt6Quick.dll',
                     'Qt6QuickControls2.dll', 'Qt6OpenGL.dll',
                     'platforms/qwindows.dll', 'qml/QtQuick/qmldir',
                     'vcruntime140.dll')) {
        Set-Content -Path (Join-Path $mock $f) -Value 'mock' -Encoding ASCII
    }
    Set-Content -Path (Join-Path $mock 'data/model_catalog.json') -Encoding ASCII -Value `
        '{"schema_version": 1, "models": [{"id": "mock_model_01", "file": "models/mock_model_01.json"}]}'

    $pass = Test-PackageManifest -Root $mock -IsQtOnly:$false -ExpectedModelCount 1 -RequireQtRuntime:$true
    $selfOk = Report-Manifest $pass '模拟完整包'

    # 失败注入 1: 抽掉平台插件 (常见事故: windeployqt 没跑/没拷全)
    Remove-Item (Join-Path $mock 'platforms/qwindows.dll')
    $inject = Test-PackageManifest -Root $mock -IsQtOnly:$false -ExpectedModelCount 1 -RequireQtRuntime:$true
    if (@($inject).Count -ge 1 -and (@($inject) -join ';') -match 'qwindows') {
        Write-Ok '失败注入 1 (删 qwindows.dll) 被正确检出'
    } else { Write-Bad '失败注入 1 未被检出 — 断言逻辑有漏'; $selfOk = $false }

    # 失败注入 2: 目录登记但模型文件缺失 (加载器会当场报错的形态)
    Set-Content -Path (Join-Path $mock 'platforms/qwindows.dll') -Value 'mock' -Encoding ASCII
    Remove-Item (Join-Path $mock 'data/models/mock_model_01.json')
    $inject2 = Test-PackageManifest -Root $mock -IsQtOnly:$false -ExpectedModelCount 1 -RequireQtRuntime:$true
    if (@($inject2).Count -ge 1 -and (@($inject2) -join ';') -match 'mock_model_01') {
        Write-Ok '失败注入 2 (目录登记但模型缺失) 被正确检出'
    } else { Write-Bad '失败注入 2 未被检出 — 断言逻辑有漏'; $selfOk = $false }

    Remove-Item $mock -Recurse -Force
    if (-not $selfOk) { Fail 'DryRun 自检未通过' }
    Write-Host "`nDryRun 完成: 环境报告与执行计划如上, 清单断言逻辑自检通过。" -ForegroundColor Green
    Write-Host '在 Windows 构建机上去掉 -DryRun 即可实跑。'
    exit 0
}

# ---- 实跑前置校验 ----
if (-not $script:OnWindows) { Fail '实跑模式仅支持 Windows; 其它平台请用 -DryRun (Linux 打包冒烟走 scripts/smoke_qt_linux_pack.sh)' }
if (-not $cmake -or -not $cpack) { Fail '缺少 cmake/cpack' }
if (-not $qtKit) { Fail '未找到 Qt 套件 (用 -QtDir 指定)' }
if (-not $vs) { Fail '未找到 VS2022 C++ 工具集' }
if ($ModelSet -ne 'full' -and -not $python) { Fail "-ModelSet $ModelSet 需要 Python3" }
if (-not $qtVersion) { Fail '无法确定 Qt 版本 (qmake -query QT_VERSION 失败)' }
$needWindeployqt = ($qtVersion -lt [version]'6.5')
if ($needWindeployqt -and -not $windeployqt) { Fail "Qt $qtVersion < 6.5 需要 windeployqt 但未找到" }

# ---- 构建 / 测试 / 打包 ----
Write-Step '配置 (手册第三节)'
Invoke-Checked '配置' $cmake $configureArgs

Write-Step '构建 Release'
Invoke-Checked '构建' $cmake @('--build', $BuildDir, '--config', 'Release', '--parallel')

if (-not $SkipTests) {
    Write-Step '测试 (GL 双 GUI 冒烟需显示环境, 按手册排除; Qt 侧测试 offscreen 照跑)'
    Invoke-Checked '测试' 'ctest' @('--test-dir', $BuildDir, '-C', 'Release',
        '--output-on-failure', '-E', '(library|inventory)_gui_smoke')
}

Write-Step "CPack 打包 (生成器: $cpackGenerators; 手册第四节)"
Push-Location $BuildDir
try {
    Invoke-Checked '打包' $cpack @('-G', $cpackGenerators, '-C', 'Release')
} finally { Pop-Location }

$suffix = if ($QtOnly) { '-qt' } else { '' }
$zip = Get-ChildItem $BuildDir -Filter "MagTileStudio-*-win64$suffix.zip" -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $zip) { Fail "未找到 ZIP 产物 (MagTileStudio-*-win64$suffix.zip)" }
Write-Ok "ZIP 产物: $($zip.Name)"
if ($nsis) {
    $installer = Get-ChildItem $BuildDir -Filter "MagTileStudio-*-win64$suffix.exe" -File |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($installer) { Write-Ok "NSIS 安装器: $($installer.Name)" }
    else { Fail '装有 NSIS 但未产出安装器 .exe' }
}

# ---- 解包到 staging ----
Write-Step '解包 ZIP 到 staging (手册第五节: 对解包后的安装目录部署)'
$staging = Join-Path $BuildDir 'smoke-staging'
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
Expand-Archive -Path $zip.FullName -DestinationPath $staging
$pkgRoot = Get-ChildItem $staging -Directory | Select-Object -First 1
if (-not $pkgRoot) { Fail 'ZIP 解包后未见顶层目录' }
Write-Ok "解包目录: $($pkgRoot.FullName)"

# ---- Qt 运行库部署 ----
if ($needWindeployqt) {
    Write-Step "Qt $qtVersion < 6.5: 运行 windeployqt (--qmldir 指向 QML 源码目录)"
    Invoke-Checked 'windeployqt' $windeployqt @(
        '--qmldir', (Join-Path $script:RepoRoot 'apps\desktop_qt\qml'),
        (Join-Path $pkgRoot.FullName 'magtile_studio_qt.exe'))
} else {
    Write-Step "Qt $qtVersion >= 6.5: 部署 API 已在 cpack 阶段收运行库, 直接核对"
}

# ---- 包内清单断言 ----
Write-Step '包内清单断言 (手册第五节核对项 + 数据/许可/CRT)'
$failures = Test-PackageManifest -Root $pkgRoot.FullName -IsQtOnly:$QtOnly.IsPresent `
    -ExpectedModelCount $expectedModels -RequireQtRuntime:$true
if (-not (Report-Manifest $failures '部署后安装目录')) { Fail '包内清单断言未通过' }

# ---- 无头启动冒烟 ----
Write-Step '无头启动冒烟 (offscreen, 包内 data/, 1.5s 自动退出)'
$smokeDb = Join-Path $env:TEMP 'magtile_qt_pack_smoke.db'
if (Test-Path $smokeDb) { Remove-Item $smokeDb -Force }
$env:QT_QPA_PLATFORM = 'offscreen'
try {
    $proc = Start-Process -FilePath (Join-Path $pkgRoot.FullName 'magtile_studio_qt.exe') `
        -ArgumentList @('--db', "`"$smokeDb`"", '--smoke-quit-ms', '1500') `
        -WorkingDirectory $pkgRoot.FullName -Wait -PassThru -NoNewWindow
    if ($proc.ExitCode -ne 0) { Fail "启动冒烟退出码 $($proc.ExitCode) (预期 0)" }
} finally { Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue }
Write-Ok '启动冒烟通过 (QML 加载无错, 包内 data/ 探测命中)'

# ---- Qt 6.4 路径: 部署后目录重压 ZIP ----
if ($needWindeployqt) {
    Write-Step '重压部署后目录 -> *-deployed.zip (自足便携包)'
    $deployedZip = Join-Path $BuildDir ($zip.BaseName + '-deployed.zip')
    if (Test-Path $deployedZip) { Remove-Item $deployedZip -Force }
    Compress-Archive -Path $pkgRoot.FullName -DestinationPath $deployedZip
    Write-Ok "自足便携包: $deployedZip"
    Write-Info '注意: NSIS 安装器仍是"未补运行库"的版本; 分发 NSIS 需按手册'
    Write-Info '第五节对已安装目录补 windeployqt, 或改用 Qt >= 6.5 (自动部署)。'
}

Write-Host "`n全部自动化冒烟通过。" -ForegroundColor Green
Write-Host '剩余人工验收 (干净机器, 见 scripts/package_qt_desktop.md 第十一节):'
Write-Host '  安装 -> 开始菜单启动 -> 模型库 -> 进教程转视角 -> 退出 -> 卸载无残留'
exit 0
