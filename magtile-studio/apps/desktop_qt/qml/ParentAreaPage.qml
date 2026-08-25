import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 家长中心 (UI_UX_SPEC.md §9.2, 门后首页): 家长门通过后的聚合页。
// 会话剩余时间常驻顶部; 订阅 (占位, 即将上线) / 设置 (字号三档 /
// 减少动效 / 年龄段) / 隐私与数据 (SECURITY_AND_PRIVACY.md §3/§4
// C4/Z8: 我们收集什么 / 数据存在哪 / 导出进度 JSON / 清除本地数据
// 带二次确认) + 「锁定家长区」(立即结束会话)。会话到期或锁定后由
// Main.qml 的守卫统一退回首页。成人信息密度: 允许小字号与说明文本。
// =============================================================
Page {
    id: page

    signal back()
    signal openSettings()
    signal openSubscription()
    signal notify(string message)
    /// 本地数据已清除: Main.qml 据此重置设置/朗读、刷新模型库并
    /// 温和退回首次启动状态 (SECURITY_AND_PRIVACY.md §4 C4/Z8)
    signal dataCleared()

    /// Main.qml 会话守卫: 会话失效时该页 (及其上层) 自动退回首页
    readonly property bool requiresParentSession: true

    /// 最近一次导出文件的完整路径 (卡片内回显, 家长好找到文件)
    property string lastExportPath: ""

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 + 标题 ---------------------------------------
    header: Item {
        height: Theme.headerHeight

        AbstractButton {
            id: backButton
            width: 140
            height: Theme.touchTarget
            anchors.left: parent.left
            anchors.leftMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: page.back()
            scale: pressed ? 0.97 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: backButton.pressed ? Theme.primaryPressed : Theme.primary
            }
            contentItem: Text {
                text: "← 返回"
                color: "white"
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Text {
            anchors.centerIn: parent
            text: "🔒 家长中心"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
    }

    // ---- 主体: 居中卡片列 --------------------------------------------
    Flickable {
        anchors.fill: parent
        contentHeight: bodyColumn.implicitHeight + 2 * Theme.spacingLarge
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: bodyColumn
            anchors.horizontalCenter: parent.horizontalCenter
            y: Theme.spacingLarge
            width: Math.min(page.width - 2 * Theme.spacingLarge, 640)
            spacing: Theme.spacing

            // 会话剩余 (只存内存, 退出应用即失效)
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: sessionText.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.primarySoft
                Text {
                    id: sessionText
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    text: "家长会话剩余 " + Math.floor(parentGate.sessionRemainingSeconds / 60)
                          + " 分 " + (parentGate.sessionRemainingSeconds % 60 < 10 ? "0" : "")
                          + (parentGate.sessionRemainingSeconds % 60)
                          + " 秒 · 只保存在内存, 退出应用即失效"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.primary
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
            }

            // ---- 订阅 (占位, 家长门之后才可见, §11) ---------------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: subscriptionColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: subscriptionColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "订阅"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "全库订阅与恢复购买将在正式版开放; 儿童界面不显示任何价格。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                    AbstractButton {
                        id: subscriptionButton
                        Layout.fillWidth: true
                        Layout.preferredHeight: Theme.touchTarget
                        onClicked: page.openSubscription()
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: subscriptionButton.pressed ? Theme.primarySoft : Theme.surface
                            border.color: Theme.primary
                            border.width: 1
                        }
                        contentItem: Text {
                            text: "订阅管理 (即将上线) ▶"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: Theme.primary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            // ---- 设置 (字号三档 / 减少动效 / 年龄段) --------------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: settingsColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: settingsColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "设置"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "字号三档缩放 / 减少动效 / 年龄段模式 (当前: "
                              + appSettings.ageModeLabel + ")。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                    AbstractButton {
                        id: settingsButton
                        Layout.fillWidth: true
                        Layout.preferredHeight: Theme.touchTarget
                        onClicked: page.openSettings()
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: settingsButton.pressed ? Theme.primaryPressed : Theme.primary
                        }
                        contentItem: Text {
                            text: "打开设置 ▶"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: "white"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            // ---- 隐私与数据 (SECURITY_AND_PRIVACY.md §3 / §4 C4/Z8:
            // 家长可查看/导出/清除全部本地数据; 全程离线, 无外链) --------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: privacyColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: privacyColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "隐私与数据"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "我们收集什么: 只在这台设备上记录搭建进度与成就、收藏、"
                              + "磁力片库存和设置 (字号/朗读/年龄段)。默认无账号、无广告、"
                              + "无第三方分析, 不联网, 也不采集孩子的姓名、照片、位置等任何个人信息。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "数据存在哪: 本机存档文件 " + privacy.dbFileText
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WrapAnywhere
                    }
                    // 诊断信息 (成人信息密度): 原首页页脚的数据目录移到
                    // 这里 —— 儿童界面不露工程路径, 家长排查时仍找得到
                    Text {
                        Layout.fillWidth: true
                        text: "模型库目录: " + studio.dataDirText
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        opacity: 0.8
                        elide: Text.ElideMiddle
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "完整隐私政策草稿随应用文档提供: docs/PRIVACY_POLICY_DRAFT.md"
                              + " (离线可读, 上架前经法务定稿)。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }

                    // 存档不可用时导出/清除温和禁用 (P3 零挫败, 不弹「失败」)
                    Text {
                        visible: !privacy.storeAvailable
                        Layout.fillWidth: true
                        text: "存档暂时不可用, 导出与清除先歇一会儿"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.spacing

                        // 导出进度 (C4/Z8「查询/导出」): JSON 落文档目录
                        AbstractButton {
                            id: exportButton
                            Layout.fillWidth: true
                            Layout.preferredHeight: Theme.touchTarget
                            enabled: privacy.storeAvailable
                            opacity: enabled ? 1.0 : 0.5
                            onClicked: {
                                var path = privacy.exportData()
                                if (path !== "") {
                                    page.lastExportPath = path
                                    page.notify("进度已导出: " + path)
                                } else {
                                    page.notify("这次没导出成功, 稍后再试一次就好")
                                }
                            }
                            background: Rectangle {
                                radius: Theme.radiusButton
                                color: exportButton.pressed ? Theme.primarySoft : Theme.surface
                                border.color: Theme.primary
                                border.width: 1
                            }
                            contentItem: Text {
                                text: "📤 导出进度 (JSON)"
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.primary
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        // 清除本地数据 (C4/Z8「删除」): 家长门之后再加
                        // 一道二次确认 (§6.1 数据操作)
                        AbstractButton {
                            id: clearButton
                            Layout.fillWidth: true
                            Layout.preferredHeight: Theme.touchTarget
                            enabled: privacy.storeAvailable
                            opacity: enabled ? 1.0 : 0.5
                            onClicked: clearConfirm.open()
                            background: Rectangle {
                                radius: Theme.radiusButton
                                color: clearButton.pressed ? Theme.warningSoft : Theme.surface
                                border.color: Theme.warning
                                border.width: 1
                            }
                            contentItem: Text {
                                text: "🧹 清除本地数据…"
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.textPrimary
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    Text {
                        visible: page.lastExportPath !== ""
                        Layout.fillWidth: true
                        text: "最近一次导出: " + page.lastExportPath
                        font.pixelSize: Theme.fontSmall
                        color: Theme.success
                        wrapMode: Text.WrapAnywhere
                    }
                }
            }

            // ---- 锁定家长区 (立即结束会话, 守卫退回首页) -----------------
            AbstractButton {
                id: lockButton
                Layout.fillWidth: true
                Layout.preferredHeight: Theme.touchTarget
                onClicked: parentGate.lockSession()
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: lockButton.pressed ? Theme.warningSoft : Theme.surface
                    border.color: Theme.warning
                    border.width: 1
                }
                contentItem: Text {
                    text: "🔒 锁定家长区 (再次进入需重新验证)"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.textPrimary
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    // ---- 清除本地数据: 二次确认 (家长门之后的第二道确认, §6.1;
    // 说清删什么 + 不可恢复 + 引导先导出; 安全选项在前) ----------------
    Popup {
        id: clearConfirm
        modal: true
        focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(560, page.width - 2 * Theme.spacingLarge)
        padding: Theme.spacingLarge
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle {
            radius: Theme.radiusSheet
            color: Theme.surface
            border.color: Theme.warning
            border.width: 2
        }
        contentItem: ColumnLayout {
            spacing: Theme.spacing

            Text {
                text: "确定要清除本机数据吗?"
                font.pixelSize: Theme.fontTitle
                font.bold: true
                color: Theme.textPrimary
            }
            Text {
                Layout.fillWidth: true
                text: "将删除这台设备上的全部搭建进度、成就、收藏、磁力片库存"
                      + "和设置, 删除后无法恢复。需要留档的话, 可以先关闭本窗口"
                      + "用「导出进度」保存一份 JSON。"
                font.pixelSize: Theme.fontBody
                color: Theme.textSecondary
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.spacing

                // 安全默认: 「先不清除」为主按钮样式且排在前
                AbstractButton {
                    id: keepDataButton
                    Layout.fillWidth: true
                    Layout.preferredHeight: Theme.touchTarget
                    onClicked: clearConfirm.close()
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: keepDataButton.pressed ? Theme.primaryPressed : Theme.primary
                    }
                    contentItem: Text {
                        text: "先不清除"
                        font.pixelSize: Theme.fontBody
                        font.bold: true
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                AbstractButton {
                    id: confirmClearButton
                    Layout.fillWidth: true
                    Layout.preferredHeight: Theme.touchTarget
                    onClicked: {
                        clearConfirm.close()
                        if (privacy.clearAllData()) {
                            page.dataCleared()
                        } else {
                            page.notify("这次没清除成功, 稍后再试一次就好")
                        }
                    }
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: confirmClearButton.pressed ? Theme.warningSoft : Theme.surface
                        border.color: Theme.warning
                        border.width: 1
                    }
                    contentItem: Text {
                        text: "确认清除"
                        font.pixelSize: Theme.fontBody
                        font.bold: true
                        color: Theme.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
