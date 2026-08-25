import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 完成庆祝页 (QT-4, UI_UX_SPEC.md §6.2 / §4.3): 教程完成时由
// Main.qml 经 studio.buildCompleted 信号路由 (replace 教程页,
// 返回不会退回已完成的教程)。彩带 + 大星星 + 温和文案 + 成就卡
// (片数/步数) + 「再搭一次」「回模型库」两个大按钮。
// 反馈只有正向与中性 (§4.3): 页面上没有分数、没有评价、没有催促。
// 「减少动态效果」开启时彩带与弹跳全部降级为静态淡入 (§4.7)。
// =============================================================
Page {
    id: page

    property string modelId: ""
    property string modelName: ""
    property int pieces: 0
    property int steps: 0

    /// Main.qml 路由判定用 (再搭一次时 replace 本页, 导航深度不增长)
    readonly property bool isCelebrationPage: true

    signal buildAgain()
    signal backToLibrary()

    background: Rectangle {
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.primarySoft }
            GradientStop { position: 1.0; color: Theme.surfaceAlt }
        }
    }

    Component.onCompleted: {
        // 4-6 岁启蒙模式自动朗读一句温和的祝贺 (§4.2 / §4.3)
        if (tts.autoRead)
            tts.speak("搭好啦！你把" + page.modelName + "搭出来啦，真棒！")
    }
    Component.onDestruction: tts.stop()

    // ---- 彩带 (轻量粒子: 一次性飘落, 减少动效时整层隐藏 §4.7) --------
    Item {
        anchors.fill: parent
        visible: !Theme.reduceMotion
        Repeater {
            model: 28
            delegate: Rectangle {
                // 每条彩带的随机参数在创建时定格 (位置/颜色/节奏各不相同)
                property real rx: Math.random()
                property real rd: Math.random()
                width: 10 + Math.round(rd * 8)
                height: 18 + Math.round(rx * 10)
                radius: 4
                color: Theme.tileColors[index % Theme.tileColors.length]
                x: rx * page.width
                y: -40
                rotation: rd * 360
                NumberAnimation on y {
                    from: -40
                    to: page.height + 40
                    duration: 1800 + rd * 900   // 全程 <= 2.5s 内落定 (§4.3)
                    easing.type: Easing.InQuad
                }
                NumberAnimation on rotation {
                    from: rd * 360
                    to: rd * 360 + (rx > 0.5 ? 540 : -540)
                    duration: 2400
                }
                // 飘落尾声淡出, 不留残影
                SequentialAnimation on opacity {
                    PauseAnimation { duration: 1600 + rd * 700 }
                    NumberAnimation { from: 1.0; to: 0.0; duration: 500 }
                }
            }
        }
    }

    // ---- 主内容 ------------------------------------------------------
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - 2 * Theme.spacingLarge, 680)
        spacing: Theme.spacing

        // 三颗大星星: 依次弹跳登场 (减少动效时静态淡入 §4.7)
        Row {
            Layout.alignment: Qt.AlignHCenter
            spacing: Theme.spacing
            Repeater {
                model: 3
                delegate: Text {
                    id: star
                    text: "⭐"
                    font.pixelSize: index === 1 ? 96 : 72
                    // 减少动效时静态直接显示 (§4.7), 否则依次弹跳登场
                    scale: Theme.reduceMotion ? 1.0 : 0.0
                    SequentialAnimation {
                        running: !Theme.reduceMotion
                        PauseAnimation { duration: 150 + index * 200 }
                        NumberAnimation {
                            target: star; property: "scale"
                            from: 0.0; to: 1.15; duration: 250
                            easing.type: Easing.OutBack
                        }
                        NumberAnimation {
                            target: star; property: "scale"
                            from: 1.15; to: 1.0; duration: 120
                            easing.type: Easing.OutQuad
                        }
                    }
                }
            }
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "搭好啦！"
            font.pixelSize: Theme.fontHero
            font.bold: true
            color: Theme.textPrimary
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            text: "你把『" + page.modelName + "』搭出来啦，真棒！"
            font.pixelSize: Theme.fontTitle
            color: Theme.textPrimary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 1.4
        }

        // 成就卡: 完成绿徽章 + 片数/步数 (图形+文字+颜色三重编码 §4.7)
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Theme.spacing
            implicitWidth: badgeRow.implicitWidth + 2 * Theme.spacingLarge
            implicitHeight: badgeRow.implicitHeight + 2 * Theme.spacing
            radius: Theme.radiusCard
            color: Theme.successSoft
            border.color: Theme.success
            border.width: 1
            Row {
                id: badgeRow
                anchors.centerIn: parent
                spacing: Theme.spacingLarge
                Text {
                    text: "✓ 完成"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.success
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "🧲 " + page.pieces + " 片磁力片"
                    font.pixelSize: Theme.fontBody
                    color: Theme.textPrimary
                    anchors.verticalCenter: parent.verticalCenter
                    visible: page.pieces > 0
                }
                Text {
                    text: "🪜 一共 " + page.steps + " 步"
                    font.pixelSize: Theme.fontBody
                    color: Theme.textPrimary
                    anchors.verticalCenter: parent.verticalCenter
                    visible: page.steps > 0
                }
            }
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Theme.spacing
            text: "想再来一次，还是去挑个新模型？"
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
        }

        // 两个大按钮 (>= 64 高 §4.1): 再搭一次 / 回模型库
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Theme.spacing
            spacing: Theme.spacingLarge

            BigButton {
                emoji: "🔁"
                text: "再搭一次"
                accent: Theme.primary
                onClicked: page.buildAgain()
            }
            BigButton {
                emoji: "📚"
                text: "回模型库"
                accent: Theme.success
                onClicked: page.backToLibrary()
            }
        }
    }
}
