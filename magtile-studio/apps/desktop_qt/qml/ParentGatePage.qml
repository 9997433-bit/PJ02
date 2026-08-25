import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 家长门 (UI_UX_SPEC.md §9): 算术乘法题 + 中文大写数字软键盘,
// 复刻 GL/ImGui 版行为 —— 题目/验证/3 次答错 60 秒冷却/15 分钟
// 内存会话全部由 core::ParentGate 状态机负责 (parentGate 后端桥)。
// 软键盘不依赖物理键盘/输入法 (平板同款交互); 答错/冷却只有温和
// 提示 (P3 零挫败, 不用红色); 门界面无任何商品/价格信息。
// =============================================================
Page {
    id: page

    signal passed()
    signal dismissed()

    /// 软键盘输入缓冲 (中文大写数字, 答案最多 3 字, 留 1 字余量)
    property string answerInput: ""
    readonly property bool coolingDown: parentGate.cooldownSeconds > 0

    function pressKey(key) {
        if (key === "退格") {
            // 键盘只产生 BMP 内单码元汉字, 按字删除
            answerInput = answerInput.slice(0, -1)
        } else if (answerInput.length < 4) {
            answerInput += key
        }
    }

    function submit() {
        if (answerInput === "")
            return
        parentGate.submitAnswer(answerInput)
        answerInput = ""   // 与 GL 版一致: 每次提交后清空输入
    }

    // 过门成功统一走后端 passed 信号 (软键盘提交与冒烟自动驾驶同一路径)
    Connections {
        target: parentGate
        function onPassed() { page.passed() }
    }

    background: Rectangle { color: Theme.surfaceAlt }

    // 居中卡片 (固定宽 480, 同 GL 版门窗口)
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: 480
        height: cardColumn.implicitHeight + 2 * 26
        radius: Theme.radiusCard
        color: Theme.surface
        border.color: Theme.cardBorder
        border.width: 1

        ColumnLayout {
            id: cardColumn
            anchors.centerIn: parent
            width: card.width - 2 * 30
            spacing: 10

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "请家长来完成"
                font.pixelSize: Theme.fontTitle
                font.bold: true
                color: Theme.textPrimary
            }
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                text: "订阅与设置只对家长开放, 请作答后进入家长区"
                font.pixelSize: Theme.fontSmall
                color: Theme.textSecondary
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 6
                Layout.bottomMargin: 6
                height: 1
                color: Theme.cardBorder
            }

            // ---- 冷却态: 温和的 "休息一下", 无惩罚文案 ------------------
            ColumnLayout {
                visible: page.coolingDown
                Layout.fillWidth: true
                spacing: 10

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 10
                    text: "休息一下"
                    font.pixelSize: Theme.fontTitle
                    font.bold: true
                    color: Theme.textPrimary
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: parentGate.cooldownSeconds + " 秒后可以再试一次"
                    font.pixelSize: Theme.fontBody
                    color: Theme.textSecondary
                }
                AbstractButton {
                    id: cooldownBackButton
                    Layout.fillWidth: true
                    Layout.topMargin: 14
                    Layout.preferredHeight: Theme.touchTarget
                    onClicked: page.dismissed()
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: cooldownBackButton.pressed ? Theme.primarySoft : Theme.surface
                        border.color: Theme.cardBorder
                        border.width: 1
                    }
                    contentItem: Text {
                        text: "返回首页"
                        font.pixelSize: Theme.fontBody
                        font.bold: true
                        color: Theme.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }

            // ---- 答题态: 题面 + 中文大写数字软键盘 ----------------------
            ColumnLayout {
                visible: !page.coolingDown
                Layout.fillWidth: true
                spacing: 10

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: parentGate.question
                    font.pixelSize: Theme.fontTitle
                    font.bold: true
                    color: Theme.textPrimary
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "请用中文大写数字作答 (例: 贰拾壹)"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.textSecondary
                }

                // 答案展示框 (软键盘输入, 不弹系统输入法)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    radius: 10
                    color: Theme.surfaceAlt
                    Text {
                        anchors.centerIn: parent
                        text: page.answerInput === "" ? "点击下方数字键输入" : page.answerInput
                        font.pixelSize: Theme.fontButton
                        font.bold: page.answerInput !== ""
                        color: page.answerInput === "" ? Theme.textSecondary : Theme.textPrimary
                    }
                }

                // 答错温和提示 (琥珀, 不用红色表达 "错误")
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    visible: parentGate.wrongAnswer
                    text: "还差一点, 再试一次吧 (还可尝试 " + parentGate.attemptsRemaining + " 次)"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.warning
                }

                // 软键盘: 4 行 x 3 列, 键高 48 (触控目标下限)
                GridLayout {
                    Layout.fillWidth: true
                    columns: 3
                    rowSpacing: 8
                    columnSpacing: 8

                    Repeater {
                        model: ["壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖", "零", "拾", "退格"]
                        delegate: AbstractButton {
                            id: keyButton
                            required property string modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: Theme.touchTarget
                            onClicked: page.pressKey(modelData)
                            scale: pressed ? 0.96 : 1.0
                            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                            background: Rectangle {
                                radius: 10
                                color: keyButton.pressed ? Theme.primarySoft : Theme.surfaceAlt
                                border.color: Theme.cardBorder
                                border.width: 1
                            }
                            contentItem: Text {
                                text: keyButton.modelData
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.textPrimary
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: 10

                    AbstractButton {
                        id: submitButton
                        Layout.fillWidth: true
                        Layout.preferredHeight: Theme.touchTarget
                        enabled: page.answerInput !== ""
                        onClicked: page.submit()
                        opacity: enabled ? 1.0 : 0.45
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: submitButton.pressed ? Theme.primaryPressed : Theme.primary
                        }
                        contentItem: Text {
                            text: "确认"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: "white"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                    AbstractButton {
                        id: dismissButton
                        Layout.fillWidth: true
                        Layout.preferredHeight: Theme.touchTarget
                        onClicked: {
                            page.answerInput = ""
                            page.dismissed()
                        }
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: dismissButton.pressed ? Theme.primarySoft : Theme.surface
                            border.color: Theme.cardBorder
                            border.width: 1
                        }
                        contentItem: Text {
                            text: "返回"
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
}
