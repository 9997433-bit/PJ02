import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 成就墙全览 (UI_UX_SPEC.md §7.1, QT-4): 徽章卡片网格。
// 已点亮 = 完成绿卡 + ✓ + 解锁日期; 未点亮 = 灰色剪影 + 一句话
// 达成条件 (§7.1: 不显示进度百分比, 防焦虑)。成就只与搭建行为
// 挂钩 (§4.5), 数据经 studio.achievementsList() 读进度存档 ——
// 与 CLI `progress list` 的成就口径同一份 SQLite。
// 页脚只报喜不催促: "已点亮 N 枚徽章" (§4.3 正向与中性反馈)。
// =============================================================
Page {
    id: page

    signal back()

    property var badges: []

    function refresh() { badges = studio.achievementsList() }

    Component.onCompleted: refresh()
    Connections {
        target: studio
        function onCatalogChanged() { page.refresh() }
    }

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
            text: "🏅 成就墙"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
    }

    // ---- 主体: 徽章卡片网格 -------------------------------------------
    Flickable {
        anchors.fill: parent
        contentHeight: bodyColumn.implicitHeight + 2 * Theme.spacingLarge
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: bodyColumn
            anchors.horizontalCenter: parent.horizontalCenter
            y: Theme.spacingLarge
            width: Math.min(page.width - 2 * Theme.spacingLarge, 760)
            spacing: Theme.spacing

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "每完成一个新模型, 就会点亮新的徽章"
                font.pixelSize: Theme.fontBody
                color: Theme.textSecondary
            }

            Flow {
                Layout.fillWidth: true
                Layout.topMargin: Theme.spacing
                spacing: Theme.spacing

                Repeater {
                    model: page.badges
                    delegate: Rectangle {
                        id: badgeCard
                        required property var modelData
                        width: 238
                        height: 180
                        radius: Theme.radiusCard
                        color: modelData.unlocked ? Theme.successSoft : Theme.surface
                        border.color: modelData.unlocked ? Theme.success : Theme.cardBorder
                        border.width: modelData.unlocked ? 2 : 1

                        ColumnLayout {
                            anchors.centerIn: parent
                            width: parent.width - 2 * Theme.spacing
                            spacing: 6

                            // 徽章图形: 未点亮时灰色剪影 (低透明度, §7.1)
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: badgeCard.modelData.emoji
                                font.pixelSize: 44
                                opacity: badgeCard.modelData.unlocked ? 1.0 : 0.3
                            }
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.fillWidth: true
                                text: badgeCard.modelData.name
                                      + (badgeCard.modelData.unlocked ? " ✓" : "")
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: badgeCard.modelData.unlocked
                                       ? Theme.textPrimary : Theme.textSecondary
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                            // 已点亮: 解锁日期; 未点亮: 一句话达成条件
                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.fillWidth: true
                                text: badgeCard.modelData.unlocked
                                      ? badgeCard.modelData.unlockedText
                                      : badgeCard.modelData.condition
                                font.pixelSize: Theme.fontSmall
                                color: badgeCard.modelData.unlocked
                                       ? Theme.success : Theme.textSecondary
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }
        }
    }

    // ---- 页脚: 只报喜不催促 (§4.3) ------------------------------------
    footer: Item {
        height: 48
        Text {
            anchors.centerIn: parent
            text: studio.achievementCount > 0
                  ? "🏅 已点亮 " + studio.achievementCount + " 枚徽章, 继续加油!"
                  : "完成第一个模型, 就能点亮第一枚徽章"
            font.pixelSize: Theme.fontSmall
            color: Theme.textSecondary
        }
    }
}
