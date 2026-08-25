import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 教程播放器 (QT-3, UI_UX_SPEC.md §6 核心屏 ★):
// 左侧 3D 视口 (TutorialViewport = QQuickFramebufferObject +
// GlSceneRenderer): 已放置片实体 / 本步新片呼吸高亮 / 未来片 ghost /
// 拖动旋转·右键平移·滚轮缩放; 右侧步骤面板: 步骤分数 + 中文说明 +
// 💡提示 + 上一步/下一步大按钮 (>= 64); 底部总进度条 + 已放置片数。
// 路由契约与占位版一致 (modelId / modelName / currentStep /
// stepCount 由 Main.qml 经 studio.buildRequested 注入); 「返回」
// 直接退 (已自动存档, 不弹确认框, §4.4), 退出时刷新模型库徽标。
//
// QT-4 接入:
//   - 🔊 朗读按钮 (页眉, §4.2) 读当前步骤说明; 4-6 岁启蒙模式切步
//     自动朗读; 切步/离开自动停旧朗读 (无叠音);
//   - 每步星星反馈 (§4.3): 步骤前进落位成功后视口顶部弹出 1~3 颗
//     小星 (<= 1s, OutBack); 「减少动态效果」降级为静态「好棒！」;
//   - 进度条里程碑小星: 每 10% 一颗 (最多 10 颗), 按会话内到达过的
//     最高进度点亮, 「上一步/从头再来」不回收已点亮的星星;
//   - 全部步骤完成 -> 短暂停留后 studio.completeBuild: 写存档完成
//     状态 + 发 buildCompleted, Main.qml 原位替换为完成庆祝页 (§6.2)。
// =============================================================
Page {
    id: page

    property string modelId: ""
    property string modelName: ""
    property int currentStep: 0
    property int stepCount: 0

    /// Main.qml 路由判定用 (完成时 replace 本页为庆祝页)
    readonly property bool isTutorialPage: true

    /// 已朗读/已停读的步骤号 (防同一步的多次状态信号重复触发)
    property int spokenStep: -1
    /// 完成链路已启动 (防 finished 状态多次信号重复触发庆祝)
    property bool completionPending: false

    // ---- 每步星星反馈 + 进度里程碑 (QT-4, §4.3 只有正向与中性) --------
    /// 分龄 (§2, 读共库 age_mode 键): 4-6 星星更大更明显, 10+ 更克制
    readonly property bool bandJunior: appSettings.ageModeId === "age_4_6"
    readonly property bool bandSenior: appSettings.ageModeId === "age_10_12"
    /// 上一次看到的步骤号 (-1 = 会话尚未就绪; 就绪时只播种不奖励,
    /// 断点续搭不会因恢复步骤触发弹星)
    property int trackedStep: -1
    /// 上一次看到的已放置片数 (算本步落位片数 -> 星星颗数 1~3)
    property int trackedTiles: 0
    /// 本次会话内到达过的最高进度 (只前进不回退, §4.3: 「上一步/
    /// 从头再来」是探索不是惩罚, 已点亮的里程碑小星永不收回)
    property real bestProgress: 0

    signal back()
    signal home()
    signal notify(string message)

    /// 离开教程前统一收尾: 停止朗读 + 落盘进度 + 刷新模型库进度徽标
    function leave() {
        tts.stop()
        viewport.finishSession()
        studio.reload()
    }

    /// 当前步骤的朗读文本 (§4.2): 步骤说明 + 💡技巧提示
    function stepSpeechText() {
        var text = viewport.stepDescription
        if (viewport.stepTip !== "")
            text += "。小提示，" + viewport.stepTip
        return text
    }

    /// 🔊 按钮入口: 引擎缺失/开关关闭时温和提示, 不弹"失败" (P3)
    function speakCurrentStep() {
        if (!tts.available) {
            page.notify("这台设备还没有语音引擎, 先看文字说明吧")
        } else if (!tts.enabled) {
            page.notify("朗读开关是关着的, 可以在家长设置里打开")
        } else if (tts.speaking) {
            tts.stop()
        } else {
            tts.speak(page.stepSpeechText())
        }
    }

    Component.onDestruction: tts.stop()   // 离开教程即停, 无叠音 (§4.2)

    // 步骤状态桥 (QT-4): 每步星星反馈 + 切步朗读管理 + 完成触发庆祝
    Connections {
        target: viewport
        function onStateChanged() {
            if (viewport.sessionReady) {
                // 只在步骤恰好前进一格 (下一步/开始搭建, 本片落位成功)
                // 时弹星; 上一步/从头再来是回退, 不触发也不收回
                var step = viewport.stepNumber
                if (page.trackedStep >= 0 && step === page.trackedStep + 1) {
                    stepCheer.show(viewport.tilesPlaced - page.trackedTiles)
                }
                if (step !== page.trackedStep) {
                    page.trackedStep = step
                    page.trackedTiles = viewport.tilesPlaced
                }
                // 里程碑基准只前进不回退 (断点续搭时按恢复进度直接点亮)
                page.bestProgress = Math.max(page.bestProgress, viewport.progress)
            }
            if (viewport.sessionReady && viewport.stepNumber !== page.spokenStep) {
                page.spokenStep = viewport.stepNumber
                if (tts.autoRead && viewport.stepDescription !== "") {
                    tts.speak(page.stepSpeechText())   // 启蒙模式自动朗读 (§4.2)
                } else {
                    tts.stop()                          // 切步停旧朗读, 无叠音
                }
            }
            if (viewport.finished && !page.completionPending) {
                page.completionPending = true
                celebrateTimer.restart()
            }
        }
    }

    // 最后一片落位后短暂停留再进庆祝页 (让孩子看见成品的完成瞬间);
    // 期间按「⏮ 从头再来」/「◀ 上一步」可自然取消
    Timer {
        id: celebrateTimer
        interval: 900
        onTriggered: {
            if (!viewport.finished) {
                page.completionPending = false
                return
            }
            tts.stop()
            viewport.finishSession()             // 先落盘步骤进度 (幂等)
            studio.completeBuild(page.modelId)   // 写完成状态 -> buildCompleted -> 庆祝页
        }
    }

    background: Rectangle { color: Theme.surfaceAlt }

    // 键盘也能切步 (与 GL 版一致: 左右方向键)
    focus: true
    Keys.onRightPressed: viewport.nextStep()
    Keys.onLeftPressed: viewport.previousStep()

    // ---- 页眉: 返回 + 标题 + 回首页 (导航铁律: <= 2 步回首页 §3) ---------
    header: Item {
        height: Theme.headerHeight

        AbstractButton {
            id: backButton
            width: 140
            height: Theme.touchTarget
            anchors.left: parent.left
            anchors.leftMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: { page.leave(); page.back() }
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
            text: (viewport.sessionReady ? viewport.modelName : page.modelName)
                  + (viewport.stepCount > 0
                     ? " · 第 " + viewport.stepNumber + "/" + viewport.stepCount + " 步"
                     : "")
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        // 🔊 步骤朗读 (§4.2, >= 48 触控目标); 朗读中变主色底提示
        AbstractButton {
            id: speakButton
            width: speakLabel.implicitWidth + 2 * Theme.spacing
            height: Theme.touchTarget
            anchors.right: homeButton.left
            anchors.rightMargin: Theme.spacing
            anchors.verticalCenter: parent.verticalCenter
            visible: viewport.sessionReady
            onClicked: page.speakCurrentStep()
            scale: pressed ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: tts.speaking ? Theme.primarySoft
                                    : (speakButton.pressed ? Theme.primarySoft : Theme.surface)
                border.color: tts.speaking ? Theme.primary : Theme.cardBorder
                border.width: 1
            }
            contentItem: Text {
                id: speakLabel
                text: tts.speaking ? "🔊 朗读中…" : "🔊 朗读"
                color: tts.speaking ? Theme.primary : Theme.textPrimary
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        AbstractButton {
            id: homeButton
            width: homeLabel.implicitWidth + 2 * Theme.spacing
            height: Theme.touchTarget
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: { page.leave(); page.home() }
            scale: pressed ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: homeButton.pressed ? Theme.primarySoft : Theme.surface
                border.color: Theme.cardBorder
                border.width: 1
            }
            contentItem: Text {
                id: homeLabel
                text: "🏠 回首页"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingLarge
        anchors.topMargin: 0
        spacing: Theme.spacing

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Theme.spacingLarge

            // ---- 3D 视口 (>= 70% 宽, §6.1) --------------------------------
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.radiusCard
                color: Theme.viewportBg   // 与场景清屏色同族, 圆角边不突兀
                border.color: Theme.cardBorder
                border.width: 1

                TutorialViewport {
                    id: viewport
                    anchors.fill: parent
                    anchors.margins: 2
                    modelFile: studio.modelFilePath(page.modelId)
                    dataDir: studio.dataDirText
                    dbFile: studio.dbFileText
                    resumeStep: page.currentStep
                    // §4.7 减少动效: 本步新片呼吸高亮降级为恒亮描边
                    // (设置页切换即时生效, 定格在最亮相位不闪不动)
                    reduceMotion: Theme.reduceMotion
                }

                // 操作提示 (左下角浮层, 常驻但视觉很轻)
                Rectangle {
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    anchors.margins: Theme.spacing
                    radius: Theme.radiusButton
                    color: Theme.overlayLight
                    width: hintLabel.implicitWidth + 2 * Theme.spacing
                    height: 40
                    visible: viewport.sessionReady
                    Text {
                        id: hintLabel
                        anchors.centerIn: parent
                        text: "🖱 拖动转圈看 · 滚轮放大 · 右键平移"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                    }
                }

                // 复位视角 (右下角, >= 48 触控目标)
                AbstractButton {
                    id: resetViewButton
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: Theme.spacing
                    width: resetViewLabel.implicitWidth + 2 * Theme.spacing
                    height: Theme.touchTarget
                    visible: viewport.sessionReady
                    onClicked: viewport.resetView()
                    scale: pressed ? 0.96 : 1.0
                    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: resetViewButton.pressed ? Theme.primarySoft : Theme.surface
                        border.color: Theme.cardBorder
                        border.width: 1
                    }
                    contentItem: Text {
                        id: resetViewLabel
                        text: "🔄 回到最佳视角"
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // 教程未就绪的温和浮层 (P3 零挫败: 不说 "失败")
                ColumnLayout {
                    anchors.centerIn: parent
                    width: Math.min(parent.width - 2 * Theme.spacingLarge, 480)
                    spacing: Theme.spacing
                    visible: !viewport.sessionReady
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "🧲"
                        font.pixelSize: 72
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.fillWidth: true
                        text: viewport.statusText !== ""
                              ? viewport.statusText
                              : "教程正在准备中, 稍等一下下…"
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        lineHeight: 1.4
                    }
                    BigButton {
                        Layout.alignment: Qt.AlignHCenter
                        emoji: "🧲"
                        text: "先去挑别的模型"
                        accent: Theme.primary
                        onClicked: { page.leave(); page.back() }
                    }
                }

                // ---- 每步星星反馈 (QT-4, §4.3): 落位成功后视口顶部短暂
                // 弹出 1~3 颗小星 (颗数 = 本步落位片数, <= 1s, OutBack)。
                // 单实例覆盖层: 快速连点「下一步」时 restart 合并动画,
                // 永不堆积; enabled=false 不截获鼠标, 动画不阻塞交互。
                // 「减少动态效果」时降级为静态显示「好棒！」(§4.7)。
                Item {
                    id: stepCheer
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: Theme.spacingLarge
                    enabled: false
                    opacity: 0

                    /// 本次反馈的星星数 (1~3, 按本步落位片数收敛)
                    property int starCount: 1
                    /// 分龄大小 (§2): 4-6 更大更明显, 10+ 更克制
                    readonly property int starSize: page.bandJunior ? 68 : (page.bandSenior ? 30 : 46)

                    function show(tilesAdded) {
                        starCount = Math.max(1, Math.min(3, tilesAdded))
                        popAnim.stop()
                        staticHideTimer.stop()
                        if (Theme.reduceMotion) {
                            scale = 1.0
                            opacity = 1.0
                            staticHideTimer.restart()   // 静态直显直隐, 零位移零缩放 (§4.7)
                        } else {
                            popAnim.restart()
                        }
                    }

                    // 动效版: 1~3 颗小星 (锚定零尺寸 Item 的水平中心自然居中)
                    Row {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        spacing: 8
                        visible: !Theme.reduceMotion
                        Repeater {
                            model: stepCheer.starCount
                            delegate: Text {
                                text: "⭐"
                                font.pixelSize: stepCheer.starSize
                            }
                        }
                    }

                    // 静态降级版: 温和文字 (§4.3 正向; §4.7 减少动效)
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        visible: Theme.reduceMotion
                        radius: Theme.radiusButton
                        color: Theme.successSoft
                        border.color: Theme.success
                        border.width: 1
                        width: cheerLabel.implicitWidth + 2 * Theme.spacing
                        height: cheerLabel.implicitHeight + Theme.spacing
                        Text {
                            id: cheerLabel
                            anchors.centerIn: parent
                            text: "⭐ 好棒！"
                            font.pixelSize: page.bandJunior ? Theme.fontTitle : Theme.fontBody
                            font.bold: true
                            color: Theme.success
                        }
                    }

                    // 弹出 -> 定格 -> 淡出, 全程 ~0.9s (<= 1s)
                    SequentialAnimation {
                        id: popAnim
                        PropertyAction { target: stepCheer; property: "opacity"; value: 1.0 }
                        NumberAnimation {
                            target: stepCheer; property: "scale"
                            from: 0.3; to: 1.1; duration: 260
                            easing.type: Easing.OutBack
                        }
                        NumberAnimation {
                            target: stepCheer; property: "scale"
                            from: 1.1; to: 1.0; duration: 100
                            easing.type: Easing.OutQuad
                        }
                        PauseAnimation { duration: 320 }
                        NumberAnimation {
                            target: stepCheer; property: "opacity"
                            from: 1.0; to: 0.0; duration: 200
                        }
                    }

                    // 减少动效时的定时隐藏 (直接消失, 不做淡出动画)
                    Timer {
                        id: staticHideTimer
                        interval: 900
                        onTriggered: stepCheer.opacity = 0
                    }
                }
            }

            // ---- 步骤面板 (右侧, §6.1) ------------------------------------
            ColumnLayout {
                Layout.fillWidth: false
                Layout.preferredWidth: 360
                Layout.fillHeight: true
                spacing: Theme.spacing
                visible: viewport.sessionReady

                // 步骤分数 (大号, 图形+数字双编码)
                RowLayout {
                    spacing: Theme.spacing
                    Rectangle {
                        radius: Theme.radiusButton
                        height: 44
                        width: stepBadge.implicitWidth + 2 * Theme.spacing
                        color: Theme.primarySoft
                        Text {
                            id: stepBadge
                            anchors.centerIn: parent
                            text: viewport.stepNumber > 0
                                  ? "第 " + viewport.stepNumber + " / " + viewport.stepCount + " 步"
                                  : "准备开始"
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: Theme.primary
                        }
                    }
                    Text {
                        text: viewport.finished ? "✓ 全部搭完" : ""
                        font.pixelSize: Theme.fontBody
                        font.bold: true
                        color: Theme.success
                    }
                }

                // 步骤说明 (可滚动, 长文案不挤压按钮)
                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentHeight: stepColumn.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: stepColumn
                        width: parent.width
                        spacing: Theme.spacing

                        Text {
                            Layout.fillWidth: true
                            text: viewport.stepDescription
                            font.pixelSize: Theme.fontButton
                            color: Theme.textPrimary
                            wrapMode: Text.WordWrap
                            lineHeight: 1.4
                        }

                        // 💡 提示行: 只放搭建技巧 (§6.3), 琥珀色不表达 "错误"
                        Rectangle {
                            Layout.fillWidth: true
                            visible: viewport.stepTip !== ""
                            radius: Theme.radiusCard
                            implicitHeight: tipLabel.implicitHeight + 2 * Theme.spacing
                            color: Theme.warningSoft
                            Text {
                                id: tipLabel
                                anchors.fill: parent
                                anchors.margins: Theme.spacing
                                text: "💡 " + viewport.stepTip
                                font.pixelSize: Theme.fontBody
                                color: Theme.textPrimary
                                wrapMode: Text.WordWrap
                                lineHeight: 1.4
                            }
                        }

                        // 🎉 完成庆祝 (完整庆祝页属 QT-4, 先给足肯定)
                        Rectangle {
                            Layout.fillWidth: true
                            visible: viewport.finished
                            radius: Theme.radiusCard
                            implicitHeight: doneColumn.implicitHeight + 2 * Theme.spacing
                            color: Theme.successSoft
                            ColumnLayout {
                                id: doneColumn
                                anchors.fill: parent
                                anchors.margins: Theme.spacing
                                spacing: 8
                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "🎉"
                                    font.pixelSize: 44
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "搭好啦, 你真棒! 摆在桌上给家人看看吧。"
                                    font.pixelSize: Theme.fontBody
                                    font.bold: true
                                    color: Theme.success
                                    wrapMode: Text.WordWrap
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                        }
                    }
                }

                // ---- 导航按钮 (>= 64 高, §6.2) -----------------------------
                BigButton {
                    Layout.fillWidth: true
                    visible: !viewport.finished
                    emoji: "▶"
                    text: viewport.stepNumber > 0 ? "下一步" : "开始搭建"
                    accent: Theme.primary
                    onClicked: viewport.nextStep()
                }
                BigButton {
                    Layout.fillWidth: true
                    visible: viewport.finished
                    emoji: "🧲"
                    text: "再挑一个模型"
                    accent: Theme.success
                    onClicked: { page.leave(); page.back() }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.spacing

                    AbstractButton {
                        id: prevButton
                        Layout.fillWidth: true
                        height: Theme.touchTarget + 8
                        enabled: viewport.stepNumber > 0
                        onClicked: viewport.previousStep()
                        scale: pressed ? 0.97 : 1.0
                        Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: prevButton.pressed ? Theme.primarySoft : Theme.surface
                            border.color: Theme.cardBorder
                            border.width: 1
                            opacity: prevButton.enabled ? 1.0 : 0.45
                        }
                        contentItem: Text {
                            text: "◀ 上一步"
                            color: Theme.textPrimary
                            opacity: prevButton.enabled ? 1.0 : 0.45
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    AbstractButton {
                        id: restartButton
                        Layout.fillWidth: true
                        height: Theme.touchTarget + 8
                        enabled: viewport.stepNumber > 0
                        onClicked: {
                            viewport.restart()
                            page.notify("回到开头啦, 先转一转看看成品吧")
                        }
                        scale: pressed ? 0.97 : 1.0
                        Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: restartButton.pressed ? Theme.primarySoft : Theme.surface
                            border.color: Theme.cardBorder
                            border.width: 1
                            opacity: restartButton.enabled ? 1.0 : 0.45
                        }
                        contentItem: Text {
                            text: "⏮ 从头再来"
                            color: Theme.textPrimary
                            opacity: restartButton.enabled ? 1.0 : 0.45
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }

        // ---- 底部总进度 (§6.1: 进度条 + 里程碑小星 + 已放置片数) ----------
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacing
            visible: viewport.sessionReady

            Rectangle {
                Layout.fillWidth: true
                height: 14
                radius: 7
                color: Theme.primarySoft
                Rectangle {
                    width: Math.round(parent.width * viewport.progress)
                    height: parent.height
                    radius: 7
                    color: viewport.finished ? Theme.success : Theme.primary
                    Behavior on width { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                }

                // 里程碑小星 (QT-4): 每 10% 一颗共 10 颗, 与进度条同一
                // 口径 (viewport.progress 是 currentStep 的确定函数, 与
                // currentStep/totalSteps 天然同步); 点亮基准为会话内最高
                // 进度 bestProgress —— 「上一步/从头再来」不回收星星。
                // 图形 (★/☆) + 颜色双编码 (§4.7), 减少动效时无弹跳。
                Repeater {
                    model: 10
                    delegate: Text {
                        id: mileStar
                        readonly property bool lit: page.bestProgress >= (index + 1) / 10 - 1e-6
                        x: Math.round((parent.width - width) * (index + 1) / 10)
                        anchors.verticalCenter: parent.verticalCenter
                        text: lit ? "★" : "☆"
                        color: lit ? Theme.warning : Theme.textDim
                        font.pixelSize: page.bandJunior ? 24 : (page.bandSenior ? 15 : 18)
                        font.bold: true
                        onLitChanged: if (lit && !Theme.reduceMotion) litPop.restart()
                        SequentialAnimation {
                            id: litPop
                            NumberAnimation {
                                target: mileStar; property: "scale"
                                from: 0.3; to: 1.4; duration: 220
                                easing.type: Easing.OutBack
                            }
                            NumberAnimation {
                                target: mileStar; property: "scale"
                                from: 1.4; to: 1.0; duration: 120
                                easing.type: Easing.OutQuad
                            }
                        }
                    }
                }
            }
            Text {
                text: "已放好 " + viewport.tilesPlaced + " / " + viewport.tilesTotal + " 片"
                font.pixelSize: Theme.fontBody
                font.bold: true
                color: Theme.textSecondary
            }
        }
    }
}
