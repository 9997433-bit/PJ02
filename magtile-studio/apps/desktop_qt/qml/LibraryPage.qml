import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 模型库 (QT-1): 左侧筛选栏 (难度 / 主题 / 只用核心 9 片 / 我能搭的)
// + 卡片网格 + 进度徽标。数据来自 studio.libraryFilter
// (LibraryFilterModel 包着 LibraryModel), 筛选规范见 UI_UX_SPEC.md
// §5.1; 点卡片进模型详情页 (§5.4)。筛选无结果时给「换个条件试试」
// 空态, 不出现空白页 (§5.2)。
// =============================================================
Page {
    id: page

    signal back()
    signal openDetail(string modelId)
    signal openInventory()
    signal notify(string message)

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 (>= 48) + 标题 + 统计徽标 ---------------------
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
                text: "← 回首页"
                color: "white"
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Text {
            anchors.centerIn: parent
            text: "模型库"
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
            width: countLabel.implicitWidth + 2 * Theme.spacing
            height: 40
            Text {
                id: countLabel
                anchors.centerIn: parent
                text: studio.libraryFilter.hasActiveFilters
                      ? "挑出 " + studio.libraryFilter.count + " / " + studio.modelCount + " 个模型"
                      : studio.modelCount + " 个模型 · " + studio.completedCount + " 个已搭好"
                font.pixelSize: Theme.fontSmall
                color: Theme.primary
                font.bold: true
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacing
        spacing: Theme.spacing

        // ---- 筛选栏 (§5.1 左侧, 可滚动) --------------------------------
        Rectangle {
            Layout.preferredWidth: 264
            Layout.fillHeight: true
            radius: Theme.radiusCard
            color: Theme.surface
            border.color: Theme.cardBorder
            border.width: 1

            Flickable {
                anchors.fill: parent
                anchors.margins: Theme.spacing
                contentHeight: filterColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ColumnLayout {
                    id: filterColumn
                    width: parent.width
                    spacing: Theme.spacing

                    Text {
                        text: "筛选"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.textPrimary
                    }

                    // -- 难度 --------------------------------------------
                    Text {
                        text: "难度"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        FilterChip {
                            text: "全部"
                            checked: studio.libraryFilter.difficulty === 0
                            onClicked: studio.libraryFilter.difficulty = 0
                        }
                        Repeater {
                            model: 5
                            FilterChip {
                                required property int index
                                text: Theme.difficultyStars(index + 1)
                                checked: studio.libraryFilter.difficulty === index + 1
                                onClicked: studio.libraryFilter.difficulty =
                                               checked ? 0 : index + 1
                            }
                        }
                    }

                    // -- 磁力片 ------------------------------------------
                    Text {
                        text: "磁力片"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    FilterChip {
                        Layout.fillWidth: true
                        text: "🧲 只用核心 9 片"
                        accent: Theme.success
                        checked: studio.libraryFilter.core9Only
                        onClicked: studio.libraryFilter.core9Only = !checked
                    }
                    FilterChip {
                        Layout.fillWidth: true
                        text: "💪 我能搭的"
                        accent: Theme.success
                        enabled: studio.inventoryConfigured
                        checked: studio.libraryFilter.buildableOnly
                        onClicked: {
                            if (studio.inventoryConfigured)
                                studio.libraryFilter.buildableOnly = !checked
                        }
                    }
                    Text {
                        visible: !studio.inventoryConfigured
                        Layout.fillWidth: true
                        text: "先登记家里的磁力片, 就能只看现在搭得成的模型啦"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        lineHeight: 1.3
                    }
                    // 库存录入入口 (UI_UX_SPEC.md §10): 未登记时是
                    // onboarding 引导, 已登记时用于随时修改
                    FilterChip {
                        Layout.fillWidth: true
                        text: studio.inventoryConfigured ? "✏️ 修改磁力片库存"
                                                         : "🧲 去登记磁力片 ▶"
                        accent: Theme.warning
                        onClicked: page.openInventory()
                    }

                    // -- 主题 --------------------------------------------
                    Text {
                        text: "主题"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        FilterChip {
                            text: "全部"
                            checked: studio.libraryFilter.theme === ""
                            onClicked: studio.libraryFilter.theme = ""
                        }
                        Repeater {
                            model: studio.themes
                            FilterChip {
                                required property string modelData
                                text: modelData
                                accent: Theme.themeColor(modelData)
                                checked: studio.libraryFilter.theme === modelData
                                onClicked: studio.libraryFilter.theme =
                                               checked ? "" : modelData
                            }
                        }
                    }

                    // -- 清除筛选 ----------------------------------------
                    FilterChip {
                        Layout.fillWidth: true
                        visible: studio.libraryFilter.hasActiveFilters
                        text: "↺ 看全部模型"
                        onClicked: studio.libraryFilter.clearFilters()
                    }

                    Item { Layout.preferredHeight: Theme.spacing }
                }
            }
        }

        // ---- 卡片网格 --------------------------------------------------
        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: studio.libraryFilter

            // 每行 3~4 张 (7-9 岁标准模式, §2), 随窗口宽度自适应
            property int columns: Math.max(2, Math.floor(width / 320))
            cellWidth: Math.floor(width / columns)
            cellHeight: 220

            delegate: Item {
                width: grid.cellWidth
                height: grid.cellHeight

                AbstractButton {
                    id: card
                    anchors.fill: parent
                    anchors.margins: Theme.spacing / 2
                    onClicked: page.openDetail(model.modelId)
                    scale: pressed ? 0.97 : 1.0
                    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                    background: Rectangle {
                        radius: Theme.radiusCard
                        color: Theme.surface
                        border.color: card.pressed ? Theme.primary : Theme.cardBorder
                        border.width: card.pressed ? 2 : 1
                    }

                    contentItem: ColumnLayout {
                        spacing: 8

                        // 主题条带 (颜色 + 文字双编码, 色盲安全 §4.7)
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            radius: Theme.radiusCard
                            color: Theme.themeColor(model.theme)
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
                                text: model.theme
                                color: "white"
                                font.pixelSize: Theme.fontSmall
                                font.bold: true
                            }
                            Text {
                                visible: model.favorited
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: Theme.spacing
                                text: "⭐"
                                font.pixelSize: Theme.fontSmall
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            Layout.leftMargin: Theme.spacing
                            Layout.rightMargin: Theme.spacing
                            text: model.name
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: Theme.textPrimary
                            elide: Text.ElideRight
                        }

                        Text {
                            Layout.leftMargin: Theme.spacing
                            text: Theme.difficultyStars(model.difficulty)
                            font.pixelSize: Theme.fontBody
                            color: Theme.warning
                        }

                        Text {
                            Layout.leftMargin: Theme.spacing
                            text: model.pieces + " 片 · " + model.steps + " 步"
                                  + (model.core9Only ? " · 🧲 核心 9 片" : "")
                            font.pixelSize: Theme.fontBody
                            color: Theme.textSecondary
                        }

                        Item { Layout.fillHeight: true }

                        // 徽标行: 进度 (✓/▶) + 缺片提示, 图形 + 文字 + 颜色
                        // 三重编码 (§4.7); 缺片用琥珀 (不用红色表达"错误")
                        RowLayout {
                            Layout.leftMargin: Theme.spacing
                            Layout.rightMargin: Theme.spacing
                            Layout.bottomMargin: Theme.spacing
                            spacing: 8

                            Rectangle {
                                visible: model.status !== 0
                                radius: Theme.radiusButton
                                height: 32
                                width: statusLabel.implicitWidth + 2 * Theme.spacing
                                color: model.status === 2 ? Theme.successSoft : Theme.primarySoft
                                Text {
                                    id: statusLabel
                                    anchors.centerIn: parent
                                    text: model.status === 2 ? "✓ 已搭好" : "▶ 第 " + model.currentStep + " 步"
                                    font.pixelSize: Theme.fontSmall
                                    font.bold: true
                                    color: model.status === 2 ? Theme.success : Theme.primary
                                }
                            }

                            Rectangle {
                                visible: studio.inventoryConfigured && model.bomKnown && !model.canBuild
                                radius: Theme.radiusButton
                                height: 32
                                width: missingLabel.implicitWidth + 2 * Theme.spacing
                                color: Theme.warningSoft
                                Text {
                                    id: missingLabel
                                    anchors.centerIn: parent
                                    text: "🧩 还缺 " + model.missingTotal + " 片"
                                    font.pixelSize: Theme.fontSmall
                                    font.bold: true
                                    color: Theme.warning
                                }
                            }

                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }

            // ---- 筛选空态 (§5.2: 不出现空白页) --------------------------
            ColumnLayout {
                visible: studio.modelCount > 0 && studio.libraryFilter.count === 0
                anchors.centerIn: parent
                spacing: Theme.spacing
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "🔍"
                    font.pixelSize: 64
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "换个条件试试"
                    font.pixelSize: Theme.fontTitle
                    font.bold: true
                    color: Theme.textPrimary
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "这个组合暂时没有模型, 松开一个筛选就有啦"
                    font.pixelSize: Theme.fontBody
                    color: Theme.textSecondary
                }
                BigButton {
                    Layout.alignment: Qt.AlignHCenter
                    emoji: "↺"
                    text: "看全部模型"
                    onClicked: studio.libraryFilter.clearFilters()
                }
            }
        }
    }

    // ---- 目录空态 (§5.2: 不出现空白页) ---------------------------------
    ColumnLayout {
        visible: studio.modelCount === 0
        anchors.centerIn: parent
        spacing: Theme.spacing
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "🧲"
            font.pixelSize: 64
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "模型们正在路上"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "用 --data-dir 指向仓库的 data 目录就能看到全部模型"
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
        }
    }
}
