import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 设置页 (UI_UX_SPEC.md §8, 家长门后完整设置): 字号三档缩放
// (§4.7 阅读友好 100/125/150%) / 减少动效开关 / 步骤朗读开关
// (§4.2, QT-4) / 年龄段模式三档 (§2)。字号/动效/年龄段经
// appSettings 后端桥、朗读开关经 tts 桥写入 ProgressStore
// settings 表 —— 与 GL 版 / CLI (`settings set-age`) 共用同一
// SQLite 存档, 全部设置立即生效 (字号与动效经 Theme 单例、朗读
// 经 tts.enabledChanged 全应用即时应用)。
// =============================================================
Page {
    id: page

    signal back()
    signal openSubscription()

    /// Main.qml 会话守卫: 会话失效时该页自动退回首页
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
            text: "⚙ 设置"
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

            // 存档不可用时的温和降级提示 (P3 零挫败, 不弹 "失败")
            Rectangle {
                visible: !appSettings.storeAvailable
                Layout.fillWidth: true
                implicitHeight: degradeText.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.warningSoft
                border.color: Theme.warning
                border.width: 1
                Text {
                    id: degradeText
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    text: "存档暂时不可用, 下面的调整只在这次运行内有效"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.textPrimary
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
            }

            // ---- 字号三档 (§4.7 阅读友好, 立即生效) ---------------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: fontColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: fontColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "字号大小"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "全应用文字一起变大, 选完立刻能看到效果"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.spacing
                        Repeater {
                            model: appSettings.fontScaleOptions()
                            delegate: FilterChip {
                                required property var modelData
                                Layout.fillWidth: true
                                text: modelData.label
                                checked: appSettings.fontScalePercent === modelData.percent
                                onClicked: appSettings.fontScalePercent = modelData.percent
                            }
                        }
                    }
                }
            }

            // ---- 减少动效 (§4.7, 立即生效) ------------------------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: motionRow.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                RowLayout {
                    id: motionRow
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: Theme.spacing

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "减少动态效果"
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: Theme.primary
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "关闭界面过渡与按钮动画, 适合对动效敏感的孩子"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                            wrapMode: Text.WordWrap
                        }
                    }

                    // 大号自绘开关 (状态三重编码: 位置 + 颜色 + 开/关文字)
                    AbstractButton {
                        id: motionSwitch
                        Layout.preferredWidth: 96
                        Layout.preferredHeight: Theme.touchTarget
                        onClicked: appSettings.reduceMotion = !appSettings.reduceMotion
                        background: Rectangle {
                            radius: height / 2
                            color: appSettings.reduceMotion ? Theme.success : Theme.cardBorder
                            Behavior on color { ColorAnimation { duration: Theme.animMs } }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: 14
                                visible: appSettings.reduceMotion
                                text: "开"
                                font.pixelSize: Theme.fontSmall
                                font.bold: true
                                color: "white"
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: 14
                                visible: !appSettings.reduceMotion
                                text: "关"
                                font.pixelSize: Theme.fontSmall
                                font.bold: true
                                color: Theme.textSecondary
                            }
                            Rectangle {
                                width: parent.height - 8
                                height: parent.height - 8
                                radius: height / 2
                                y: 4
                                x: appSettings.reduceMotion ? parent.width - width - 4 : 4
                                color: "white"
                                border.color: Theme.cardBorder
                                border.width: 1
                                Behavior on x { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                            }
                        }
                        contentItem: Item {}
                    }
                }
            }

            // ---- 步骤朗读 (§4.2, QT-4): 开关直绑 tts 桥, 持久化
            // ui_settings "tts_enabled" 键, 教程页 🔊 与自动朗读即时生效 ----
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: ttsRow.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                RowLayout {
                    id: ttsRow
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: Theme.spacing

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "步骤朗读"
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: Theme.primary
                        }
                        Text {
                            Layout.fillWidth: true
                            // 引擎缺失时温和说明 (P3 零挫败): 开关照常可调,
                            // 装好语音引擎后无需再进设置
                            text: tts.available
                                  ? "教程里用 🔊 听步骤说明; 4-6 岁启蒙模式会自动朗读"
                                  : "这台设备暂时没有语音引擎, 装好后按这里的开关生效"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                            wrapMode: Text.WordWrap
                        }
                    }

                    // 大号自绘开关 (与「减少动效」同款: 位置 + 颜色 + 文字三重编码)
                    AbstractButton {
                        id: ttsSwitch
                        Layout.preferredWidth: 96
                        Layout.preferredHeight: Theme.touchTarget
                        onClicked: tts.enabled = !tts.enabled
                        background: Rectangle {
                            radius: height / 2
                            color: tts.enabled ? Theme.success : Theme.cardBorder
                            Behavior on color { ColorAnimation { duration: Theme.animMs } }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: 14
                                visible: tts.enabled
                                text: "开"
                                font.pixelSize: Theme.fontSmall
                                font.bold: true
                                color: "white"
                            }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: 14
                                visible: !tts.enabled
                                text: "关"
                                font.pixelSize: Theme.fontSmall
                                font.bold: true
                                color: Theme.textSecondary
                            }
                            Rectangle {
                                width: parent.height - 8
                                height: parent.height - 8
                                radius: height / 2
                                y: 4
                                x: tts.enabled ? parent.width - width - 4 : 4
                                color: "white"
                                border.color: Theme.cardBorder
                                border.width: 1
                                Behavior on x { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                            }
                        }
                        contentItem: Item {}
                    }
                }
            }

            // ---- 年龄段模式 (§2 三档分层, 与 GL 版 / CLI 同一设置) -------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: ageColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: ageColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "孩子的年龄段"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "按年龄调整模型库布局密度与朗读方式; 与其他版本共用同一份存档"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Repeater {
                            model: appSettings.ageModeOptions()
                            delegate: FilterChip {
                                required property var modelData
                                Layout.fillWidth: true
                                text: modelData.label
                                checked: appSettings.ageModeId === modelData.id
                                onClicked: appSettings.ageModeId = modelData.id
                            }
                        }
                    }
                }
            }

            // ---- 订阅入口 (QT-5, §11: 本页已在家长门后, 可直达订阅页) ----
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
                        text: "免费精选模型永久免费; 订阅解锁全库与每周上新 (即将上线)。"
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
                            text: "查看订阅说明 ▶"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: Theme.primary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: "设置立即生效并保存在本机存档里, 不上传任何数据"
                font.pixelSize: Theme.fontSmall
                color: Theme.textSecondary
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }
}
