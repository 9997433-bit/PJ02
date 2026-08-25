import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 模型库 (占位版): 卡片网格展示目录元数据 + 进度徽标。
// 数据来自 studio.libraryModel (magtile_core 的 model_catalog +
// 进度存档)。卡片规范见 UI_UX_SPEC.md §5.2; 点击进教程属
// QT-3 阶段 (docs/QT_UI_PLAN.md), 当前给温和占位提示。
// =============================================================
Page {
    id: page

    signal back()
    signal notify(string message)

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 (>= 48) + 标题 + 统计徽标 ---------------------
    header: Item {
        height: 72

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
                text: "← 回首页"
                color: "white"
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Text {
            anchors.centerIn: parent
            text: "模型库"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            radius: Theme.radiusButton
            color: Theme.primarySoft
            width: countLabel.implicitWidth + 2 * Theme.spacing
            height: 40
            Text {
                id: countLabel
                anchors.centerIn: parent
                text: studio.modelCount + " 个模型 · " + studio.completedCount + " 个已搭好"
                font.pixelSize: Theme.fontSmall
                color: Theme.primary
                font.bold: true
            }
        }
    }

    // ---- 卡片网格 ----------------------------------------------------
    GridView {
        id: grid
        anchors.fill: parent
        anchors.margins: Theme.spacing
        clip: true
        model: studio.libraryModel

        // 每行 3~4 张 (7-9 岁标准模式, §2), 随窗口宽度自适应
        property int columns: Math.max(2, Math.floor(width / 320))
        cellWidth: Math.floor(width / columns)
        cellHeight: 220

        delegate: Item {
            width: grid.cellWidth
            height: grid.cellHeight

            AbstractButton {
                id: card
                anchors.fill: parent
                anchors.margins: Theme.spacing / 2
                onClicked: page.notify("『" + model.name + "』的 3D 教程即将接入 Qt 版; 现在可用 magtile_app library --gui 搭建")
                scale: pressed ? 0.97 : 1.0
                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                background: Rectangle {
                    radius: Theme.radiusCard
                    color: Theme.surface
                    border.color: card.pressed ? Theme.primary : Theme.cardBorder
                    border.width: card.pressed ? 2 : 1
                }

                contentItem: ColumnLayout {
                    spacing: 8

                    // 主题条带 (颜色 + 文字双编码, 色盲安全 §4.7)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        radius: Theme.radiusCard
                        color: Theme.themeColor(model.theme)
                        // 底边补一块直角矩形, 让条带只有上角是圆角
                        Rectangle {
                            anchors.bottom: parent.bottom
                            anchors.left: parent.left
                            anchors.right: parent.right
                            height: parent.radius
                            color: parent.color
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: Theme.spacing
                            text: model.theme
                            color: "white"
                            font.pixelSize: Theme.fontSmall
                            font.bold: true
                        }
                        Text {
                            visible: model.favorited
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: Theme.spacing
                            text: "⭐"
                            font.pixelSize: Theme.fontSmall
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        Layout.leftMargin: Theme.spacing
                        Layout.rightMargin: Theme.spacing
                        text: model.name
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                        elide: Text.ElideRight
                    }

                    Text {
                        Layout.leftMargin: Theme.spacing
                        text: Theme.difficultyStars(model.difficulty)
                        font.pixelSize: Theme.fontBody
                        color: Theme.warning
                    }

                    Text {
                        Layout.leftMargin: Theme.spacing
                        text: model.pieces + " 片 · " + model.steps + " 步"
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                    }

                    Item { Layout.fillHeight: true }

                    // 状态徽标: 图形 + 文字 + 颜色三重编码 (§4.7)
                    Rectangle {
                        visible: model.status !== 0
                        Layout.leftMargin: Theme.spacing
                        Layout.bottomMargin: Theme.spacing
                        radius: Theme.radiusButton
                        height: 32
                        width: statusLabel.implicitWidth + 2 * Theme.spacing
                        color: model.status === 2 ? Theme.successSoft : Theme.primarySoft
                        Text {
                            id: statusLabel
                            anchors.centerIn: parent
                            text: model.status === 2 ? "✓ 已搭好" : "▶ 第 " + model.currentStep + " 步"
                            font.pixelSize: Theme.fontSmall
                            font.bold: true
                            color: model.status === 2 ? Theme.success : Theme.primary
                        }
                    }
                }
            }
        }
    }

    // ---- 空态 (§5.2: 不出现空白页) -------------------------------------
    ColumnLayout {
        visible: studio.modelCount === 0
        anchors.centerIn: parent
        spacing: Theme.spacing
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "🧲"
            font.pixelSize: 64
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "模型们正在路上"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "用 --data-dir 指向仓库的 data 目录就能看到全部模型"
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
        }
    }
}
