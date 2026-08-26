import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 进度页「我的作品」(UI_UX_SPEC.md §7, QT-4): 顶部三格温和统计
// (已完成/进行中/收藏) + 成就墙条带 (点亮的徽章一眼可见, 入口进
// 全览) + 进行中列表 (进度条 + 继续搭建) + 已完成列表 (完成日期
// 与用时 + 再搭一次) + 我的收藏。数据经 StudioBackend 读进度存档
// (与 CLI `progress list` / GL 版同一份 SQLite)。
// 页面上只有正向与中性反馈 (§4.3): 没有分数没有排名, 空态温和
// 引导去模型库; 点任意作品行直达模型详情 (继续/再搭都在详情页
// 的大按钮上, 与全应用「开始搭建」同一条路由)。
// =============================================================
Page {
    id: page

    signal back()
    signal openModel(string modelId)
    signal openAchievements()
    signal openLibrary()

    // 列表快照: 进入时读一次, 存档变化 (catalogChanged) 时刷新
    property var inProgressRows: []
    property var completedRows: []
    property var favoriteRows: []
    property var badges: []

    function refresh() {
        inProgressRows = studio.inProgressList()
        completedRows = studio.completedList()
        favoriteRows = studio.favoritesList()
        badges = studio.achievementsList()
    }

    Component.onCompleted: refresh()
    Connections {
        target: studio
        function onCatalogChanged() { page.refresh() }
    }

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
            text: "🏆 我的作品"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
    }

    // ---- 复用小组件 ---------------------------------------------------

    /// 顶部统计格: 图形 + 数字 + 文字三重编码 (§4.7, 不单靠颜色)
    component StatCard: Rectangle {
        property string emoji: ""
        property string label: ""
        property int count: 0
        property color fg: Theme.primary
        property color bg: Theme.primarySoft

        Layout.fillWidth: true
        implicitHeight: 88
        radius: Theme.radiusCard
        color: bg
        border.color: fg
        border.width: 1

        RowLayout {
            anchors.centerIn: parent
            spacing: 10
            Text {
                text: emoji
                font.pixelSize: Theme.fontTitle
                color: fg
            }
            Text {
                text: count
                font.pixelSize: Theme.fontTitle
                font.bold: true
                color: Theme.textPrimary
            }
            Text {
                text: label
                font.pixelSize: Theme.fontBody
                color: Theme.textSecondary
            }
        }
    }

    /// 分区标题行
    component SectionTitle: Text {
        Layout.topMargin: Theme.spacing
        font.pixelSize: Theme.fontButton
        font.bold: true
        color: Theme.textPrimary
    }

    // ---- 主体: 居中滚动列 ---------------------------------------------
    Flickable {
        anchors.fill: parent
        contentHeight: bodyColumn.implicitHeight + 2 * Theme.spacingLarge
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: bodyColumn
            anchors.horizontalCenter: parent.horizontalCenter
            y: Theme.spacingLarge
            width: Math.min(page.width - 2 * Theme.spacingLarge, 760)
            spacing: Theme.spacing

            // ---- 三格温和统计 ------------------------------------------
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.spacing

                StatCard { emoji: "✓"; label: "已完成"; count: studio.completedCount; fg: Theme.success; bg: Theme.successSoft }
                StatCard { emoji: "▶"; label: "进行中"; count: studio.inProgressCount; fg: Theme.primary; bg: Theme.primarySoft }
                StatCard { emoji: "⭐"; label: "收藏"; count: studio.favoriteCount; fg: Theme.warning; bg: Theme.warningSoft }
            }

            // ---- 成就墙条带 (§7.1: 点亮的徽章 + 全览入口) ---------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: badgeColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: badgeColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: Theme.spacing
                    anchors.rightMargin: Theme.spacing
                    spacing: Theme.spacing

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "🏅 成就墙"
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: Theme.textPrimary
                        }
                        Item { Layout.fillWidth: true }
                        AbstractButton {
                            id: allBadgesButton
                            Layout.preferredHeight: Theme.touchTarget
                            Layout.preferredWidth: allBadgesText.implicitWidth + 2 * Theme.spacing
                            onClicked: page.openAchievements()
                            background: Rectangle {
                                radius: Theme.radiusButton
                                color: allBadgesButton.pressed ? Theme.primarySoft : "transparent"
                                border.color: Theme.cardBorder
                                border.width: 1
                            }
                            contentItem: Text {
                                id: allBadgesText
                                text: "看看全部徽章 ▶"
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.primary
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    // 徽章胶囊: 点亮 = 完成绿 + ✓; 未点亮 = 灰色剪影 + …
                    // (图形+文字双编码, 不显示进度百分比, §7.1 防焦虑)
                    Flow {
                        Layout.fillWidth: true
                        spacing: 10

                        Repeater {
                            model: page.badges
                            delegate: Rectangle {
                                required property var modelData
                                width: chipRow.implicitWidth + 2 * Theme.spacing
                                height: Theme.touchTarget
                                radius: Theme.radiusButton
                                color: modelData.unlocked ? Theme.successSoft : Theme.surfaceAlt
                                border.color: modelData.unlocked ? Theme.success : Theme.cardBorder
                                border.width: 1

                                Row {
                                    id: chipRow
                                    anchors.centerIn: parent
                                    spacing: 6
                                    Text {
                                        text: modelData.emoji
                                        font.pixelSize: Theme.fontBody
                                        opacity: modelData.unlocked ? 1.0 : 0.35
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    Text {
                                        text: modelData.name + (modelData.unlocked ? " ✓" : " …")
                                        font.pixelSize: Theme.fontBody
                                        font.bold: modelData.unlocked
                                        color: modelData.unlocked ? Theme.success : Theme.textSecondary
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ---- 温和空态 (§4.3: 只有引导, 没有"空空如也"的挫败感) -------
            Rectangle {
                visible: page.inProgressRows.length === 0 && page.completedRows.length === 0
                Layout.fillWidth: true
                implicitHeight: emptyColumn.implicitHeight + 2 * Theme.spacingLarge
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: emptyColumn
                    anchors.centerIn: parent
                    spacing: Theme.spacing

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "🧲"
                        font.pixelSize: 44
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "第一个作品在等你"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "从模型库挑一个喜欢的模型, 搭完它就会出现在这里啦"
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                    }
                    BigButton {
                        Layout.alignment: Qt.AlignHCenter
                        emoji: "🏰"
                        text: "去模型库挑一个"
                        accent: Theme.primary
                        onClicked: page.openLibrary()
                    }
                }
            }

            // ---- 进行中 (按最近游玩倒序) --------------------------------
            SectionTitle {
                visible: page.inProgressRows.length > 0
                text: "▶ 进行中 (" + page.inProgressRows.length + ")"
            }

            Repeater {
                model: page.inProgressRows
                delegate: AbstractButton {
                    id: inProgressRow
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 84
                    onClicked: page.openModel(modelData.modelId)
                    scale: pressed ? 0.98 : 1.0
                    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                    background: Rectangle {
                        radius: Theme.radiusCard
                        color: Theme.surface
                        border.color: inProgressRow.pressed ? Theme.primary : Theme.cardBorder
                        border.width: 1
                    }
                    contentItem: RowLayout {
                        spacing: Theme.spacing

                        Text {
                            Layout.leftMargin: Theme.spacing
                            text: "▶"
                            font.pixelSize: Theme.fontTitle
                            color: Theme.primary
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: inProgressRow.modelData.name
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.textPrimary
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Theme.spacing
                                // 进度条: 图形 + "第 x/y 步" 文字双编码 (§4.7)
                                Rectangle {
                                    id: progressTrack
                                    Layout.fillWidth: true
                                    Layout.maximumWidth: 260
                                    height: 10
                                    radius: 5
                                    color: Theme.surfaceAlt
                                    border.color: Theme.cardBorder
                                    border.width: 1
                                    Rectangle {
                                        width: inProgressRow.modelData.stepCount > 0
                                               ? parent.width * Math.min(1.0, inProgressRow.modelData.currentStep / inProgressRow.modelData.stepCount)
                                               : 0
                                        height: parent.height
                                        radius: 5
                                        color: Theme.primary
                                    }
                                }
                                Text {
                                    text: "第 " + inProgressRow.modelData.currentStep + "/" + inProgressRow.modelData.stepCount + " 步"
                                    font.pixelSize: Theme.fontSmall
                                    color: Theme.textSecondary
                                }
                                Text {
                                    visible: inProgressRow.modelData.playText.length > 0
                                    text: inProgressRow.modelData.playText
                                    font.pixelSize: Theme.fontSmall
                                    color: Theme.textSecondary
                                }
                            }
                        }
                        Text {
                            Layout.rightMargin: Theme.spacing
                            text: "继续搭建 ▶"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: Theme.primary
                        }
                    }
                }
            }

            // ---- 已完成 (按完成时间倒序) --------------------------------
            SectionTitle {
                visible: page.completedRows.length > 0
                text: "✓ 已完成 (" + page.completedRows.length + ")"
            }

            Repeater {
                model: page.completedRows
                delegate: AbstractButton {
                    id: completedRow
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 76
                    onClicked: page.openModel(modelData.modelId)
                    scale: pressed ? 0.98 : 1.0
                    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                    background: Rectangle {
                        radius: Theme.radiusCard
                        color: Theme.surface
                        border.color: completedRow.pressed ? Theme.success : Theme.cardBorder
                        border.width: 1
                    }
                    contentItem: RowLayout {
                        spacing: Theme.spacing

                        Text {
                            Layout.leftMargin: Theme.spacing
                            text: "✓"
                            font.pixelSize: Theme.fontTitle
                            font.bold: true
                            color: Theme.success
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: completedRow.modelData.name
                                font.pixelSize: Theme.fontBody
                                font.bold: true
                                color: Theme.textPrimary
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            Text {
                                visible: text.length > 0
                                text: {
                                    var parts = []
                                    if (completedRow.modelData.metaText.length > 0)
                                        parts.push(completedRow.modelData.metaText)
                                    if (completedRow.modelData.pieces > 0)
                                        parts.push(completedRow.modelData.pieces + " 片")
                                    return parts.join(" · ")
                                }
                                font.pixelSize: Theme.fontSmall
                                color: Theme.textSecondary
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                        Text {
                            Layout.rightMargin: Theme.spacing
                            text: "再搭一次 ▶"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: Theme.success
                        }
                    }
                }
            }

            // ---- 我的收藏 (点击直达详情) --------------------------------
            SectionTitle {
                visible: page.favoriteRows.length > 0
                text: "⭐ 我的收藏 (" + page.favoriteRows.length + ")"
            }

            Flow {
                visible: page.favoriteRows.length > 0
                Layout.fillWidth: true
                spacing: 10

                Repeater {
                    model: page.favoriteRows
                    delegate: AbstractButton {
                        id: favoriteChip
                        required property var modelData
                        width: favoriteChipRow.implicitWidth + 2 * Theme.spacing
                        height: Theme.touchTarget
                        onClicked: page.openModel(modelData.modelId)
                        scale: pressed ? 0.96 : 1.0
                        Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: favoriteChip.pressed ? Theme.warningSoft : Theme.surface
                            border.color: Theme.warning
                            border.width: 1
                        }
                        contentItem: Row {
                            id: favoriteChipRow
                            spacing: 6
                            Text {
                                text: "⭐"
                                font.pixelSize: Theme.fontBody
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: favoriteChip.modelData.name
                                font.pixelSize: Theme.fontBody
                                color: Theme.textPrimary
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                }
            }
        }
    }

    // ---- 页脚状态行 (与首页同款, 存档不可用时的温和提示也在此) --------
    footer: Item {
        height: 48
        Text {
            anchors.centerIn: parent
            text: studio.statusMessage
            font.pixelSize: Theme.fontSmall
            color: Theme.textSecondary
            elide: Text.ElideMiddle
            width: parent.width - 2 * Theme.spacingLarge
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
