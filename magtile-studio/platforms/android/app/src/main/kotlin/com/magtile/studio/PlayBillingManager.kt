package com.magtile.studio

import android.app.Activity
import android.content.Context
import android.util.Log
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Google Play Billing 接线 (V1 清单 §2 B2, COMMERCIAL_PLAN §2.2/§4.4)。
 *
 * 角色分工 (与桌面同一抽象缝, 界面/免费层锁零感知商店 SDK):
 *   - 本类持有 Play Billing Library (连接 / 商品查询 / 购买流 / 恢复 /
 *     回执确认), 是 Android 端唯一接触商店 SDK 的地方;
 *   - 购买或恢复成功后经既有 JNI `MagTileNative.setSubscriptionActive`
 *     写 `progress/subscription_settings` 契约键 (`subscription_active` /
 *     `subscription_product_id`) —— 与桌面 FakeBillingClient / Qt
 *     BillingBackend **同键同口径**, 免费层锁 (`billing::isContentUnlocked`
 *     / 详情弹窗订阅锁) 零改动即感知;
 *   - 原生 C++ `billing::StoreBillingClient` 保留为跨商店接口缝,
 *     在 Android 不参与购买链路 (见 src/billing/store_billing_client.cpp)。
 *
 * 商品 id 三端统一 (store_billing_client.hpp 注释 / COMMERCIAL_PLAN §3.1,
 * Play Console 后台须配置同名订阅商品): sub_monthly / sub_yearly /
 * sub_family_yearly。价格与本地化文案以 Play 后台为准, 经
 * [queryProducts] 下发, 本类不内置任何价格文本 (儿童侧零价格红线 §11:
 * 价格只允许出现在家长门后的订阅页)。
 *
 * Debug / Release 分流 (BuildConfig.DEBUG 编译期常量):
 *   - **Debug**: 本类全部入口温和短路 (同步不跑 / 购买恢复回
 *     UNAVAILABLE) —— QA 走既有「模拟已订阅」开关 (家长门后年龄段
 *     对话框, 与桌面 FakeBillingClient::devSetSubscribed 同角色),
 *     零真实扣费, 两条链路互不干扰;
 *   - **Release**: 走真实 Play Billing。沙盒验收 (清单 §2 B3) 用
 *     Play Console 内部测试轨 + 许可测试账号, 见
 *     platforms/android/README.md「订阅与计费」小节。
 *
 * 启动静默恢复 ([syncOnAppStart], MagTileApplication 调起): 进程启动即
 * 向 Play 账户查询有效订阅 (`queryPurchasesAsync(SUBS)`, 商店回执是
 * 权威来源) —— 有则补确认回执并落盘契约键 (换机 / 重装 / 他端购买
 * 自动生效), 明确没有则清掉本地过期凭证; **查询失败 (无网/商店不可用)
 * 不动本地凭证** —— settings 契约键即离线宽限期本地凭证
 * (COMMERCIAL_PLAN §4.4), 无网启动读它保持解锁。
 *
 * 进度存档时序: 契约键落在 SQLite settings 表, 存档由 MainActivity
 * 启动链路异步打开 (首启含资产解包) —— Play 应答先于开档时
 * `setSubscriptionActive` 返回 false, 本类以短退避重试直到落盘
 * (幂等写, 见 [persistEntitlement]); 重试耗尽只记 logcat, 下次启动
 * 静默恢复兜底 (温和降级, 不弹「失败」)。
 *
 * 消费方: 家长门后的订阅页 SubscriptionActivity (三档档位卡经
 * [queryProducts] 取价 / 主 CTA 经 [purchase] 调起收银台 / 恢复
 * 购买按钮经 [restore], 对齐桌面 Qt SubscriptionPage); 启动静默
 * 恢复继续兜底保证已购用户权益不丢 (换机 / 重装 / 他端购买)。
 */
object PlayBillingManager : PurchasesUpdatedListener {

    /** 购买 / 恢复结果 (与 C++ billing::PurchaseOutcome 同语汇, 界面
     *  据此给温和提示, 永不弹「失败」)。PENDING (待付款) 归入
     *  UNAVAILABLE: 权益在 Play 侧完成收款后由下次启动静默恢复补发。 */
    enum class Outcome { PURCHASED, RESTORED, NOTHING_TO_RESTORE, CANCELLED, UNAVAILABLE }

    /** 订阅商品 id (三端统一约定, Play Console 后台同名配置)。 */
    val PRODUCT_IDS = listOf("sub_monthly", "sub_yearly", "sub_family_yearly")

