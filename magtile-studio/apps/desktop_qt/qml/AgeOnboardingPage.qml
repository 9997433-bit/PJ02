import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 首次启动年龄段引导 (QT-5, UI_UX_SPEC.md §10.1 / §2): 盖在首页
// 之上的温和全屏引导。存档从未写过 age_mode 键且无
// onboarding_age_done 完成标记时出现一次 (appSettings.
// ageOnboardingPending); 三档大卡片 (4-6 / 7-9 / 10+) 的档位标识
// 与 LibraryPage 分龄口径完全同源 (同一组 age_mode 值, 家长之后
// 随时可在 ⚙ 设置 里改档)。选完经 appSettings.completeAgeOnboarding
// 落盘 (age_mode + 完成标记) 并淡出露出首页 —— 选档就是全部,
// 无跳过按钮也无催促 (选任何一档都对, 默认档也在三张卡里)。
// 「减少动态效果」开启时 Theme.animMs 归零, 入场/退场降级为静态
// 直出直收 (§4.7)。
// =============================================================
Rectangle {
    id: overlay

    visible: false
    opacity: 0
    color: Theme.surfaceAlt

    // 引导期间拦下全部指针事件: 下层首页在选完档位前不可点
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
    }

    Component.onCompleted: {
        if (appSettings.ageOnboardingPending) {
            visible = true
            enterAnim.start()   // 减少动效时时长为 0: 静态直出 (§4.7)
        }
    }

    /// 选定档位 (卡片点击与冒烟自动驾驶同走这一条路径): 落盘
    /// age_mode + onboarding_age_done 后温和淡出, 露出首页
    function choose(ageModeId) {
        if (!visible) return
        appSettings.completeAgeOnboarding(ageModeId)
        if (!appSettings.ageOnboardingPending) {
            enterAnim.stop()
            leaveAnim.start()
        }
    }

    // 三档大卡片数据: modeId 与 LibraryPage/SettingsPage 读写的
    // age_mode 完全同一组标识; 文案儿童友好, 只描述体验不提对错
    readonly property var ageCards: [
        {
            modeId: "age_4_6",
            emoji: "🐣",
            ageText: "4-6 岁",
            modeName: "启蒙模式",
            hint: "超大卡片和自动朗读, 一步一步慢慢搭"
        },
        {
            modeId: "age_7_9",
            emoji: "🦖",
            ageText: "7-9 岁",
            modeName: "标准模式",
            hint: "自己挑喜欢的模型, 跟着 3D 教程搭"
        },
        {
            modeId: "age_10_12",
            emoji: "🚀",
            ageText: "10 岁以上",
            modeName: "进阶模式",
            hint: "全部筛选工具和更有挑战的大模型"
        }
    ]

    // 入场: 整页淡入 + 内容轻微上浮 (温和不惊扰); 减少动效时静态直出
    ParallelAnimation {
        id: enterAnim
        NumberAnimation {
            target: overlay; property: "opacity"
            from: 0; to: 1
            duration: 2 * Theme.animMs; easing.type: Easing.OutQuad
        }
        NumberAnimation {
            target: contentColumn; property: "anchors.verticalCenterOffset"
            from: 24; to: 0
            duration: 2 * Theme.animMs; easing.type: Easing.OutQuad
        }
    }

    // 退场: 淡出后彻底隐藏 (选完即进入首页)
    SequentialAnimation {
        id: leaveAnim
        NumberAnimation {
            target: overlay; property: "opacity"
            from: 1; to: 0
            duration: Theme.animMs; easing.type: Easing.OutQuad
        }
        ScriptAction { script: overlay.visible = false }
    }

    ColumnLayout {
        id: contentColumn
        anchors.centerIn: parent
        width: Math.min(parent.width - 2 * Theme.spacingLarge, 960)
        spacing: Theme.spacing

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "🧲"
            font.pixelSize: 56
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "你好呀, 欢迎来到磁力片工坊!"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
            horizontalAlignment: Text.AlignHCenter
        }

        Text {
            Layout.fillWidth: true
            text: "搭磁力片的小朋友今年几岁啦? 点一张卡片, 界面会变成最合适的样子"
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }

        Item { Layout.preferredHeight: Theme.spacing }

        // 三档大卡片 (§4.1: 远超 48 触控目标; 状态 图形+文字 双编码)
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacingLarge

            Repeater {
                model: overlay.ageCards
                delegate: AbstractButton {
                    id: ageCard
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 248
                    onClicked: overlay.choose(modelData.modeId)
                    scale: pressed ? 0.97 : 1.0
                    Behavior on scale {
                        NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad }
                    }

                    background: Rectangle {
                        radius: Theme.radiusCard
                        color: ageCard.pressed ? Theme.primarySoft : Theme.surface
                        border.color: ageCard.hovered ? Theme.primary : Theme.cardBorder
                        border.width: 2
                    }
                    contentItem: ColumnLayout {
                        spacing: 6

                        Item { Layout.fillHeight: true }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: ageCard.modelData.emoji
                            font.pixelSize: 44
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: ageCard.modelData.ageText
                            font.pixelSize: Theme.fontTitle
                            font.bold: true
                            color: Theme.primary
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: ageCard.modelData.modeName
                            font.pixelSize: Theme.fontButton
                            color: Theme.textPrimary
                        }
                        Text {
                            Layout.fillWidth: true
                            Layout.leftMargin: Theme.spacing
                            Layout.rightMargin: Theme.spacing
                            text: ageCard.modelData.hint
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                            wrapMode: Text.WordWrap
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }

        Item { Layout.preferredHeight: Theme.spacing }

        Text {
            Layout.fillWidth: true
            text: "选好就开始搭啦! 之后家长随时可以在 ⚙ 设置 里修改"
            font.pixelSize: Theme.fontSmall
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
