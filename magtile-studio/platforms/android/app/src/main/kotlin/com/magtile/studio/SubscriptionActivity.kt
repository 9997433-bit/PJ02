package com.magtile.studio

import android.app.Activity
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import com.android.billingclient.api.ProductDetails
import java.util.concurrent.Executors

/**
 * 订阅页 (UI_UX_SPEC.md §11, V1 清单 §2 B2 的 Android 订阅页 UI):
 * 家长门后的三档档位卡 + 主 CTA + 恢复购买, 信息结构与措辞对齐
 * 桌面 Qt SubscriptionPage。
 *
 * 家长门红线 (§11 / §12.2, 价格只出现在本页):
 *   - 入口在家长门后的年龄段对话框 (MainActivity, 与「隐私与数据」
 *     同位), 到达本页时家长会话必然有效;
 *   - 会话守卫与桌面 Main.qml 同策略: onCreate / onResume / 前台
 *     周期检查 core::ParentGate 会话, 15 分钟会话到期本页自动退场
 *     (finish) —— 价格页绝不停留在儿童面前;
 *   - 无倒计时、无「即将涨价」、无预勾选加购、不索取任何个人信息;
 *     全页不用红色与紧迫话术, 购买/恢复结果永不弹「失败」。
 *
 * 档位与价格 (COMMERCIAL_PLAN §3.1): 三端统一商品 id
 * (sub_monthly / sub_yearly / sub_family_yearly) 的中文名与一句话
 * 说明用本地表 (与桌面 FakeBillingClient / store_billing_client
 * 档位表同文案), 价格**不在本地写死** —— 经
 * [PlayBillingManager.queryProducts] 实时读 Play 后台本地化价格;
 * 查询不可用 (无网 / 商店没连上 / Debug 档温和短路) 退回「订阅功能
 * 正在准备中」温和占位卡, 绝不显示空价格卡 (与桌面 Qt / Windows
 * 商店档「商品表真查到才亮价格卡」同一口径)。
 *
 * 点卡只是选择 (默认高亮年度主推档, 非预勾选 —— 不选也不买),
 * 购买必须再按主 CTA ([PlayBillingManager.purchase] 调起 Play
 * 收银台); 「恢复购买」接 [PlayBillingManager.restore] (换机 /
 * 重装场景, COMMERCIAL_PLAN §2.2 承诺项)。购买 / 恢复成功由
 * PlayBillingManager 写 progress/subscription_settings 契约键,
 * 免费层锁零改动即感知; 本页界面状态以回调结果驱动。
 *
 * Debug 构建: PlayBillingManager 温和短路 (查询回 null → 占位卡),
 * 页内保留「模拟已订阅」开关 (与桌面订阅页 devControlsEnabled
 * 开发开关同角色同位置; BuildConfig.DEBUG 编译期常量, Release 档
 * 不可见亦不可达), QA 据此演练免费层锁的解锁与回锁, 零真实扣费。
 */
