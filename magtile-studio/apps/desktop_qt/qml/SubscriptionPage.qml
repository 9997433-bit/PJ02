import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 订阅页 (QT-5, UI_UX_SPEC.md §11): 必须在家长门之后才可见
// (由 Main.qml 路由与会话守卫保证)。给家长看的页面 = 信息完整、
// 无套路: 页首明示免费额度 (反套路即信任), 温和说明订阅解锁全库,
// 「免费 vs 全库」对比数字实时读模型目录 (studio.freeModelCount /
// studio.modelCount, 与 QA 红线工具同一「免费」标签口径)。
// 付费区走计费适配层 (billing 桥, COMMERCIAL_PLAN §2.2): 三卡档位
// 与主 CTA / 恢复购买只面向 BillingClient 抽象 —— 桌面开发档为
// FakeBillingClient (零真实扣费, 开发档另有「模拟已订阅」开关),
// 商店空实现档 (storeAvailable=false) 自动退回「即将上线」占位;
// 接真商店 SDK 时本页零改动 (Windows 商店/Google Play 接法见
// include/magtile/billing/store_billing_client.hpp)。
// 红线 (§11 禁止事项): 无倒计时、无「即将涨价」、无预勾选加购、
// 不索取任何个人信息; 全页不用红色与紧迫话术; 价格只出现在
// 本页 (家长门后), 儿童侧界面零价格信息。
// =============================================================
Page {
    id: page

    signal back()
    signal notify(string message)

    /// Main.qml 会话守卫: 会话失效时该页自动退回首页
    readonly property bool requiresParentSession: true

    /// 上线前替换为正式支持邮箱 (RFC 2606 保留域, 占位期不可达)
    readonly property string contactMail: "hello@magtile.example"

    /// 可购档位快照 (计费适配层, 档位表静态, 加载一次即可)
    readonly property var productList: billing.products()

    /// 选中的档位 id; 默认落在主推档 (年度, COMMERCIAL_PLAN §3.2) ——
    /// 是"默认高亮"不是"预勾选加购" (§11): 不选也不买, 无任何默认扣费
    property string selectedProductId: {
        for (var i = 0; i < productList.length; ++i) {
            if (productList[i].recommended) return productList[i].productId
        }
        return productList.length > 0 ? productList[0].productId : ""
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

            // ---- 订阅生效状态卡 (完成绿: 已拥有) ------------------------
            Rectangle {
                visible: billing.subscriptionActive
                Layout.fillWidth: true
                implicitHeight: activeColumn.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.successSoft

                ColumnLayout {
                    id: activeColumn
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: 8

                    Text {
                        text: billing.activePlanName !== ""
                              ? "✓ 订阅生效中 · " + billing.activePlanName
                              : "✓ 订阅生效中"
                        font.pixelSize: Theme.fontButton
                        font.bold: true
                        color: Theme.success
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "全库 " + studio.modelCount + " 个模型已解锁, 每周上新自动包含。"
                              + "取消与退款入口将随正式商店版提供 (一步取消, 不设挽留关卡)。"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ---- 三卡档位 (计费适配层, 家长门后才可能看到价格) -----------
            // 点卡只是选择, 购买必须再按下方大按钮 (无预勾选加购语义)
            Repeater {
                model: billing.subscriptionActive ? [] : page.productList
                delegate: AbstractButton {
                    id: productCard
                    required property var modelData
                    readonly property bool selected: page.selectedProductId === modelData.productId
                    Layout.fillWidth: true
                    implicitHeight: productRow.implicitHeight + 2 * Theme.spacing
                    onClicked: page.selectedProductId = modelData.productId

                    background: Rectangle {
                        radius: Theme.radiusCard
                        color: productCard.selected ? Theme.primarySoft : Theme.surface
                        border.color: productCard.selected ? Theme.primary : Theme.cardBorder
                        border.width: productCard.selected ? 2 : 1
                    }
                    contentItem: RowLayout {
                        id: productRow
                        spacing: Theme.spacing

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.margins: Theme.spacing
                            spacing: 4
                            RowLayout {
                                spacing: 8
                                Text {
                                    text: productCard.modelData.name
                                    font.pixelSize: Theme.fontBody
                                    font.bold: true
                                    color: Theme.textPrimary
                                }
                                // 主推徽标 (中性推荐, 非稀缺/催促话术);
                                // 字号走 Theme 令牌, 徽标随字号三档缩放不裁字 (§4.7)
                                Rectangle {
                                    visible: productCard.modelData.recommended
                                    radius: Theme.radiusButton
                                    height: recommendTag.implicitHeight + 8
                                    width: recommendTag.implicitWidth + 16
                                    color: Theme.primary
                                    Text {
                                        id: recommendTag
                                        anchors.centerIn: parent
                                        text: "多数家庭的选择"
                                        font.pixelSize: Theme.fontSmall
                                        font.bold: true
                                        color: "white"
                                    }
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: productCard.modelData.blurb
                                font.pixelSize: Theme.fontSmall
                                color: Theme.textSecondary
                                wrapMode: Text.WordWrap
                            }
                        }
                        Text {
                            Layout.rightMargin: Theme.spacing
                            text: productCard.modelData.priceText
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: productCard.selected ? Theme.primary : Theme.textPrimary
                        }
                    }
                }
            }

            // ---- 主 CTA: 经计费适配层发起购买 ---------------------------
            // 商店可用 (桌面开发档 = 假计费) 时购买选中档位; 空实现档
            // (storeAvailable=false) 保持「即将上线」温和占位
            AbstractButton {
                id: ctaButton
                visible: !billing.subscriptionActive
                Layout.fillWidth: true
                Layout.preferredHeight: Theme.bigButtonHeight
                onClicked: {
                    if (billing.storeAvailable && page.selectedProductId !== "") {
                        page.notify(billing.purchase(page.selectedProductId))
                    } else {
                        page.notify("订阅功能正在准备中, 上线后会在这里开放 —— 免费模型现在就能玩")
                    }
                }
                scale: pressed ? 0.97 : 1.0
                Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: ctaButton.pressed ? Theme.primaryPressed : Theme.primary
                }
                contentItem: Text {
                    text: billing.storeAvailable && page.selectedProductId !== ""
                          ? "🌱 开通订阅 (开发模拟, 不产生扣费)"
                          : "🌱 订阅即将上线"
                    color: "white"
                    font.pixelSize: Theme.fontButton
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // 恢复购买 (换机/重装场景; 空实现档给"随正式版开放"温和提示)
            AbstractButton {
                id: restoreButton
                visible: !billing.subscriptionActive
                Layout.fillWidth: true
                Layout.preferredHeight: Theme.touchTarget
                onClicked: page.notify(billing.restore())
                background: Rectangle {
                    radius: Theme.radiusButton
                    color: restoreButton.pressed ? Theme.primarySoft : Theme.surface
                    border.color: Theme.primary
                    border.width: 1
                }
                contentItem: Text {
                    text: "↺ 恢复购买"
                    font.pixelSize: Theme.fontBody
                    font.bold: true
                    color: Theme.primary
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // ---- 开发档控件: 「模拟已订阅」开关 (Debug / --dev-billing) --
            // 正式商店档编译期恒不可见 (billing.devControlsEnabled 恒 false)
            Rectangle {
                visible: billing.devControlsEnabled
                Layout.fillWidth: true
                implicitHeight: devRow.implicitHeight + 2 * Theme.spacing
                radius: Theme.radiusCard
                color: Theme.surface
                border.color: Theme.cardBorder
                border.width: 1

                RowLayout {
                    id: devRow
                    anchors.centerIn: parent
                    width: parent.width - 2 * Theme.spacing
                    spacing: Theme.spacing

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "开发档: 模拟已订阅"
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            color: Theme.textPrimary
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "假计费适配层, 不接商店不扣费; 关掉后可用「恢复购买」演练恢复流程。"
                            font.pixelSize: Theme.fontSmall
                            color: Theme.textSecondary
                            wrapMode: Text.WordWrap
                        }
                    }
                    Switch {
                        checked: billing.subscriptionActive
                        onToggled: billing.devSetSubscribed(checked)
                    }
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
