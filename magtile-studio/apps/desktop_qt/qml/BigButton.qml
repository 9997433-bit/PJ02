import QtQuick
import QtQuick.Controls
import MagTile.Studio

// =============================================================
// 儿童友好大按钮: 胶囊造型 (圆角 24)、高度 >= 64、字号 22、
// 按下轻微缩放 + 200ms ease-out (UI_UX_SPEC.md §1.2 / §4.1)。
// =============================================================
Button {
    id: control

    property color accent: Theme.primary
    property color accentPressed: Qt.darker(accent, 1.25)
    property string emoji: ""

    implicitHeight: Theme.bigButtonHeight
    implicitWidth: Math.max(220, row.implicitWidth + 64)

    scale: pressed ? 0.97 : 1.0
    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

    background: Rectangle {
        radius: Theme.radiusButton
        color: control.pressed ? control.accentPressed : control.accent
        Behavior on color { ColorAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
    }

    contentItem: Item {
        implicitWidth: row.implicitWidth
        implicitHeight: row.implicitHeight
        Row {
            id: row
            spacing: 12
            anchors.centerIn: parent
            Text {
                visible: control.emoji.length > 0
                text: control.emoji
                font.pixelSize: Theme.fontButton + 4
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: control.text
                color: "white"
                font.pixelSize: Theme.fontButton
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
