import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 模型详情页 (UI_UX_SPEC.md §5.4, QT-1): 进教程前的确认页。
// 大预览位: 3D 可旋转成品预览 (复用 QT-3 TutorialViewport 的只读
// previewMode —— 最终态全貌, 无 ghost/步骤高亮, 不写进度存档;
// 拖动旋转 / 滚轮缩放 / 右键平移与教程一致) + 难度/片数/步数 +
// 所需片型 BOM 清单 (对照家庭库存, 缺片琥珀提示, 不用红色表达
// "错误") + 收藏 + 「开始搭建」大按钮 (高 64, 占宽 80%)。
// 数据经 studio.modelDetail / studio.bomForModel 读取;
// 「开始搭建」走 studio.startBuild -> buildRequested 信号,
// 路由在 Main.qml。
// 订阅内容 (非免费层): 元数据/BOM/3D 预览照常可浏览, 「开始搭建」
// 改为「请家长来解锁」-> openSubscription 信号 -> Main.qml 经家长门
// 导向订阅页 (§11, COMMERCIAL_PLAN §2.1 只锁内容不锁功能)。
// =============================================================
Page {
    id: page

    property string modelId: ""
    property var detail: ({ found: false })
    property var bom: []

    // 订阅内容 (非免费层): 只锁「开始搭建」入口, 元数据/BOM 照常可看
    // (COMMERCIAL_PLAN §2.1 只锁内容不锁功能)。isFree 显式为 false 才
    // 上锁 —— 数据未就绪 (undefined) 时不误锁 (宁可放行)。
    readonly property bool locked: detail.found === true && detail.isFree === false

    signal back()
    signal notify(string message)
    /// 非免费模型「开始搭建」: Main.qml 路由到家长门后的订阅页 (§11)
    signal openSubscription()

    function refresh() {
        detail = studio.modelDetail(modelId)
        bom = studio.bomForModel(modelId)
    }

    Component.onCompleted: refresh()
    Connections {
        target: studio
        function onCatalogChanged() { page.refresh() }
    }

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 返回 + 标题 + 收藏 (均 >= 48 触控目标) -------------------
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
            text: page.detail.found ? page.detail.name : "模型详情"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        // 收藏切换: 选中 = 实心星 + 琥珀底 (图形 + 文字 + 颜色三重编码 §4.7)
        AbstractButton {
            id: favoriteButton
            width: favoriteLabel.implicitWidth + 2 * Theme.spacing
            height: Theme.touchTarget
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: {
                var favorited = studio.toggleFavorite(page.modelId)
                page.refresh()
                page.notify(favorited ? "⭐ 已加入收藏" : "已从收藏移出")
            }
            scale: pressed ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: page.detail.favorited ? Theme.warningSoft : Theme.surface
                border.color: page.detail.favorited ? Theme.warning : Theme.cardBorder
                border.width: 1
            }
            contentItem: Text {
                id: favoriteLabel
                text: page.detail.favorited ? "⭐ 已收藏" : "☆ 收藏"
                color: page.detail.favorited ? Theme.warning : Theme.textPrimary
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingLarge
        spacing: Theme.spacingLarge

        // ---- 3D 可旋转成品预览 (只读 previewMode, 复用 QT-3 视口) --------
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.radiusCard
            color: "#E6ECF2"   // 与场景清屏色同族, 圆角边不突兀
            border.color: Theme.cardBorder
            border.width: 1

            TutorialViewport {
                id: previewViewport
                anchors.fill: parent
                anchors.margins: 2
                previewMode: true
                modelFile: studio.modelFilePath(page.modelId)
                dataDir: studio.dataDirText
                // 只读预览不设 dbFile: 纯看不写, 不建进度存档
            }

            // 操作提示 (左下角浮层, 常驻但视觉很轻, 与教程页同款)
            Rectangle {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.margins: Theme.spacing
                radius: Theme.radiusButton
                color: "#CCFFFFFF"
                width: previewHintLabel.implicitWidth + 2 * Theme.spacing
                height: 40
                visible: previewViewport.sessionReady
                Text {
                    id: previewHintLabel
                    anchors.centerIn: parent
                    text: "🖱 拖动转圈看成品 · 滚轮放大"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.textSecondary
                }
            }

            // 复位视角 (右下角, >= 48 触控目标)
            AbstractButton {
                id: previewResetButton
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: Theme.spacing
                width: previewResetLabel.implicitWidth + 2 * Theme.spacing
                height: Theme.touchTarget
                visible: previewViewport.sessionReady
                onClicked: previewViewport.resetView()
                scale: pressed ? 0.96 : 1.0
                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: previewResetButton.pressed ? Theme.primarySoft : Theme.surface
                    border.color: Theme.cardBorder
                    border.width: 1
                }
                contentItem: Text {
                    id: previewResetLabel
                    text: "🔄 回到最佳视角"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSmall
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // 预览未就绪的温和降级 (P3 零挫败: 名称卡片占位, 不说 "失败")
            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                radius: Theme.radiusCard
                visible: !previewViewport.sessionReady
                color: page.detail.found ? Qt.lighter(Theme.themeColor(page.detail.theme), 1.75)
                                         : Theme.surfaceAlt

                ColumnLayout {
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacingLarge
                    spacing: Theme.spacing
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "🧲"
                        font.pixelSize: 96
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.maximumWidth: parent.width
                        text: page.detail.found ? page.detail.name : ""
                        font.pixelSize: Theme.fontHero
                        font.bold: true
                        color: Theme.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        visible: page.detail.found && page.detail.nameEn !== ""
                        Layout.alignment: Qt.AlignHCenter
                        text: page.detail.found ? page.detail.nameEn : ""
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: previewViewport.statusText !== ""
                              ? previewViewport.statusText : "3D 预览正在准备中"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                    }
                }
            }
        }

        // ---- 信息面板: 元数据 + BOM + 缺片提示 + 开始搭建 -----------------
        ColumnLayout {
            // 嵌套布局在 RowLayout 里默认 fillWidth=true, 必须显式关掉,
            // 否则会与预览区争宽把预览挤没
            Layout.fillWidth: false
            Layout.preferredWidth: 440
            Layout.fillHeight: true
            spacing: Theme.spacing

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentHeight: infoColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ColumnLayout {
                    id: infoColumn
                    width: parent.width
                    spacing: Theme.spacing

                    // -- 难度 / 片数 / 步数 -------------------------------
                    RowLayout {
                        spacing: Theme.spacing
                        Text {
                            text: page.detail.found ? Theme.difficultyStars(page.detail.difficulty) : ""
                            font.pixelSize: Theme.fontButton
                            color: Theme.warning
                        }
                        Rectangle {
                            radius: Theme.radiusButton
                            height: 36
                            width: piecesLabel.implicitWidth + 2 * Theme.spacing
                            color: Theme.primarySoft
                            Text {
                                id: piecesLabel
                                anchors.centerIn: parent
                                text: page.detail.found ? page.detail.pieces + " 片" : ""
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.primary
                            }
                        }
                        Rectangle {
                            radius: Theme.radiusButton
                            height: 36
                            width: stepsLabel.implicitWidth + 2 * Theme.spacing
                            color: Theme.primarySoft
                            Text {
                                id: stepsLabel
                                anchors.centerIn: parent
                                text: page.detail.found ? page.detail.steps + " 步" : ""
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.primary
                            }
                        }
                    }

                    // -- 套装分层 + 免费层徽章 -----------------------------
                    RowLayout {
                        spacing: 8
                        Rectangle {
                            visible: page.detail.found && page.detail.bomKnown
                            radius: Theme.radiusButton
                            height: 36
                            width: tierLabel.implicitWidth + 2 * Theme.spacing
                            color: page.detail.core9Only ? Theme.successSoft : Theme.warningSoft
                            Text {
                                id: tierLabel
                                anchors.centerIn: parent
                                text: page.detail.core9Only ? "🧲 核心 9 片就能搭"
                                                            : "✨ 会用到扩展片"
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: page.detail.core9Only ? Theme.success : Theme.warning
                            }
                        }
                        // 订阅解锁徽章 (温和, 主色浅底不用红色)
                        Rectangle {
                            visible: page.locked
                            radius: Theme.radiusButton
                            height: 36
                            width: subscriptionTag.implicitWidth + 2 * Theme.spacing
                            color: Theme.primarySoft
                            Text {
                                id: subscriptionTag
                                anchors.centerIn: parent
                                text: "🔒 订阅解锁"
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.primary
                            }
                        }
                    }

                    Text {
                        visible: page.detail.found && page.detail.description !== ""
                        Layout.fillWidth: true
                        text: page.detail.found ? page.detail.description : ""
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        lineHeight: 1.4
                    }

                    // -- 进度回显 (进行中 / 已完成) ------------------------
                    Rectangle {
                        visible: page.detail.found && page.detail.status !== 0
                        Layout.fillWidth: true
                        radius: Theme.radiusCard
                        implicitHeight: progressLabel.implicitHeight + 2 * Theme.spacing
                        color: page.detail.status === 2 ? Theme.successSoft : Theme.primarySoft
                        Text {
                            id: progressLabel
                            anchors.fill: parent
                            anchors.margins: Theme.spacing
                            text: page.detail.status === 2
                                  ? "✓ 已经搭好过一次啦, 随时可以再搭"
                                  : "▶ 上次搭到第 " + page.detail.currentStep + "/"
                                    + page.detail.steps + " 步, 可以接着搭"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: page.detail.status === 2 ? Theme.success : Theme.primary
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    // -- BOM 清单 (§5.4: 对照库存, 缺片琥珀提示) ------------
                    Text {
                        text: "需要的磁力片"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                    }

                    Text {
                        visible: page.detail.found && !page.detail.bomKnown
                        Layout.fillWidth: true
                        text: "清单正在准备中"
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                    }

                    Repeater {
                        model: page.bom
                        Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            radius: Theme.radiusCard
                            implicitHeight: 52
                            color: Theme.surface
                            border.color: modelData.missing > 0 ? Theme.warning : Theme.cardBorder
                            border.width: 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: Theme.spacing
                                anchors.rightMargin: Theme.spacing
                                spacing: 8

                                Text {
                                    text: modelData.shapeName
                                    font.pixelSize: Theme.fontBody
                                    font.bold: true
                                    color: Theme.textPrimary
                                }
                                Rectangle {
                                    visible: !modelData.isCore
                                    radius: Theme.radiusButton
                                    height: 26
                                    width: expansionTag.implicitWidth + Theme.spacing
                                    color: Theme.warningSoft
                                    Text {
                                        id: expansionTag
                                        anchors.centerIn: parent
                                        text: "扩展片"
                                        font.pixelSize: Theme.fontSmall
                                        color: Theme.warning
                                    }
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: "× " + modelData.needed
                                    font.pixelSize: Theme.fontBody
                                    font.bold: true
                                    color: Theme.textPrimary
                                }
                                Text {
                                    visible: studio.inventoryConfigured
                                    text: modelData.missing > 0
                                          ? "缺 " + modelData.missing + " 片"
                                          : "✓ 够用"
                                    font.pixelSize: Theme.fontSmall
                                    font.bold: true
                                    color: modelData.missing > 0 ? Theme.warning : Theme.success
                                }
                            }
                        }
                    }

                    // -- 库存对照结论 (温和, 无失败羞辱 §P3) ----------------
                    Rectangle {
                        visible: page.detail.found && page.detail.bomKnown
                                 && studio.inventoryConfigured && !page.detail.canBuild
                        Layout.fillWidth: true
                        radius: Theme.radiusCard
                        implicitHeight: missingBanner.implicitHeight + 2 * Theme.spacing
                        color: Theme.warningSoft
                        border.color: Theme.warning
                        border.width: 1
                        Text {
                            id: missingBanner
                            anchors.fill: parent
                            anchors.margins: Theme.spacing
                            text: "🧩 " + page.detail.missingText
                                  + "。可以先用颜色不同的同款片代替, 或先挑一个「我能搭的」模型"
                            font.pixelSize: Theme.fontBody
                            color: Theme.textPrimary
                            wrapMode: Text.WordWrap
                            lineHeight: 1.4
                        }
                    }

                    Rectangle {
                        visible: page.detail.found && page.detail.bomKnown
                                 && studio.inventoryConfigured && page.detail.canBuild
                        Layout.fillWidth: true
                        radius: Theme.radiusCard
                        implicitHeight: enoughBanner.implicitHeight + 2 * Theme.spacing
                        color: Theme.successSoft
                        Text {
                            id: enoughBanner
                            anchors.fill: parent
                            anchors.margins: Theme.spacing
                            text: "✓ 家里的磁力片够用, 开搭吧!"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: Theme.success
                            wrapMode: Text.WordWrap
                        }
                    }

                    Text {
                        visible: page.detail.found && page.detail.bomKnown
                                 && !studio.inventoryConfigured
                        Layout.fillWidth: true
                        text: "请爸爸妈妈登记家里的磁力片后, 这里会帮你对照缺不缺片"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        lineHeight: 1.3
                    }

                    // -- 订阅内容温和说明 (§11/§12.2: 无价格无催促, 免费层
                    //    先说明白; 免费数实时读目录 studio.freeModelCount) --
                    Rectangle {
                        visible: page.locked
                        Layout.fillWidth: true
                        radius: Theme.radiusCard
                        implicitHeight: subscriptionBanner.implicitHeight + 2 * Theme.spacing
                        color: Theme.primarySoft
                        Text {
                            id: subscriptionBanner
                            anchors.fill: parent
                            anchors.margins: Theme.spacing
                            text: "🔒 这个模型属于订阅内容: 简介和磁力片清单随时可以看, "
                                  + "完整的 3D 分步教程订阅后解锁。免费区还有 "
                                  + studio.freeModelCount
                                  + " 个模型永久免费, 随时开搭。"
                            font.pixelSize: Theme.fontBody
                            color: Theme.textPrimary
                            wrapMode: Text.WordWrap
                            lineHeight: 1.4
                        }
                    }

                    Item { Layout.preferredHeight: Theme.spacing }
                }
            }

            // -- 主 CTA: 开始/继续搭建 (高 64, 占宽 80%, §5.4); 订阅内容
            //    改为「请家长来解锁」, 经家长门导向订阅页 (§11 订阅只在
            //    门后; 儿童侧只说"请家长来解锁", 无价格 §12.2) ------------
            BigButton {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.round(parent.width * 0.8)
                emoji: page.locked ? "🔒"
                                   : (page.detail.status === 1 ? "▶" : "🧲")
                text: page.locked
                      ? "请家长来解锁"
                      : (page.detail.status === 1
                         ? "继续搭建 (第 " + page.detail.currentStep + " 步)"
                         : (page.detail.status === 2 ? "再搭一次" : "开始搭建"))
                accent: Theme.primary
                onClicked: page.locked ? page.openSubscription()
                                       : studio.startBuild(page.modelId)
            }
        }
    }
}
