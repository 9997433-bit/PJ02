import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 磁力片库存录入 (UI_UX_SPEC.md §10.2): 全部片型中文名 + 大号
// − / + 步进器 (48dp, 长按连加) + 数量直接输入, 按 基础套装 /
// 扩展包 分组。数据经 "inventory" 后端桥 (InventoryBackend) 读写
// ProgressStore 的 tile_inventory 表 —— 与 CLI `inventory set` 和
// GL 版录入界面同一份 SQLite。保存后调 studio.reload() 刷新
// 「我能搭的」筛选; 「保存, 看看我能搭什么」直达已开筛选的模型库。
// 编辑副本只存内存, 「返回」不落盘 (温和, 不弹确认)。
// =============================================================
Page {
    id: page

    signal back()
    signal notify(string message)
    /// 保存成功后 "看看我能搭什么": 由 Main.qml 路由到已开
    /// 「我能搭的」筛选的模型库。
    signal lookWhatICanBuild()

    /// 编辑副本 (shapeId -> count): 进入页面时从存档快照, 保存才落盘。
    property var counts: ({})
    property int totalCount: 0
    property var rowsData: []

    function reloadRows() {
        rowsData = inventory.rows()
        var c = {}
        var t = 0
        for (var i = 0; i < rowsData.length; ++i) {
            c[rowsData[i].shapeId] = rowsData[i].count
            t += rowsData[i].count
        }
        counts = c
        totalCount = t
    }

    function updateCount(shapeId, value) {
        var v = Math.max(0, Math.min(999, Math.round(value)))
        counts[shapeId] = v
        var t = 0
        for (var key in counts) t += counts[key]
        totalCount = t
        return v
    }

    function saveAll(andMatch) {
        if (!inventory.save(counts)) {
            // P3 零挫败: 存档暂不可用时温和提示, 不弹"失败"
            page.notify("库存暂时没保存上, 稍后再试一次就好")
            return
        }
        studio.reload()   // 刷新「我能搭的」徽标与筛选数据
        if (andMatch) {
            page.lookWhatICanBuild()
        } else {
            page.notify("已记住家里的 " + totalCount + " 片磁力片")
            page.back()
        }
    }

    Component.onCompleted: reloadRows()

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 (>= 48) + 标题 ------------------------------
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
            text: "🧲 家里有哪些磁力片?"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            radius: Theme.radiusButton
            color: Theme.primarySoft
            width: totalBadge.implicitWidth + 2 * Theme.spacing
            height: 40
            Text {
                id: totalBadge
                anchors.centerIn: parent
                text: "合计 " + page.totalCount + " 片"
                font.pixelSize: Theme.fontSmall
                font.bold: true
                color: Theme.primary
            }
        }
    }

    // ---- 主体: 分组卡片流 (可滚动) ----------------------------------
    Flickable {
        anchors.fill: parent
        anchors.margins: Theme.spacing
        contentHeight: contentColumn.implicitHeight + Theme.spacingLarge
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: contentColumn
            width: parent.width
            spacing: Theme.spacing

            Text {
                Layout.fillWidth: true
                text: "照着盒子数一数, 用 − / + 或直接输入数量; 保存后模型库就能筛出「我能搭的」"
                font.pixelSize: Theme.fontBody
                color: Theme.textSecondary
                wrapMode: Text.WordWrap
            }

            // -- 基础套装 (核心 9 片型) ----------------------------------
            RowLayout {
                spacing: Theme.spacing
                Text {
                    text: "基础套装"
                    font.pixelSize: Theme.fontButton
                    font.bold: true
                    color: Theme.textPrimary
                }
                Text {
                    text: "最常见的 9 种片型"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.textSecondary
                }
            }
            Flow {
                Layout.fillWidth: true
                spacing: Theme.spacing
                Repeater {
                    model: page.rowsData.filter(function(r) { return !r.expansion })
                    delegate: countCard
                }
            }

            // -- 扩展包 --------------------------------------------------
            RowLayout {
                spacing: Theme.spacing
                Text {
                    text: "扩展包"
                    font.pixelSize: Theme.fontButton
                    font.bold: true
                    color: Theme.textPrimary
                }
                Text {
                    text: "没有就保持 0, 不影响基础模型"
                    font.pixelSize: Theme.fontSmall
                    color: Theme.textSecondary
                }
            }
            Flow {
                Layout.fillWidth: true
                spacing: Theme.spacing
                Repeater {
                    model: page.rowsData.filter(function(r) { return r.expansion })
                    delegate: countCard
                }
            }
        }
    }

    // ---- 片型计数卡片 (中文名 + − / 输入 / +) ------------------------
    Component {
        id: countCard

        Rectangle {
            id: card
            required property var modelData
            property int count: modelData.count

            width: 250
            height: 118
            radius: Theme.radiusCard
            color: Theme.surface
            border.color: count > 0 ? Theme.primary : Theme.cardBorder
            border.width: 1

            function apply(value) {
                count = page.updateCount(modelData.shapeId, value)
            }

            Text {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: Theme.spacing
                text: card.modelData.nameZh
                font.pixelSize: Theme.fontBody
                font.bold: true
                color: card.count > 0 ? Theme.textPrimary : Theme.textSecondary
            }

            RowLayout {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Theme.spacing
                spacing: 8

                // 大号步进器 (§4.1 触控目标 48dp; autoRepeat 长按连减/连加)
                AbstractButton {
                    id: minusButton
                    Layout.preferredWidth: Theme.touchTarget
                    Layout.preferredHeight: Theme.touchTarget
                    enabled: card.count > 0
                    autoRepeat: true
                    autoRepeatDelay: 400
                    autoRepeatInterval: 80
                    onClicked: card.apply(card.count - 1)
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: minusButton.pressed ? Theme.primaryPressed
                             : minusButton.enabled ? Theme.primarySoft : Theme.surfaceAlt
                    }
                    contentItem: Text {
                        text: "−"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: minusButton.pressed ? "white"
                             : minusButton.enabled ? Theme.primary : Theme.cardBorder
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // 数量直接输入 (数字键盘; 失焦/回车时夹到 0..999)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Theme.touchTarget
                    radius: Theme.radiusCard / 2
                    color: Theme.surfaceAlt
                    border.color: countInput.activeFocus ? Theme.primary : Theme.cardBorder
                    border.width: 1
                    TextInput {
                        id: countInput
                        anchors.fill: parent
                        horizontalAlignment: TextInput.AlignHCenter
                        verticalAlignment: TextInput.AlignVCenter
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                        inputMethodHints: Qt.ImhDigitsOnly
                        validator: IntValidator { bottom: 0; top: 999 }
                        text: card.count
                        onEditingFinished: card.apply(parseInt(text) || 0)
                    }
                }

                AbstractButton {
                    id: plusButton
                    Layout.preferredWidth: Theme.touchTarget
                    Layout.preferredHeight: Theme.touchTarget
                    enabled: card.count < 999
                    autoRepeat: true
                    autoRepeatDelay: 400
                    autoRepeatInterval: 80
                    onClicked: card.apply(card.count + 1)
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: plusButton.pressed ? Theme.primaryPressed : Theme.primary
                    }
                    contentItem: Text {
                        text: "+"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }

    // ---- 页脚操作条: 保存 / 保存并看看能搭什么 ------------------------
    footer: Rectangle {
        height: 88
        color: Theme.surface
        border.color: Theme.cardBorder
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Theme.spacingLarge
            anchors.rightMargin: Theme.spacingLarge
            spacing: Theme.spacing

            Text {
                text: "数量为 0 的片型也会记住「明确没有」"
                font.pixelSize: Theme.fontSmall
                color: Theme.textSecondary
            }
            Item { Layout.fillWidth: true }

            AbstractButton {
                id: saveButton
                Layout.preferredWidth: 168
                Layout.preferredHeight: Theme.bigButtonHeight
                onClicked: page.saveAll(false)
                scale: pressed ? 0.97 : 1.0
                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: saveButton.pressed ? Theme.successSoft : Theme.surface
                    border.color: Theme.success
                    border.width: 2
                }
                contentItem: Text {
                    text: "保存库存"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.success
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            AbstractButton {
                id: saveMatchButton
                Layout.preferredWidth: 280
                Layout.preferredHeight: Theme.bigButtonHeight
                onClicked: page.saveAll(true)
                scale: pressed ? 0.97 : 1.0
                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: saveMatchButton.pressed ? Theme.primaryPressed : Theme.primary
                }
                contentItem: Text {
                    text: "保存, 看看我能搭什么 ▶"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
}
