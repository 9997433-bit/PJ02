import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 完成庆祝页 (QT-4, UI_UX_SPEC.md §6.2 / §4.3): 教程完成时由
// Main.qml 经 studio.buildCompleted 信号路由 (replace 教程页,
// 返回不会退回已完成的教程)。彩带 + 大星星 + 温和文案 + 成就卡
// (片数/步数) + 「再搭一次」「回模型库」两个大按钮 + 「再搭一个?」
// 温和推荐 (最多 2 张相近难度、现在就能搭的免费模型卡片, 经
// studio.libraryFilter.recommendSimilar 排除刚完成的模型; 点卡走
// 既有 startBuild -> buildRequested 路由原位替换本页, 导航深度不
// 增长; 无推荐时整块隐藏)。4-6 岁启蒙模式推荐卡更大、每行 1 张。
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

    /// 4-6 岁启蒙模式 (§2): 推荐卡更大、每行 1 张、字号加大
    readonly property bool bandJunior: appSettings.ageModeId === "age_4_6"

    /// 「再搭一个」推荐 (§6.2): 同难度 ±1 优先、canBuild 且免费层,
    /// 排除刚完成的模型; 业务逻辑全在 C++ 桥 (recommendSimilar),
    /// completeBuild 已先 reload 再进本页, 数据定格一次即可
    readonly property var recommendations: studio.libraryFilter.recommendSimilar(page.modelId, 2)

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

    // ---- 主内容 (加推荐区后最小窗高 640 可能放不下, 包一层可滚动;
    //      内容放得下时照旧垂直居中且不可拖动, 观感不变) -----------------
    Flickable {
        id: scroller
        anchors.fill: parent
        contentWidth: width
        contentHeight: content.y + content.height + Theme.spacingLarge
        interactive: contentHeight > height
        clip: true

        ColumnLayout {
            id: content
            width: Math.min(scroller.width - 2 * Theme.spacingLarge, 680)
            x: Math.round((scroller.width - width) / 2)
            y: Math.max(Theme.spacingLarge, Math.round((scroller.height - height) / 2))
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

            // ---- 「再搭一个?」温和推荐 (§6.2): 最多 2 张相近难度、
            //      现在就能搭的模型卡; 点卡直接开搭 (startBuild ->
            //      buildRequested, Main.qml 原位替换本页, 深度不增长);
            //      没有可推荐时整块隐藏, 不显示空态文案 --------------------
            Text {
                visible: page.recommendations.length > 0
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: Theme.spacingLarge
                text: "再搭一个？这些你现在就能搭:"
                font.pixelSize: page.bandJunior ? Theme.fontTitle : Theme.fontButton
                font.bold: true
                color: Theme.textPrimary
            }

            // 4-6 岁启蒙模式每行 1 张更大的卡 (§2), 其余年龄段一行 2 张
            GridLayout {
                visible: page.recommendations.length > 0
                Layout.alignment: Qt.AlignHCenter
                columns: page.bandJunior ? 1 : 2
                columnSpacing: Theme.spacing
                rowSpacing: Theme.spacing

                Repeater {
                    model: page.recommendations

                    AbstractButton {
                        id: recCard
                        required property var modelData
                        Layout.preferredWidth: page.bandJunior ? 440 : 300
                        Layout.preferredHeight: page.bandJunior ? 212 : 158
                        onClicked: studio.startBuild(modelData.modelId)
                        scale: pressed ? 0.97 : 1.0
                        Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                        background: Rectangle {
                            radius: Theme.radiusCard
                            color: Theme.surface
                            border.color: recCard.pressed ? Theme.primary : Theme.cardBorder
                            border.width: recCard.pressed ? 2 : 1
                        }

                        contentItem: ColumnLayout {
                            spacing: 4

                            // 主题条带缩略位 (与模型库卡片同语言: 颜色 +
                            // 文字双编码, 色盲安全 §4.7)
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: page.bandJunior ? 64 : 36
                                radius: Theme.radiusCard
                                color: Theme.themeColor(recCard.modelData.theme)
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
                                    text: recCard.modelData.theme
                                    color: "white"
                                    font.pixelSize: page.bandJunior ? Theme.fontButton : Theme.fontSmall
                                    font.bold: true
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                Layout.leftMargin: Theme.spacing
                                Layout.rightMargin: Theme.spacing
                                text: recCard.modelData.name
                                font.pixelSize: page.bandJunior ? Theme.fontTitle : Theme.fontButton
                                font.bold: true
                                color: Theme.textPrimary
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.leftMargin: Theme.spacing
                                text: Theme.difficultyStars(recCard.modelData.difficulty)
                                      + "  ·  🧲 " + recCard.modelData.pieces + " 片"
                                font.pixelSize: page.bandJunior ? Theme.fontButton : Theme.fontBody
                                color: Theme.textSecondary
                            }

                            Item { Layout.fillHeight: true }

                            // 正向徽标 (§4.3): 只报喜, 不催促
                            Rectangle {
                                Layout.leftMargin: Theme.spacing
                                Layout.bottomMargin: Theme.spacing / 2
                                radius: Theme.radiusButton
                                height: page.bandJunior ? 36 : 28
                                width: recTag.implicitWidth + 2 * Theme.spacing
                                color: Theme.successSoft
                                Text {
                                    id: recTag
                                    anchors.centerIn: parent
                                    text: "✓ 现在就能搭"
                                    font.pixelSize: page.bandJunior ? Theme.fontBody : Theme.fontSmall
                                    font.bold: true
                                    color: Theme.success
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