    /** Release 才走真实 Play Billing; Debug 保留「模拟已订阅」QA 链路。 */
    val enabled: Boolean get() = !BuildConfig.DEBUG

    private const val TAG = "MagTileBilling"
    private const val MAX_PERSIST_ATTEMPTS = 8
    private const val PERSIST_RETRY_SECONDS = 2L

    /** 落盘重试与回调派发线程 (JNI 写档是 SQLite IO, 不占 binder 线程)。 */
    private val worker = Executors.newSingleThreadScheduledExecutor { r ->
        Thread(r, "magtile-billing")
    }

    private val lock = Any()
    private var client: BillingClient? = null
    private var connecting = false
    /** 连接就绪前排队的操作 (就绪后按序执行; 连接失败以 null 派发)。 */
    private val pendingActions = mutableListOf<(BillingClient?) -> Unit>()
    /** 进行中的购买流回调 (launchBillingFlow -> onPurchasesUpdated)。 */
    @Volatile private var purchaseCallback: ((Outcome, String) -> Unit)? = null

    // ---- 启动静默恢复 (MagTileApplication.onCreate 调起) ----------------

    /** 进程启动时向 Play 账户静默同步订阅权益 (商店回执是权威来源);
     *  Debug 构建温和短路 —— QA 走「模拟已订阅」开关。 */
    fun syncOnAppStart(context: Context) {
        if (!enabled) {
            Log.i(TAG, "Debug 构建: 跳过 Play Billing 启动同步 (QA 走模拟订阅开关)")
            return
        }
        withClient(context.applicationContext) { ready ->
            if (ready == null) {
                Log.w(TAG, "Play Billing 连接失败, 保留本地订阅凭证 (离线宽限期)")
            } else {
                refreshEntitlement(ready, onOutcome = null)
            }
        }
    }

    // ---- 订阅页数据源与购买 / 恢复入口 (家长门后, §11) -------------------

