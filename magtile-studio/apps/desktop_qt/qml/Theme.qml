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
    readonly property color textDim: "#B9C6D6"         // 未点亮元素 (里程碑星等)
    readonly property color cardBorder: "#E1E8F2"
    readonly property color viewportBg: "#E6ECF2"      // 3D 视口底 (与场景清屏色同族)
    readonly property color overlayLight: "#CCFFFFFF"  // 视口浮层提示底 (半透明白)

    // 磁力片实物常见 8 色 (渲染层为半透明材质, UI 侧用作主题条带)
    readonly property var tileColors: [
        "#E8604C", "#F5A623", "#F8D648", "#7BC96F",
        "#4AA8D8", "#2E7DD1", "#9B6DD6", "#F080B5"
    ]

    // ---- 圆角 / 阴影 / 间距 ---------------------------------------
    readonly property int radiusCard: 16
    readonly property int radiusButton: 24            // 胶囊按钮
    readonly property int radiusSheet: 20
    readonly property int spacingSmall: 8
    readonly property int spacing: 16
    readonly property int spacingLarge: 24
    readonly property int headerHeight: 72            // 全页统一页眉高

    // ---- 触控目标 (§4.1 硬性规范) ----------------------------------
    readonly property int touchTarget: 48             // 儿童可点元素最小边
    readonly property int bigButtonHeight: 64         // 主操作按钮
    readonly property int parentGateSize: 32          // 家长区入口 (全应用唯一例外)

    // ---- 无障碍 (§4.7; Main.qml 启动时绑定到 appSettings 后端桥) ----
    property real fontScale: 1.0        // 字号三档: 1.0 / 1.25 / 1.5
    property bool reduceMotion: false   // 减少动效: 动效时长归零

    // ---- 字号 (7-9 岁标准模式基准 18, §2; 随 fontScale 三档缩放) ----
    readonly property int fontSmall: Math.round(14 * fontScale)
    readonly property int fontBody: Math.round(18 * fontScale)
    readonly property int fontButton: Math.round(22 * fontScale)
    readonly property int fontTitle: Math.round(28 * fontScale)
    readonly property int fontHero: Math.round(44 * fontScale)

    // ---- 动效 (标准 200ms ease-out; 减少动效时归零) ------------------
    readonly property int animMs: reduceMotion ? 0 : 200

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
