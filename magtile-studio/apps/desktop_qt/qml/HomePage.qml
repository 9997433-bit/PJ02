import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 首页: 超大主操作按钮 + "继续上次"大卡片 + 右上角刻意做小的
// 家长区入口 (32px, UI_UX_SPEC.md §5.3 全应用唯一 < 48 的可点元素)。
// =============================================================
Page {
    id: page

    signal openLibrary()
    signal openModel(string modelId)
    signal openInventory()
    signal notify(string message)

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉 ------------------------------------------------------
    header: Item {
        height: 72

        Text {
            anchors.left: parent.left
            anchors.leftMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            text: "🧲 MagTile 磁力片工坊"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        // 家长区入口: 唯一允许 32px 的小按钮 (防儿童误入 + 家长门兜底)
        AbstractButton {
            id: parentGateButton
            width: Theme.parentGateSize
            height: Theme.parentGateSize
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: page.notify("家长区 (算术题家长门) 正在从 GL 版搬到 Qt 版, 即将上线")
            background: Rectangle {
                radius: width / 2
                color: parentGateButton.pressed ? Theme.primarySoft : "transparent"
                border.color: Theme.cardBorder
                border.width: 1
            }
            contentItem: Text {
                text: "🔒"
                font.pixelSize: 16
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    // ---- 主体 ------------------------------------------------------
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - 2 * Theme.spacingLarge, 720)
        spacing: Theme.spacingLarge

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "搭一个自己的世界"
            font.pixelSize: Theme.fontHero
            font.bold: true
            color: Theme.textPrimary
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "跟着一步一步的 3D 教程, 用家里的磁力片搭出城堡、火箭和大恐龙"
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        // "继续上次"大卡片 (§5.2: 首页最顶部, 一键回到断点的模型详情)
        AbstractButton {
            id: continueCard
            visible: studio.hasContinue
            Layout.fillWidth: true
            Layout.preferredHeight: 88
            onClicked: page.openModel(studio.continueModelId)
            scale: pressed ? 0.98 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

            background: Rectangle {
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.primary
                border.width: 2
            }
            contentItem: RowLayout {
                spacing: Theme.spacing
                Text {
                    Layout.leftMargin: Theme.spacingLarge
                    text: "▶"
                    font.pixelSize: 30
                    color: Theme.primary
                }
                ColumnLayout {
                    spacing: 4
                    Text {
                        text: "继续上次"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                    }
                    Text {
                        text: studio.continueTitle
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                    }
                }
                Item { Layout.fillWidth: true }
            }
        }

        // 首启 onboarding 入口 (UI_UX_SPEC.md §10.1: 引导而非报错,
        // 跳过永远可见 —— 不登记也能正常开搭): 未登记库存时给清晰的
        // 图形录入入口, 登记后此卡自动消失 (录入入口常驻模型库筛选栏)
        AbstractButton {
            id: inventoryOnboardingCard
            visible: !studio.inventoryConfigured
            Layout.fillWidth: true
            Layout.preferredHeight: 88
            onClicked: page.openInventory()
            scale: pressed ? 0.98 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

            background: Rectangle {
                radius: Theme.radiusCard
                color: Theme.warningSoft
                border.color: Theme.warning
                border.width: 2
            }
            contentItem: RowLayout {
                spacing: Theme.spacing
                Text {
                    Layout.leftMargin: Theme.spacingLarge
                    text: "🧲"
                    font.pixelSize: 30
                }
                ColumnLayout {
                    spacing: 4
                    Text {
                        text: "先登记家里的磁力片 (2 分钟)"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                    }
                    Text {
                        text: "登记后模型库能筛出「我能搭的」, 开搭前不会再因缺片而中断"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                    }
                }
                Item { Layout.fillWidth: true }
                Text {
                    Layout.rightMargin: Theme.spacingLarge
                    text: "去登记 ▶"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.primary
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: Theme.spacingLarge

            BigButton {
                emoji: "🏰"
                text: "开始搭建"
                accent: Theme.primary
                onClicked: page.openLibrary()
            }

            BigButton {
                emoji: "🏅"
                text: "我的进度"
                accent: Theme.success
                onClicked: page.notify("进度与成就页正在搭建中, 马上就好!")
            }
        }
    }

    // ---- 页脚状态行 --------------------------------------------------
    footer: Item {
        height: 48
        Text {
            anchors.centerIn: parent
            text: studio.statusMessage + "  ·  数据目录: " + studio.dataDirText
            font.pixelSize: Theme.fontSmall
            color: Theme.textSecondary
            elide: Text.ElideMiddle
            width: parent.width - 2 * Theme.spacingLarge
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
