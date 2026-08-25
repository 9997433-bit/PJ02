pragma Singleton
import QtQuick

// =============================================================
// 设计令牌单例 —— docs/UI_UX_SPEC.md §1.2 的唯一 QML 落点。
// 颜色为色盲安全组合 (蓝/琥珀/绿, §4.7), 状态从不单靠颜色表达。
// =============================================================
QtObject {
    // ---- 颜色 ----------------------------------------------------
    readonly property color primary: "#2E7DD1"        // 磁力蓝 (主操作)
    readonly property color primaryPressed: "#1F5FA8" // 按下态加深
    readonly property color primarySoft: "#E3EEFA"    // 主色浅底 (徽标/条带)
    readonly property color success: "#2C9F6B"        // 完成绿
    readonly property color successSoft: "#E0F2E9"
    readonly property color warning: "#E8A13C"        // 提示琥珀 (不用红色表达"错误")
    readonly property color warningSoft: "#FBF0DC"
    readonly property color surface: "#FFFFFF"        // 亮主题卡片面
    readonly property color surfaceAlt: "#F2F6FB"     // 页面底色 (低饱和蓝灰)
    readonly property color surfaceDark: "#1C2230"    // 暗主题面 (预留)
    readonly property color textPrimary: "#243244"
    readonly property color textSecondary: "#5B6B7F"
    readonly property color cardBorder: "#E1E8F2"

    // 磁力片实物常见 8 色 (渲染层为半透明材质, UI 侧用作主题条带)
    readonly property var tileColors: [
        "#E8604C", "#F5A623", "#F8D648", "#7BC96F",
        "#4AA8D8", "#2E7DD1", "#9B6DD6", "#F080B5"
    ]

    // ---- 圆角 / 阴影 / 间距 ---------------------------------------
    readonly property int radiusCard: 16
    readonly property int radiusButton: 24            // 胶囊按钮
    readonly property int radiusSheet: 20
    readonly property int spacing: 16
    readonly property int spacingLarge: 24

    // ---- 触控目标 (§4.1 硬性规范) ----------------------------------
    readonly property int touchTarget: 48             // 儿童可点元素最小边
    readonly property int bigButtonHeight: 64         // 主操作按钮
    readonly property int parentGateSize: 32          // 家长区入口 (全应用唯一例外)

    // ---- 字号 (7-9 岁标准模式基准 18, §2) --------------------------
    readonly property int fontSmall: 14
    readonly property int fontBody: 18
    readonly property int fontButton: 22
    readonly property int fontTitle: 28
    readonly property int fontHero: 44

    // ---- 动效 (标准 200ms ease-out) --------------------------------
    readonly property int animMs: 200

    /// 主题标签 → 卡片条带色 (稳定散列, 同主题永远同色)
    function themeColor(theme) {
        var hash = 0
        for (var i = 0; i < theme.length; ++i)
            hash = (hash * 31 + theme.charCodeAt(i)) % 2147483647
        return tileColors[hash % tileColors.length]
    }

    /// 难度 1~5 → 星串 "★★☆☆☆" (图形+数量双编码, 不依赖颜色)
    function difficultyStars(level) {
        var s = ""
        for (var i = 1; i <= 5; ++i)
            s += i <= level ? "★" : "☆"
        return s
    }
}
