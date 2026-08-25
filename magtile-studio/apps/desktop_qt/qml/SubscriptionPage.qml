import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 订阅页脚手架 (QT-5, UI_UX_SPEC.md §11): 必须在家长门之后才可见
// (由 Main.qml 路由与会话守卫保证)。给家长看的页面 = 信息完整、
// 无套路: 页首明示免费额度 (反套路即信任), 温和说明订阅解锁全库,
// 「免费 vs 全库」对比数字实时读模型目录 (studio.freeModelCount /
// studio.modelCount, 与 QA 红线工具同一「免费」标签口径)。
// 主 CTA 为「即将上线」占位 + mailto 联系通道 —— 不接任何 IAP /
// 支付 SDK; 正式三卡定价 (月/年/家庭年) 与恢复购买在付费闭环
// (COMMERCIAL_PLAN.md V1) 时替换本页占位区。
// 红线 (§11 禁止事项): 无倒计时、无「即将涨价」、无预勾选加购、
// 不索取任何个人信息; 全页不用红色与紧迫话术。
// =============================================================
Page {
    id: page

    signal back()
    signal notify(string message)

    /// Main.qml 会话守卫: 会话失效时该页自动退回首页
    readonly property bool requiresParentSession: true

    /// 上线前替换为正式支持邮箱 (RFC 2606 保留域, 占位期不可达)
    readonly property string contactMail: "hello@magtile.example"

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 + 标题 ---------------------------------------
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
            text: "订阅"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
    }

    // ---- 主体: 居中卡片列 (成人信息密度, 允许小字号说明) ---------------
    Flickable {
        anchors.fill: parent
        contentHeight: bodyColumn.implicitHeight + 2 * Theme.spacingLarge
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: bodyColumn
            anchors.horizontalCenter: parent.horizontalCenter
            y: Theme.spacingLarge
            width: Math.min(page.width - 2 * Theme.spacingLarge, 640)
            spacing: Theme.spacing

            // ---- 页首免费额度明示 (§11 反套路即信任) --------------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: freeNoticeText.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.successSoft
                Text {
                    id: freeNoticeText
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    text: studio.freeModelCount > 0
                          ? "✓ 无需付费, 现在就能玩 " + studio.freeModelCount
                            + " 个精选模型 —— 永久免费, 功能不打折"
                          : "✓ 无需付费也可以玩精选模型 —— 永久免费, 功能不打折"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.success
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }
            }

            // ---- 订阅说明 (温和文案: 只讲价值, 不写羞辱/紧迫话术) --------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: introColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: introColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "订阅能解锁什么"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "一份订阅解锁模型库里的全部模型, 以及之后每周的新模型。"
                              + "免费的精选模型永远免费; 订阅只增加内容, 不锁任何功能 ——"
                              + " 3D 教程、物理校验、进度存档对所有家庭完全一样。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ---- 免费 vs 全库对比 (数字实时读模型目录) -------------------
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: compareRow.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                RowLayout {
                    id: compareRow
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: Theme.spacing

                    // 免费层 (完成绿: 已拥有, 不是"缺失")
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        spacing: 4
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "现在免费畅玩"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: studio.freeModelCount > 0 ? String(studio.freeModelCount) : "—"
                            font.pixelSize: Theme.fontHero
                            font.bold: true
                            color: Theme.success
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "个精选模型"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.fillHeight: true
                        color: Theme.cardBorder
                    }

                    // 全库 (磁力蓝: 订阅解锁的内容量)
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        spacing: 4
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "订阅解锁全库"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: studio.modelCount > 0 ? String(studio.modelCount) : "—"
                            font.pixelSize: Theme.fontHero
                            font.bold: true
                            color: Theme.primary
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "个模型 · 每周上新"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                        }
                    }
                }
            }

            // ---- 主 CTA: 「即将上线」占位 (不接 IAP / 支付 SDK) ----------
            AbstractButton {
                id: ctaButton
                Layout.fillWidth: true
                Layout.preferredHeight: Theme.bigButtonHeight
                onClicked: page.notify("订阅功能正在准备中, 上线后会在这里开放 —— 免费模型现在就能玩")
                scale: pressed ? 0.97 : 1.0
                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: ctaButton.pressed ? Theme.primaryPressed : Theme.primary
                }
                contentItem: Text {
                    text: "🌱 订阅即将上线"
                    color: "white"
                    font.pixelSize: Theme.fontButton
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // 次级 CTA: mailto 联系通道 (外链在家长门后, §14 验收清单)
            AbstractButton {
                id: mailButton
                Layout.fillWidth: true
                Layout.preferredHeight: Theme.touchTarget
                onClicked: Qt.openUrlExternally("mailto:" + page.contactMail
                                                + "?subject=" + encodeURIComponent("MagTile 订阅咨询"))
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: mailButton.pressed ? Theme.primarySoft : Theme.surface
                    border.color: Theme.primary
                    border.width: 1
                }
                contentItem: Text {
                    text: "✉ 有疑问或建议? 给我们写邮件"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.primary
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // ---- 我们的承诺 (透明条款预告, §11 / COMMERCIAL_PLAN §2-3) ---
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: promiseColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                ColumnLayout {
                    id: promiseColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: "我们的承诺"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.primary
                    }
                    Repeater {
                        model: [
                            "儿童界面永远不显示价格与付费入口, 付费只由家长在这里决定",
                            "无倒计时、无「即将涨价」、无预勾选加购; 订阅前不索取任何个人信息",
                            "正式上线时条款透明: 自动续费规则、一步取消路径、年度档 7 天无理由退款",
                            "会提供「恢复购买」按钮; 更喜欢买断的家庭也会有一次性内容包可选"
                        ]
                        delegate: RowLayout {
                            required property string modelData
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                Layout.alignment: Qt.AlignTop
                                text: "✓"
                                font.pixelSize: Theme.fontSmall
                                font.bold: true
                                color: Theme.success
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData
                                font.pixelSize: Theme.fontSmall
                                color: Theme.textSecondary
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: "本页只在家长验证之后可见; 这里的一切都不会出现在孩子的界面里。"
                font.pixelSize: Theme.fontSmall
                color: Theme.textSecondary
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }
}