    /**
     * 可购的订阅档位 (含 Play 后台本地化价格文案): 成功回调
     * ProductDetails 列表 (仅三端统一 id), 商店不可用回调 null ——
     * 界面据此退回「即将上线」占位 (与桌面 queryProducts 空表同语义)。
     * 回调在 billing 工作线程, 界面侧自行切主线程。
     */
    fun queryProducts(context: Context, onResult: (List<ProductDetails>?) -> Unit) {
        if (!enabled) {
            onResult(null)
            return
        }
        withClient(context.applicationContext) { ready ->
            if (ready == null) {
                onResult(null)
                return@withClient
            }
            val params = QueryProductDetailsParams.newBuilder()
                .setProductList(PRODUCT_IDS.map { id ->
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(id)
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build()
                })
                .build()
            ready.queryProductDetailsAsync(params) { result, details ->
                if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                    onResult(details)
                } else {
                    Log.w(TAG, "商品查询失败: ${describe(result)}")
                    onResult(null)
                }
            }
        }
    }

    /**
     * 发起订阅购买流 (Play 收银台弹层): 结果经 [onPurchasesUpdated]
     * 回调 —— PURCHASED = 回执已确认且契约键已提交落盘 (免费层锁
     * 生效), CANCELLED = 用户主动收起 (中性结果), 其余 UNAVAILABLE。
     * 未知商品 id 直接 UNAVAILABLE (与 FakeBillingClient 同口径)。
     */
    fun purchase(activity: Activity, productId: String, onOutcome: (Outcome, String) -> Unit) {
        if (!enabled || productId !in PRODUCT_IDS) {
            onOutcome(Outcome.UNAVAILABLE, "")
            return
        }
        withClient(activity.applicationContext) { ready ->
            if (ready == null) {
                onOutcome(Outcome.UNAVAILABLE, "")
                return@withClient
            }
            val params = QueryProductDetailsParams.newBuilder()
                .setProductList(listOf(
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(productId)
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build()))
                .build()
            ready.queryProductDetailsAsync(params) { result, details ->
                val product = details.firstOrNull { it.productId == productId }
                val offerToken =
                    product?.subscriptionOfferDetails?.firstOrNull()?.offerToken
                if (result.responseCode != BillingClient.BillingResponseCode.OK ||
                    product == null || offerToken == null) {
                    Log.w(TAG, "购买前商品解析失败 ($productId): ${describe(result)}")
                    onOutcome(Outcome.UNAVAILABLE, "")
                    return@queryProductDetailsAsync
                }
                purchaseCallback = onOutcome
                val flowParams = BillingFlowParams.newBuilder()
                    .setProductDetailsParamsList(listOf(
                        BillingFlowParams.ProductDetailsParams.newBuilder()
                            .setProductDetails(product)
                            .setOfferToken(offerToken)
                            .build()))
                    .build()
                // 收银台弹层必须在主线程调起 (billing 回调在 binder 线程)
                activity.runOnUiThread {
                    val launch = ready.launchBillingFlow(activity, flowParams)
                    if (launch.responseCode != BillingClient.BillingResponseCode.OK) {
                        Log.w(TAG, "购买流调起失败: ${describe(launch)}")
                        purchaseCallback = null
                        onOutcome(Outcome.UNAVAILABLE, "")
                    }
                }
            }
        }
    }

    /**
     * 恢复购买 (换机 / 重装场景, COMMERCIAL_PLAN §2.2 承诺项): 从 Play
     * 账户回执恢复 —— RESTORED = 找到有效订阅且契约键已提交落盘,
     * NOTHING_TO_RESTORE = 账户下无有效订阅 (中性结果), UNAVAILABLE =
     * 商店不可用 (本地凭证不动, 离线宽限期)。
     */
    fun restore(context: Context, onOutcome: (Outcome, String) -> Unit) {
        if (!enabled) {
            onOutcome(Outcome.UNAVAILABLE, "")
            return
        }
        withClient(context.applicationContext) { ready ->
            if (ready == null) {
                onOutcome(Outcome.UNAVAILABLE, "")
            } else {
                refreshEntitlement(ready, onOutcome)
            }
        }
    }

    // ---- 购买流结果 (PurchasesUpdatedListener) ---------------------------

    override fun onPurchasesUpdated(result: BillingResult, purchases: List<Purchase>?) {
        val callback = purchaseCallback
        purchaseCallback = null
        when (result.responseCode) {
            BillingClient.BillingResponseCode.OK -> {
                val active = purchases.orEmpty().firstOrNull { purchased(it) }
                if (active != null) {
                    val productId = knownProductId(active)
                    acknowledgeIfNeeded(active)
                    persistEntitlement(active = true, productId = productId)
                    callback?.invoke(Outcome.PURCHASED, productId)
                } else {
                    // 待付款 (PENDING) 等非终态: 权益由 Play 完成收款后的
                    // 下次启动静默恢复补发, 本次按不可用温和收场
                    Log.i(TAG, "购买流返回但无已完成购买 (可能为待付款)")
                    callback?.invoke(Outcome.UNAVAILABLE, "")
                }
            }
            BillingClient.BillingResponseCode.USER_CANCELED ->
                callback?.invoke(Outcome.CANCELLED, "")
            else -> {
                Log.w(TAG, "购买流失败: ${describe(result)}")
                callback?.invoke(Outcome.UNAVAILABLE, "")
            }
        }
    }

    // ---- Play 账户权益同步 (启动静默恢复 / 恢复购买共用) ------------------

    /**
     * 查询 Play 账户下的有效订阅并同步契约键:
     *   - 有已完成购买: 补确认回执 (acknowledge, 3 天内未确认 Play 会
     *     自动退款) + 落盘 active=true;
     *   - 明确没有 (查询成功且空): 清掉本地凭证 (订阅过期 / 退款 /
     *     换账号后不再误放行 —— 宁可锁);
     *   - 查询失败: 本地凭证不动 (离线宽限期, §4.4)。
     */
    private fun refreshEntitlement(ready: BillingClient, onOutcome: ((Outcome, String) -> Unit)?) {
        val params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.SUBS)
            .build()
        ready.queryPurchasesAsync(params) { result, purchases ->
            if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                Log.w(TAG, "订阅查询失败, 保留本地凭证: ${describe(result)}")
                onOutcome?.invoke(Outcome.UNAVAILABLE, "")
                return@queryPurchasesAsync
            }
            val active = purchases.firstOrNull { purchased(it) }
            if (active != null) {
                val productId = knownProductId(active)
                acknowledgeIfNeeded(active)
                persistEntitlement(active = true, productId = productId)
                onOutcome?.invoke(Outcome.RESTORED, productId)
            } else {
                // 明确无有效订阅: 只在本地仍标记已订阅时清理 (避免
                // 首启存档未开时空转重试); 存档未开读到 false 同样跳过
                val locallyActive = try {
                    MagTileNative.subscriptionActive()
                } catch (t: Throwable) {
                    false
                }
                if (locallyActive) {
                    persistEntitlement(active = false, productId = "")
                }
                onOutcome?.invoke(Outcome.NOTHING_TO_RESTORE, "")
            }
        }
    }

    /** 已完成购买且含三端统一商品 id (未知 id 的历史商品不放行)。 */
    private fun purchased(purchase: Purchase): Boolean =
        purchase.purchaseState == Purchase.PurchaseState.PURCHASED &&
            purchase.products.any { it in PRODUCT_IDS }

    private fun knownProductId(purchase: Purchase): String =
        purchase.products.firstOrNull { it in PRODUCT_IDS } ?: purchase.products.first()

    /** 确认回执 (幂等; 未确认的购买 Play 会在 3 天后自动退款): 失败
     *  只记 logcat, 下次启动静默恢复会再试。 */
    private fun acknowledgeIfNeeded(purchase: Purchase) {
        if (purchase.isAcknowledged) return
        val ready = synchronized(lock) { client } ?: return
        val params = AcknowledgePurchaseParams.newBuilder()
            .setPurchaseToken(purchase.purchaseToken)
            .build()
        ready.acknowledgePurchase(params) { result ->
            if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                Log.w(TAG, "回执确认失败 (下次启动重试): ${describe(result)}")
            }
        }
    }

    // ---- 契约键落盘 (与 FakeBilling / 桌面同键, 免费层锁读取口径) --------

    /**
     * 写 `progress/subscription_settings` 契约键 (幂等)。进度存档由
     * MainActivity 启动链路异步打开 —— 未就绪时 JNI 返回 false, 以
     * 2 秒退避重试至多 [MAX_PERSIST_ATTEMPTS] 次; 耗尽只记 logcat
     * (下次启动静默恢复兜底), 绝不在未落盘时翻转界面解锁状态。
     */
    private fun persistEntitlement(active: Boolean, productId: String, attempt: Int = 0) {
        worker.execute {
            val persisted = try {
                MagTileNative.setSubscriptionActive(active, productId)
            } catch (t: Throwable) {
                Log.e(TAG, "订阅状态落盘异常", t)
                false
            }
            when {
                persisted ->
                    Log.i(TAG, "订阅状态已落盘: active=$active product=$productId")
                attempt + 1 < MAX_PERSIST_ATTEMPTS ->
                    worker.schedule(
                        { persistEntitlement(active, productId, attempt + 1) },
                        PERSIST_RETRY_SECONDS, TimeUnit.SECONDS)
                else ->
                    Log.w(TAG, "订阅状态落盘重试耗尽 (下次启动静默恢复兜底)")
            }
        }
    }

    // ---- 连接管理 (惰性单连接, 断线后按需重连) ---------------------------

    /** 就绪后执行 action (未就绪先排队; 连接失败以 null 派发一次)。 */
    private fun withClient(context: Context, action: (BillingClient?) -> Unit) {
        synchronized(lock) {
            val existing = client
            if (existing != null && existing.isReady) {
                action(existing)
                return
            }
            pendingActions.add(action)
            if (connecting) return
            connecting = true
            val built = client ?: BillingClient.newBuilder(context)
                .setListener(this)
                .enablePendingPurchases()
                .build()
                .also { client = it }
            built.startConnection(object : BillingClientStateListener {
                override fun onBillingSetupFinished(result: BillingResult) {
                    val ok = result.responseCode == BillingClient.BillingResponseCode.OK
                    if (!ok) Log.w(TAG, "Play Billing 连接失败: ${describe(result)}")
                    drainPending(if (ok) built else null)
                }

                override fun onBillingServiceDisconnected() {
                    // 下一次 withClient 按需重连 (isReady 已为 false)
                    Log.i(TAG, "Play Billing 服务断开, 后续操作将重连")
                    drainPending(null)
                }
            })
        }
    }

    private fun drainPending(ready: BillingClient?) {
        val actions: List<(BillingClient?) -> Unit>
        synchronized(lock) {
            connecting = false
            actions = pendingActions.toList()
            pendingActions.clear()
        }
        for (action in actions) {
            try {
                action(ready)
            } catch (t: Throwable) {
                Log.e(TAG, "billing 操作执行失败", t)
            }
        }
    }

    private fun describe(result: BillingResult): String =
        "code=${result.responseCode} msg=${result.debugMessage}"
}
