import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 家长中心 (UI_UX_SPEC.md §9.2, 门后首页): 家长门通过后的聚合页。
// 会话剩余时间常驻顶部; 订阅 (占位, 即将上线) / 设置 (字号三档 /
// 减少动效 / 年龄段) / 隐私与数据说明 + 「锁定家长区」(立即结束
// 会话)。会话到期或锁定后由 Main.qml 的守卫统一退回首页。
// 成人信息密度: 允许小字号与说明性文本。
// =============================================================
Page {
    id: page

    signal back()
    signal openSettings()
    signal openSubscription()

    /// Main.qml 会话守卫: 会话失效时该页 (及其上层) 自动退回首页
    readonly property bool requiresParentSession: true

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

            // ---- 隐私与数据 (说明性, 无外链) ----------------------------
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
                        text: "本应用不采集儿童个人信息, 进度与设置只保存在这台设备上; 数据导出与一键清除将在此提供。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
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
}
