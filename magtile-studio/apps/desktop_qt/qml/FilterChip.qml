import QtQuick
import QtQuick.Controls
import MagTile.Studio

// =============================================================
// 筛选胶囊: 选中态实心主色 + 白字, 未选中白底描边; 高度 48
// (儿童触控目标下限, UI_UX_SPEC.md §4.1)。选中状态完全由外部
// 绑定驱动 (checkable 关闭), 点击行为由使用方的 onClicked 决定,
// 避免内部切换与属性绑定互相打架。
// =============================================================
AbstractButton {
    id: control

    property color accent: Theme.primary

    implicitHeight: Theme.touchTarget
    implicitWidth: chipLabel.implicitWidth + 2 * Theme.spacing

    opacity: enabled ? 1.0 : 0.45
    scale: pressed ? 0.96 : 1.0
    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

    background: Rectangle {
        radius: Theme.radiusButton
        color: control.checked ? control.accent
             : (control.pressed ? Theme.primarySoft : Theme.surface)
        border.color: control.checked ? control.accent : Theme.cardBorder
        border.width: 1
        Behavior on color { ColorAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
    }

    contentItem: Text {
        id: chipLabel
        text: control.text
        color: control.checked ? "white" : Theme.textPrimary
        font.pixelSize: Theme.fontBody
        font.bold: control.checked
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
