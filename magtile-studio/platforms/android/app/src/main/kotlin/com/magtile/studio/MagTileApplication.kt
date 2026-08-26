package com.magtile.studio

import android.app.Application

/**
 * 进程级入口 (AndroidManifest android:name 注册): 目前唯一职责是
 * 调起 Play Billing 启动静默恢复 (Release 档; Debug 档在
 * PlayBillingManager 内温和短路, QA 走「模拟已订阅」开关) ——
 * 商店回执是权威来源, 换机 / 重装 / 他端购买的订阅在启动时自动
 * 写回 progress/subscription_settings 契约键 (COMMERCIAL_PLAN §4.4)。
 *
 * 刻意放在 Application 而非 MainActivity: 权益同步是进程级一次性
 * 动作, 与具体界面无关; 进度存档由 MainActivity 启动链路异步打开,
 * 时序差由 PlayBillingManager 的落盘退避重试吸收。
 */
class MagTileApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        PlayBillingManager.syncOnAppStart(this)
    }
}
