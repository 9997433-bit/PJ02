# MSI 打包资产占位

本目录承载 Windows 安装器 (首选 WiX v4 / MSI) 的资产, 当前为占位。
计划放入的文件:

- `Product.wxs` — WiX 主描述文件 (组件、快捷方式、UpgradeCode)
- `License.rtf` — 安装向导许可文本
- `icon.ico` / `banner.bmp` / `dialog.bmp` — 安装器图标与界面素材
- `sign.ps1` — signtool 代码签名脚本

构建方式与整体规划见上级目录 `platforms/windows/README.md`。
