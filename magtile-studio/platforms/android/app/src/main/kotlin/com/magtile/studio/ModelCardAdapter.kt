package com.magtile.studio

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

/** 模型库卡片列表适配器: 中文名 + 英文名/主题 + 难度星 + 片数·步数。 */
class ModelCardAdapter(
    private val onCardClick: (ModelCard) -> Unit,
) : RecyclerView.Adapter<ModelCardAdapter.CardHolder>() {

    private val cards = mutableListOf<ModelCard>()

    fun submit(newCards: List<ModelCard>) {
        cards.clear()
        cards.addAll(newCards)
        @Suppress("NotifyDataSetChanged")  // 全量替换一次, 无增量更新场景
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CardHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_model_card, parent, false)
        return CardHolder(view)
    }

    override fun getItemCount(): Int = cards.size

    override fun onBindViewHolder(holder: CardHolder, position: Int) {
        holder.bind(cards[position])
    }

    inner class CardHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val name: TextView = itemView.findViewById(R.id.model_name)
        private val subtitle: TextView = itemView.findViewById(R.id.model_subtitle)
        private val difficulty: TextView = itemView.findViewById(R.id.model_difficulty)
        private val pieces: TextView = itemView.findViewById(R.id.model_pieces)

        fun bind(card: ModelCard) {
            name.text = card.name
            subtitle.text = listOf(card.theme, card.nameEn)
                .filter { it.isNotBlank() }
                .joinToString(" · ")
            difficulty.text = card.difficultyStars
            pieces.text = itemView.context.getString(
                R.string.card_pieces_steps, card.totalPieces, card.stepCount)
            itemView.setOnClickListener { onCardClick(card) }
        }
    }
}
