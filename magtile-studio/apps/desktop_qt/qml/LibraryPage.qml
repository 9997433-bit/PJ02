import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 模型库 (QT-1): 左侧筛选栏 (难度 / 免费模型 / 主题 / 只用核心 9 片 /
// 我能搭的) + 卡片网格 + 进度徽标。数据来自 studio.libraryFilter
// (LibraryFilterModel 包着 LibraryModel), 筛选规范见 UI_UX_SPEC.md
// §5.1; 点卡片进模型详情页 (§5.4)。筛选无结果时给「换个条件试试」
// 空态, 不出现空白页 (§5.2); 开着「我能搭的」时空态改为推荐 3 个
// 现在就能搭的模型 (canBuild, 难度升序)。
//
// 年龄分层 (§2, 读 appSettings.ageModeId, 家长区切换即时生效):
//   4-6 启蒙  无筛选栏, 只留超大主题入口, 每行 2 张超大卡片;
//   7-9 标准  难度 + 免费模型 + 主题三个筛选器, 每行 3~4 张;
//   10+ 进阶  全量筛选 (难度/免费/主题/核心 9 片/我能搭的), 每行 4~5 张。
// =============================================================
Page {
    id: page

    signal back()
    signal openDetail(string modelId)
    signal openInventory()
    signal notify(string message)

    readonly property bool bandJunior: appSettings.ageModeId === "age_4_6"
    readonly property bool bandFull: appSettings.ageModeId === "age_10_12"

    // 被收起的筛选维度同步清零: 看不见的筛选绝不能悄悄过滤列表
    // (否则孩子面对被过滤的列表却没有任何入口能解除筛选)
    function collapseHiddenFilters() {
        // 免费筛选属内容可及性, 7-9 标准档保留 (侧栏可见即保留),
        // 4-6 启蒙档随整栏侧栏收起同步清零
        if (bandJunior) {
            studio.libraryFilter.difficulty = 0
            studio.libraryFilter.freeOnly = false
        }
        if (!bandFull) {
            studio.libraryFilter.core9Only = false
            studio.libraryFilter.buildableOnly = false
        }
    }
    onBandJuniorChanged: collapseHiddenFilters()
    onBandFullChanged: collapseHiddenFilters()
    Component.onCompleted: collapseHiddenFilters()

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 (>= 48) + 标题 + 统计徽标 ---------------------
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

        // ---- 筛选栏 (§5.1 左侧, 可滚动; 4-6 岁启蒙模式整栏收起) --------
        Rectangle {
            visible: !page.bandJunior
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
                    // 分组标题统一加组间留白 (Layout.topMargin), 筛选栏
                    // 不再一整列贴死 —— 分组呼吸感, 儿童一眼找到分区
                    Text {
                        Layout.topMargin: Theme.spacingSmall
                        text: "难度"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: Theme.spacingSmall
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

                    // -- 内容 (免费层, COMMERCIAL_PLAN §2.1: 「免费」标签
                    //    即事实来源; 订阅内容照常可浏览, 只锁教程入口)。
                    //    内容可及性筛选, 7-9 标准档起就展示 (整栏侧栏
                    //    在 4-6 启蒙档已收起, 无需单独 visible 门控) ----
                    Text {
                        Layout.topMargin: Theme.spacingSmall
                        text: "内容"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    FilterChip {
                        Layout.fillWidth: true
                        text: "🎁 免费模型"
                        checked: studio.libraryFilter.freeOnly
                        onClicked: studio.libraryFilter.freeOnly = !checked
                    }

                    // -- 磁力片 (仅 10+ 进阶模式的全量筛选可见, §2) -------
                    Text {
                        visible: page.bandFull
                        Layout.topMargin: Theme.spacingSmall
                        text: "磁力片"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    FilterChip {
                        visible: page.bandFull
                        Layout.fillWidth: true
                        text: "🧲 只用核心 9 片"
                        accent: Theme.success
                        checked: studio.libraryFilter.core9Only
                        onClicked: studio.libraryFilter.core9Only = !checked
                    }
                    FilterChip {
                        visible: page.bandFull
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
                        visible: page.bandFull && !studio.inventoryConfigured
                        Layout.fillWidth: true
                        text: "先登记家里的磁力片, 就能只看现在搭得成的模型啦"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        lineHeight: 1.3
                    }
                    // 库存录入入口 (UI_UX_SPEC.md §10): 未登记时是
                    // onboarding 引导, 已登记时用于随时修改; 7-9 模式
                    // 虽收起「我能搭的」筛选, 入口保留 (录库存不设门槛,
                    // 首页也有常驻入口)
                    FilterChip {
                        Layout.fillWidth: true
                        text: studio.inventoryConfigured ? "✏️ 修改磁力片库存"
                                                         : "🧲 去登记磁力片 ▶"
                        accent: Theme.warning
                        onClicked: page.openInventory()
                    }

                    // -- 主题 --------------------------------------------
                    Text {
                        Layout.topMargin: Theme.spacingSmall
                        text: "主题"
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        color: Theme.textSecondary
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: Theme.spacingSmall
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
                        Layout.topMargin: Theme.spacingSmall
                        visible: studio.libraryFilter.hasActiveFilters
                        text: "↺ 看全部模型"
                        onClicked: studio.libraryFilter.clearFilters()
                    }

                    Item { Layout.preferredHeight: Theme.spacing }
                }
            }
        }

        // ---- 右侧: 超大主题入口 (仅 4-6) + 卡片网格 --------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Theme.spacing

            // 4-6 启蒙模式唯一的"筛选": 超大主题入口胶囊 (§2 无筛选器,
            // 只有大主题入口; 高 64 大字号, 认字过渡期靠颜色也能分辨 §4.6)
            Flow {
                visible: page.bandJunior
                Layout.fillWidth: true
                spacing: Theme.spacing

                FilterChip {
                    implicitHeight: Theme.bigButtonHeight
                    fontSize: Theme.fontButton
                    text: "🌈 全部"
                    checked: studio.libraryFilter.theme === ""
                    onClicked: studio.libraryFilter.theme = ""
                }
                Repeater {
                    model: studio.themes
                    FilterChip {
                        required property string modelData
                        implicitHeight: Theme.bigButtonHeight
                        fontSize: Theme.fontButton
                        text: modelData
                        accent: Theme.themeColor(modelData)
                        checked: studio.libraryFilter.theme === modelData
                        onClicked: studio.libraryFilter.theme =
                                       checked ? "" : modelData
                    }
                }
            }

            GridView {
                id: grid
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: studio.libraryFilter

                // 分龄卡片密度 (§2): 4-6 每行 2 张超大卡片; 7-9 每行
                // 3~4 张; 10+ 每行 4~5 张 (均随窗口宽度自适应, 窄窗兜底)
                property int columns: page.bandJunior
                                      ? 2
                                      : page.bandFull
                                        ? Math.min(5, Math.max(3, Math.floor(width / 236)))
                                        : Math.min(4, Math.max(2, Math.floor(width / 320)))
                cellWidth: Math.floor(width / columns)
                cellHeight: page.bandJunior ? 344 : 220

                // 「我能搭的」空态推荐 (§5.2): 无视其他筛选, canBuild
                // 里按难度升序挑 3 个; 筛选或库存变化时自动重算
                property var buildableRecs: (studio.libraryFilter.buildableOnly
                                             && studio.libraryFilter.count === 0)
                                            ? studio.libraryFilter.recommendBuildable(3)
                                            : []

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

                            // 主题条带 (颜色 + 文字双编码, 色盲安全 §4.7);
                            // 4-6 超大卡片加高条带, 图形占比更大 (§2)
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: page.bandJunior ? 88 : 34
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
                                    font.pixelSize: page.bandJunior ? Theme.fontButton : Theme.fontSmall
                                    font.bold: true
                                }
                                Text {
                                    visible: model.favorited
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.right: parent.right
                                    anchors.rightMargin: Theme.spacing
                                    text: "⭐"
                                    font.pixelSize: page.bandJunior ? Theme.fontButton : Theme.fontSmall
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                Layout.leftMargin: Theme.spacing
                                Layout.rightMargin: Theme.spacing
                                text: model.name
                                font.pixelSize: page.bandJunior ? Theme.fontTitle : Theme.fontButton
                                font.bold: true
                                color: Theme.textPrimary
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.leftMargin: Theme.spacing
                                text: Theme.difficultyStars(model.difficulty)
                                font.pixelSize: page.bandJunior ? Theme.fontButton : Theme.fontBody
                                color: Theme.warning
                            }

                            Text {
                                Layout.leftMargin: Theme.spacing
                                // 4-6 只留最短的数字信息 (§2 文字量最少)
                                text: model.pieces + " 片 · " + model.steps + " 步"
                                      + (!page.bandJunior && model.core9Only ? " · 🧲 核心 9 片" : "")
                                font.pixelSize: page.bandJunior ? Theme.fontButton : Theme.fontBody
                                color: Theme.textSecondary
                            }

                            Item { Layout.fillHeight: true }

                            // 徽标行: 订阅解锁 + 进度 (✓/▶) + 缺片提示, 图形 +
                            // 文字 + 颜色三重编码 (§4.7); 缺片用琥珀, 订阅用
                            // 主色浅底 (均不用红色表达"错误"/"锁")
                            RowLayout {
                                Layout.leftMargin: Theme.spacing
                                Layout.rightMargin: Theme.spacing
                                Layout.bottomMargin: Theme.spacing
                                spacing: 8

                                // 订阅解锁角标 (温和): 元数据照常可浏览, 详情页
                                // 「开始搭建」经家长门引导到订阅页 (§11);
                                // 4-6 超大卡片同步放大 (与进度徽标同规格)
                                Rectangle {
                                    visible: !model.isFree
                                    radius: Theme.radiusButton
                                    height: page.bandJunior ? 40 : 32
                                    width: subscriptionLabel.implicitWidth + 2 * Theme.spacing
                                    color: Theme.primarySoft
                                    Text {
                                        id: subscriptionLabel
                                        anchors.centerIn: parent
                                        text: "🔒 订阅解锁"
                                        font.pixelSize: page.bandJunior ? Theme.fontBody : Theme.fontSmall
                                        font.bold: true
                                        color: Theme.primary
                                    }
                                }

                                Rectangle {
                                    visible: model.status !== 0
                                    radius: Theme.radiusButton
                                    height: page.bandJunior ? 40 : 32
                                    width: statusLabel.implicitWidth + 2 * Theme.spacing
                                    color: model.status === 2 ? Theme.successSoft : Theme.primarySoft
                                    Text {
                                        id: statusLabel
                                        anchors.centerIn: parent
                                        text: model.status === 2 ? "✓ 已搭好" : "▶ 第 " + model.currentStep + " 步"
                                        font.pixelSize: page.bandJunior ? Theme.fontBody : Theme.fontSmall
                                        font.bold: true
                                        color: model.status === 2 ? Theme.success : Theme.primary
                                    }
                                }

                                Rectangle {
                                    // 4-6 不展示缺片提示 (启蒙模式减文字量, §2)
                                    visible: !page.bandJunior && studio.inventoryConfigured
                                             && model.bomKnown && !model.canBuild
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

                // ---- 筛选空态 (§5.2: 不出现空白页) ----------------------
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
                        text: grid.buildableRecs.length > 0
                              ? "这个组合暂时没有模型, 不过这几个现在就能搭:"
                              : "这个组合暂时没有模型, 松开一个筛选就有啦"
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                    }

                    // 「我能搭的」推荐卡: canBuild 里难度升序前 3 个,
                    // 点击直达模型详情 (§5.2 空态推荐)
                    RowLayout {
                        visible: grid.buildableRecs.length > 0
                        Layout.alignment: Qt.AlignHCenter
                        spacing: Theme.spacing

                        Repeater {
                            model: grid.buildableRecs
                            AbstractButton {
                                id: recCard
                                required property var modelData
                                implicitWidth: 208
                                implicitHeight: 150
                                onClicked: page.openDetail(modelData.modelId)
                                scale: pressed ? 0.97 : 1.0
                                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }

                                background: Rectangle {
                                    radius: Theme.radiusCard
                                    color: Theme.surface
                                    border.color: recCard.pressed ? Theme.primary : Theme.cardBorder
                                    border.width: recCard.pressed ? 2 : 1
                                }

                                contentItem: ColumnLayout {
                                    spacing: 6

                                    Text {
                                        Layout.fillWidth: true
                                        Layout.topMargin: 12
                                        Layout.leftMargin: Theme.spacing
                                        Layout.rightMargin: Theme.spacing
                                        text: recCard.modelData.name
                                        font.pixelSize: Theme.fontBody
                                        font.bold: true
                                        color: Theme.textPrimary
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        Layout.leftMargin: Theme.spacing
                                        text: Theme.difficultyStars(recCard.modelData.difficulty)
                                        font.pixelSize: Theme.fontSmall
                                        color: Theme.warning
                                    }
                                    Text {
                                        Layout.leftMargin: Theme.spacing
                                        text: recCard.modelData.pieces + " 片 · " + recCard.modelData.theme
                                        font.pixelSize: Theme.fontSmall
                                        color: Theme.textSecondary
                                    }
                                    Item { Layout.fillHeight: true }
                                    Rectangle {
                                        Layout.leftMargin: Theme.spacing
                                        Layout.bottomMargin: 12
                                        radius: Theme.radiusButton
                                        height: 28
                                        width: recTag.implicitWidth + 2 * Theme.spacing
                                        color: Theme.successSoft
                                        Text {
                                            id: recTag
                                            anchors.centerIn: parent
                                            text: "✓ 现在就能搭"
                                            font.pixelSize: Theme.fontSmall
                                            font.bold: true
                                            color: Theme.success
                                        }
                                    }
                                }
                            }
                        }
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
    }

    // ---- 目录空态 / 加载失败态 (§5.2: 不出现空白页, 不说 "失败") --------
    // 目录读取是同步的: modelCount === 0 即 "没读到" (加载中或出错都
    // 归到这里)。给温和文案 + 重试大按钮 (studio.reload 幂等可重入),
    // 技术细节 (statusMessage) 以小字给家长看, 儿童侧只见引导不见报错。
    ColumnLayout {
        visible: studio.modelCount === 0
        anchors.centerIn: parent
        width: Math.min(parent.width - 2 * Theme.spacingLarge, 520)
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
            Layout.fillWidth: true
            text: "这次没有找到模型, 别着急 —— 点下面的按钮再叫它们一次"
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 1.4
        }
        BigButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Theme.spacingSmall
            emoji: "🔄"
            text: "再试一次"
            accent: Theme.primary
            onClicked: {
                studio.reload()
                if (studio.modelCount > 0)
                    page.notify("模型们到齐啦, 开搭吧!")
            }
        }
        // 家长可读的小字诊断 (statusMessage 带具体原因, 儿童侧不放大)
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.topMargin: Theme.spacingSmall
            text: studio.statusMessage
            font.pixelSize: Theme.fontSmall
            color: Theme.textSecondary
            opacity: 0.8
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