class SubscriptionActivity : Activity() {

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())

    private lateinit var freeNoticeView: TextView
    private lateinit var activeCard: View
    private lateinit var activeTitleView: TextView
    private lateinit var planListView: LinearLayout
    private lateinit var placeholderView: TextView
    private lateinit var ctaView: TextView
    private lateinit var restoreView: TextView
    private lateinit var devSwitch: Switch

    /** 已渲染的档位卡 (商品 id -> 卡片视图), 选中态切换用。 */
    private val planViews = LinkedHashMap<String, View>()

    /** 订阅是否生效 (界面口径; 初值经 JNI 读契约键, 之后由购买/恢复/
     *  模拟开关的回调结果驱动 —— 与免费层锁同一判定源)。 */
    private var subscriptionActive = false
    /** 生效中的档位 id (状态卡展示档位中文名用)。 */
    private var activeProductId = ""
    /** 商品表是否真查到 (查到才亮价格卡与「开通订阅」CTA)。 */
    private var productsAvailable = false
    /** 选中的档位 id (默认年度主推档; 只是选择, 不是预勾选购买)。 */
    private var selectedProductId = ""
    /** 模拟开关程序性回写时抑制监听器 (防递归触发)。 */
    private var updatingDevSwitch = false

    /** 会话守卫心跳: 家长会话到期本页自动退场 (儿童侧零价格红线,
     *  与桌面 Main.qml requiresParentSession 守卫同角色)。 */
    private val sessionGuard = object : Runnable {
        override fun run() {
            if (!MagTileNative.parentGateSessionActive()) {
                finish()
                return
            }
            handler.postDelayed(this, SESSION_CHECK_INTERVAL_MS)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 纵深防御: 本页只能从家长门后进入 (进程重建等路径下会话
        // 失效时直接退场, 不渲染任何价格信息)
        if (!MagTileNative.parentGateSessionActive()) {
            finish()
            return
        }
        setContentView(R.layout.activity_subscription)

        freeNoticeView = findViewById(R.id.subscription_free_notice)
        activeCard = findViewById(R.id.subscription_active_card)
        activeTitleView = findViewById(R.id.subscription_active_title)
        planListView = findViewById(R.id.subscription_plan_list)
        placeholderView = findViewById(R.id.subscription_placeholder)
        ctaView = findViewById(R.id.subscription_cta)
        restoreView = findViewById(R.id.subscription_restore)
        devSwitch = findViewById(R.id.subscription_dev_switch)

        findViewById<View>(R.id.subscription_back).setOnClickListener { finish() }
        ctaView.setOnClickListener { onCtaClicked() }
        restoreView.setOnClickListener { onRestoreClicked() }

        // 页首免费额度明示 (§11 反套路即信任): 免费层模型数由模型库
        // 侧带入 (与桌面 studio.freeModelCount 同一「免费」标签口径),
        // 尚未加载完时退回不带数字的版本
        val freeCount = intent.getIntExtra(EXTRA_FREE_MODEL_COUNT, 0)
        freeNoticeView.text = if (freeCount > 0) {
            getString(R.string.subscription_free_notice, freeCount)
        } else {
            getString(R.string.subscription_free_notice_no_count)
        }

        if (BuildConfig.DEBUG) {
            // 「模拟已订阅」开关 (仅 Debug; 与桌面订阅页 devControls
            // 同位置策略 —— 开发控件就住在订阅页里)
            findViewById<View>(R.id.subscription_dev_row).visibility = View.VISIBLE
            devSwitch.setOnCheckedChangeListener { _, checked ->
                if (!updatingDevSwitch) toggleDevBilling(checked)
            }
        }

        applyState()
        loadSubscriptionState()
        queryProducts()
    }

    override fun onResume() {
        super.onResume()
        handler.post(sessionGuard)
    }

    override fun onPause() {
        super.onPause()
        handler.removeCallbacks(sessionGuard)
    }

    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacksAndMessages(null)
        backgroundExecutor.shutdown()
    }

    // ---- 订阅状态 (契约键读取 + 回调结果驱动) --------------------------

    /** 启动时读一次契约键 (SQLite IO 放工作线程); 之后的状态翻转由
     *  购买/恢复/模拟开关的回调结果驱动, 不反复轮询存档。 */
    private fun loadSubscriptionState() {
        backgroundExecutor.execute {
            val active = try {
                MagTileNative.subscriptionActive()
            } catch (t: Throwable) {
                false
            }
            val productId = if (active) {
                try {
                    MagTileNative.subscriptionProductId()
                } catch (t: Throwable) {
                    ""
                }
            } else {
                ""
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                subscriptionActive = active
                activeProductId = productId
                applyState()
            }
        }
    }

    /** 按当前状态收放区块: 已订阅 = 状态卡, 未订阅 = 档位卡/占位 +
     *  CTA + 恢复购买 (与桌面 SubscriptionPage 同一显隐口径)。 */
    private fun applyState() {
        activeCard.visibility = if (subscriptionActive) View.VISIBLE else View.GONE
        activeTitleView.text = planDisplayName(activeProductId)
            ?.let { getString(R.string.subscription_active_title_plan, it) }
            ?: getString(R.string.subscription_active_title)
        planListView.visibility = if (subscriptionActive) View.GONE else View.VISIBLE
        placeholderView.visibility =
            if (!subscriptionActive && !productsAvailable) View.VISIBLE else View.GONE
        ctaView.visibility = if (subscriptionActive) View.GONE else View.VISIBLE
        restoreView.visibility = if (subscriptionActive) View.GONE else View.VISIBLE
        ctaView.text = getString(
            if (productsAvailable) R.string.subscription_cta
            else R.string.subscription_cta_coming)
        if (BuildConfig.DEBUG) {
            updatingDevSwitch = true
            devSwitch.isChecked = subscriptionActive
            updatingDevSwitch = false
        }
    }

    // ---- 档位卡 (价格实时读 Play 后台, 查询不可用退回温和占位) ---------

    private fun queryProducts() {
        // Debug 档 / 商店不可用时回 null -> renderPlans 落占位卡
        PlayBillingManager.queryProducts(this) { products ->
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                renderPlans(products)
            }
        }
    }

    /** 渲染三档档位卡: 只认三端统一 id 且真取到价格的商品 (缺价格的
     *  不亮卡), 按 PRODUCT_IDS 约定顺序排列; 一张都没有则占位。 */
    private fun renderPlans(products: List<ProductDetails>?) {
        planListView.removeAllViews()
        planViews.clear()
        val cards = products.orEmpty()
            .mapNotNull { toPlanCard(it) }
            .sortedBy { PlayBillingManager.PRODUCT_IDS.indexOf(it.productId) }
        productsAvailable = cards.isNotEmpty()
        if (productsAvailable) {
            // 默认高亮年度主推档 (COMMERCIAL_PLAN §3.2; 是"默认选中"
            // 不是"预勾选购买" —— 不按 CTA 不会发生任何扣费)
            selectedProductId = cards.firstOrNull { it.recommended }?.productId
                ?: cards.first().productId
            for (card in cards) {
                val view = layoutInflater.inflate(
                    R.layout.item_subscription_plan, planListView, false)
                view.findViewById<TextView>(R.id.plan_name).text = card.name
                view.findViewById<TextView>(R.id.plan_blurb).text = card.blurb
                view.findViewById<TextView>(R.id.plan_price).text = card.priceText
                view.findViewById<View>(R.id.plan_badge).visibility =
                    if (card.recommended) View.VISIBLE else View.GONE
                view.setOnClickListener {
                    selectedProductId = card.productId
                    updatePlanSelection()
                }
                (view.layoutParams as LinearLayout.LayoutParams).topMargin =
                    resources.getDimensionPixelSize(R.dimen.spacing_small)
                planListView.addView(view)
                planViews[card.productId] = view
            }
            updatePlanSelection()
        } else {
            placeholderView.setText(R.string.subscription_placeholder)
        }
        applyState()
    }

    /** 选中态: 主色浅底 + 加粗描边 (bg_plan_card state_selected),
     *  价格同步换主色 —— 选中从不单靠颜色表达, 描边加粗兜底 (§4.7)。 */
    private fun updatePlanSelection() {
        for ((productId, view) in planViews) {
            val selected = productId == selectedProductId
            view.isSelected = selected
            view.findViewById<TextView>(R.id.plan_price).setTextColor(
                getColor(if (selected) R.color.magtile_primary
                         else R.color.magtile_text_primary))
        }
    }

    /** ProductDetails -> 档位卡数据: 只认三端统一 id, 价格取首个
     *  订阅 offer 的常态计费阶段 (最后一个 pricing phase = 免费/
     *  折扣期之后的持续价格), 取不到价格不亮卡。 */
    private fun toPlanCard(details: ProductDetails): PlanCard? {
        val productId = details.productId
        if (productId !in PlayBillingManager.PRODUCT_IDS) return null
        val price = details.subscriptionOfferDetails
            ?.firstOrNull()
            ?.pricingPhases
            ?.pricingPhaseList
            ?.lastOrNull()
            ?.formattedPrice
            ?: return null
        val priceText = getString(
            if (productId == "sub_monthly") R.string.plan_price_per_month
            else R.string.plan_price_per_year,
            price)
        return when (productId) {
            "sub_monthly" -> PlanCard(
                productId, getString(R.string.plan_monthly_name),
                getString(R.string.plan_monthly_blurb), priceText, false)
            "sub_yearly" -> PlanCard(
                productId, getString(R.string.plan_yearly_name),
                getString(R.string.plan_yearly_blurb), priceText, true)
            else -> PlanCard(
                productId, getString(R.string.plan_family_name),
                getString(R.string.plan_family_blurb), priceText, false)
        }
    }

    private data class PlanCard(
        val productId: String,
        val name: String,
        val blurb: String,
        val priceText: String,
        val recommended: Boolean,
    )

    /** 三端统一档位 id 的中文展示名 (状态卡用); 未知 id 返回 null。 */
    private fun planDisplayName(productId: String): String? = when (productId) {
        "sub_monthly" -> getString(R.string.plan_monthly_name)
        "sub_yearly" -> getString(R.string.plan_yearly_name)
        "sub_family_yearly" -> getString(R.string.plan_family_name)
        else -> null
    }

    // ---- 购买 / 恢复 (结果永不弹「失败」, 与桌面 BillingBackend 同措辞) --

    private fun onCtaClicked() {
        if (!productsAvailable || selectedProductId.isEmpty()) {
            // 占位态: 温和说明即可 (与桌面 CTA 占位分支同文案)
            toast(getString(R.string.subscription_placeholder))
            return
        }
        PlayBillingManager.purchase(this, selectedProductId) { outcome, productId ->
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                when (outcome) {
                    PlayBillingManager.Outcome.PURCHASED -> {
                        subscriptionActive = true
                        activeProductId = productId
                        applyState()
                        setResult(RESULT_OK)
                        toast(getString(R.string.subscription_purchase_done))
                    }
                    PlayBillingManager.Outcome.CANCELLED ->
                        // 家长主动收起收银台: 中性结果, 不挽留不催促
                        toast(getString(R.string.subscription_purchase_cancelled))
                    else ->
                        toast(getString(R.string.subscription_purchase_unavailable))
                }
            }
        }
    }

    private fun onRestoreClicked() {
        if (!PlayBillingManager.enabled) {
            // Debug 档商店链路温和短路 (与桌面空实现档同措辞)
            toast(getString(R.string.subscription_restore_coming))
            return
        }
        PlayBillingManager.restore(this) { outcome, productId ->
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                when (outcome) {
                    PlayBillingManager.Outcome.RESTORED -> {
                        subscriptionActive = true
                        activeProductId = productId
                        applyState()
                        setResult(RESULT_OK)
                        toast(getString(R.string.subscription_restore_done))
                    }
                    PlayBillingManager.Outcome.NOTHING_TO_RESTORE ->
                        toast(getString(R.string.subscription_restore_nothing))
                    else ->
                        toast(getString(R.string.subscription_restore_unavailable))
                }
            }
        }
    }

    // ---- Debug 档「模拟已订阅」(与桌面 FakeBillingClient::devSetSubscribed
    //      同口径: 写同一契约键, 免费层锁跨端互认; 零真实扣费) -----------

    private fun toggleDevBilling(target: Boolean) {
        if (!BuildConfig.DEBUG) return  // Release 档误接线也改不了订阅状态
        backgroundExecutor.execute {
            val persisted = try {
                MagTileNative.setSubscriptionActive(
                    target, if (target) DEV_BILLING_PRODUCT_ID else "")
            } catch (t: Throwable) {
                Log.e(TAG, "模拟订阅切换未落盘", t)
                false
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (persisted) {
                    // 订阅权益以落盘为准: 落盘成功才翻转界面状态
                    subscriptionActive = target
                    activeProductId = if (target) DEV_BILLING_PRODUCT_ID else ""
                    setResult(RESULT_OK)
                }
                applyState()  // 未落盘时开关随 applyState 回弹到真实状态
                toast(getString(when {
                    !persisted -> R.string.dev_billing_soft_fail
                    target -> R.string.dev_billing_on_toast
                    else -> R.string.dev_billing_off_toast
                }))
            }
        }
    }

    private fun toast(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }

    companion object {
        private const val TAG = "MagTileSubscription"

        /** 免费层模型数 (页首免费额度明示用; 缺省 0 = 不带数字版本)。 */
        const val EXTRA_FREE_MODEL_COUNT = "free_model_count"

        /** 会话守卫心跳间隔: 秒级足够 (会话时长 15 分钟量级)。 */
        private const val SESSION_CHECK_INTERVAL_MS = 2000L

        /** Debug 档「模拟已订阅」写档的模拟档位: 年度主推 (与桌面
         *  FakeBillingClient::devSetSubscribed 同一档位约定)。 */
        private const val DEV_BILLING_PRODUCT_ID = "sub_yearly"
    }
}
