package com.magtile.studio

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

/**
 * 模型库卡片列表适配器: 缩略图 + 中文名 + 英文名/主题 + 扩展装角标 +
 * 难度星 + 片数·步数。缩略图经 ThumbnailLoader 异步流式读 APK assets,
 * 缺失/解码中显示占位底色。
 *
 * 分龄卡片密度三档 (UI_UX_SPEC.md §2, 与桌面 Qt LibraryPage 的
 * 2 列超大 / 3~4 列标准 / 4~5 列紧凑同一密度梯度, 手机屏以行高表达):
 *   [DENSITY_JUNIOR]   4-6 启蒙  超大卡片 item_model_card_junior
 *                      (大缩略图竖排 + 大字号 + 最少文字);
 *   [DENSITY_STANDARD] 7-9 标准  标准卡片 item_model_card;
 *   [DENSITY_COMPACT]  10+ 进阶  紧凑卡片 item_model_card_compact
 *                      (信息不减只降密度, 一屏可见更多模型)。
 */
class ModelCardAdapter(
    private val onCardClick: (ModelCard) -> Unit,
) : RecyclerView.Adapter<ModelCardAdapter.CardHolder>() {

    private val cards = mutableListOf<ModelCard>()

    /** 分龄卡片密度档 (三档之一); 切换时整表重建 (布局不可复用)。 */
    var density: Int = DENSITY_STANDARD
        set(value) {
            if (field == value) return
            field = value
            @Suppress("NotifyDataSetChanged")  // 布局整体切换, 无增量更新场景
            notifyDataSetChanged()
        }

    /** 减少动效 (§4.7): 卡片点按反馈由水波纹退为静态按压色。
     *  onCreate 时机赋值一次 (视图创建前), 无需触发重建。 */
    var reduceMotion: Boolean = false

    fun submit(newCards: List<ModelCard>) {
        cards.clear()
        cards.addAll(newCards)
        @Suppress("NotifyDataSetChanged")  // 全量替换一次, 无增量更新场景
        notifyDataSetChanged()
    }

    // 布局资源 id 即视图类型: 三种布局的视图 id 一一对应, 共用 CardHolder
    override fun getItemViewType(position: Int): Int = when (density) {
        DENSITY_JUNIOR -> R.layout.item_model_card_junior
        DENSITY_COMPACT -> R.layout.item_model_card_compact
        else -> R.layout.item_model_card
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CardHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(viewType, parent, false)
        if (reduceMotion) {
            view.setBackgroundResource(R.drawable.bg_model_card_calm)
        }
        return CardHolder(view)
    }

    override fun getItemCount(): Int = cards.size

    override fun onBindViewHolder(holder: CardHolder, position: Int) {
        holder.bind(cards[position])
    }

    inner class CardHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val thumbnail: ImageView = itemView.findViewById(R.id.model_thumbnail)
        private val name: TextView = itemView.findViewById(R.id.model_name)
        private val subtitle: TextView = itemView.findViewById(R.id.model_subtitle)
        private val expansionBadge: TextView =
            itemView.findViewById(R.id.model_expansion_badge)
        private val difficulty: TextView = itemView.findViewById(R.id.model_difficulty)
        private val pieces: TextView = itemView.findViewById(R.id.model_pieces)

        init {
            // 按占位背景的圆角轮廓裁剪位图 (XML 属性 clipToOutline 需 API 31+,
            // minSdk 26 故在代码里开启)
            thumbnail.clipToOutline = true
        }

        fun bind(card: ModelCard) {
            ThumbnailLoader.load(thumbnail, card.thumbnailAssetPath)
            name.text = card.name
            if (density == DENSITY_JUNIOR) {
                // 启蒙模式减文字量 (§2): 副标题只留主题, 不显示英文名
                // 与「需要扩展装」角标 (与 Qt bandJunior 卡片同一取舍)
                subtitle.text = card.theme
                subtitle.visibility =
                    if (card.theme.isBlank()) View.GONE else View.VISIBLE
                expansionBadge.visibility = View.GONE
            } else {
                subtitle.text = listOf(card.theme, card.nameEn)
                    .filter { it.isNotBlank() }
                    .joinToString(" · ")
                subtitle.visibility = View.VISIBLE
                // 「需要扩展装」角标: 口径与桌面 GL 一致 (bom_known && !core9_only)
                expansionBadge.visibility =
                    if (card.needsExpansion) View.VISIBLE else View.GONE
            }
            difficulty.text = card.difficultyStars
            pieces.text = itemView.context.getString(
                R.string.card_pieces_steps, card.totalPieces, card.stepCount)
            itemView.setOnClickListener { onCardClick(card) }
        }
    }

    companion object {
        /** 4-6 启蒙: 超大卡片。 */
        const val DENSITY_JUNIOR = 0
        /** 7-9 标准: 标准卡片 (默认档)。 */
        const val DENSITY_STANDARD = 1
        /** 10+ 进阶: 紧凑卡片。 */
        const val DENSITY_COMPACT = 2
    }
}
