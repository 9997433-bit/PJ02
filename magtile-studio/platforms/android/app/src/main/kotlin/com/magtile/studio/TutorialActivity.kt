package com.magtile.studio

import android.app.Activity
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

/**
 * 分步教程页 (3D 渲染接入前的文字分步浏览; 从模型库详情弹窗的
 * 「开始搭建」进入): 进度头 ("第 x/y 步 · 已放 n/m 片" + 进度条) +
 * 温和占位条 (3D 搭建视图即将上线, 不锁功能 §4.3) + 步骤列表
 * (序号圆徽 + 中文说明 + 小提示 + 片数增量, 当前步高亮并自动滚动
 * 定位) + 底部「上一步 / 下一步」大按钮 (末步时变「完成 🎉」)。
 *
 * 步骤数据经 MagTileNative.getTutorialSteps (JNI) 读核心库
 * ModelDefinition.steps (与桌面 TutorialEngine 同一份步骤数据);
 * 当前步经 saveTutorialStep 写进度存档 —— 与桌面 CLI / GL / Qt
 * 同一份 SQLite schema (model_progress 表), 口径对齐桌面
 * TutorialViewport: 会话开始即建档 (模型库/进度页立刻显示进行中),
 * 每次步骤导航落盘当前步并按增量累计游玩时长, 走到最后一步记完成
 * + 解锁首搭成就; 存档写入失败只降级不打断搭建 (P3 零挫败)。
 * 断点续搭: 进入时经 savedTutorialStep 读回上次的当前步。
 */
class TutorialActivity : Activity() {

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private lateinit var stepLabel: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var finishedBanner: TextView
    private lateinit var prevButton: Button
    private lateinit var nextButton: Button
    private lateinit var stepList: RecyclerView
    private lateinit var adapter: TutorialStepAdapter

    private var modelId = ""
    private var steps: List<TutorialStep> = emptyList()
    private var totalPieces = 0

    /** 已完成步数 (0..steps.size); 当前展示步 = doneCount + 1 (夹到末步)。 */
    private var doneCount = 0

    /** 数据是否已加载 (加载前忽略导航与落盘)。 */
    private var loaded = false

    /** 上次落盘后的计时起点 (elapsedRealtime 毫秒), 时长按增量累计。 */
    private var playClockStartMs = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_tutorial)

        modelId = intent.getStringExtra(EXTRA_MODEL_ID).orEmpty()
        intent.getStringExtra(EXTRA_MODEL_NAME)?.takeIf { it.isNotBlank() }?.let {
            findViewById<TextView>(R.id.tutorial_title).text = it
        }

        stepLabel = findViewById(R.id.tutorial_step_label)
        progressBar = findViewById(R.id.tutorial_progress)
        finishedBanner = findViewById(R.id.tutorial_finished)
        prevButton = findViewById(R.id.tutorial_prev_button)
        nextButton = findViewById(R.id.tutorial_next_button)

        findViewById<TextView>(R.id.tutorial_back).setOnClickListener { finish() }
        prevButton.setOnClickListener { navigate(-1) }
        nextButton.setOnClickListener { navigate(+1) }

        adapter = TutorialStepAdapter()
        stepList = findViewById<RecyclerView>(R.id.tutorial_steps).apply {
            layoutManager = LinearLayoutManager(this@TutorialActivity)
            adapter = this@TutorialActivity.adapter
        }

        loadStepsAsync()
    }

    /** 离屏 (返回 / Home / 熄屏) 时落盘一次, 把最后一段游玩时长记上。 */
    override fun onPause() {
        super.onPause()
        if (loaded) saveProgressAsync()
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()  // 已入队的收尾落盘照常执行完
    }

    /** 打开存档 + 拉取步骤数据 + 读回断点 (工作线程), 回主线程渲染。 */
    private fun loadStepsAsync() {
        backgroundExecutor.execute {
            try {
                // 独立打开存档: 即使从进程重建直达本屏 (未经 MainActivity
                // 启动流程) 也能读写; 原生上下文是进程级单例, 重复打开无害。
                MagTileNative.openProgressStore(
                    File(filesDir, MainActivity.PROGRESS_DB_NAME).absolutePath)
                val dataDir = DataAssetInstaller.ensureInstalled(this)  // 版本戳一致零拷贝
                val root = JSONObject(
                    MagTileNative.getTutorialSteps(dataDir.absolutePath, modelId))
                check(!root.has("error")) { root.getString("error") }
                // 断点续搭: 上次搭到第几步 (无记录 0; 已完成 = 总步数)
                val savedStep = MagTileNative.savedTutorialStep(modelId)
                runOnUiThread {
                    if (isFinishing || isDestroyed) return@runOnUiThread
                    render(root, savedStep)
                }
            } catch (t: Throwable) {
                Log.e(TAG, "分步教程加载失败: $modelId", t)
                runOnUiThread {
                    if (isFinishing || isDestroyed) return@runOnUiThread
                    findViewById<TextView>(R.id.tutorial_status).text =
                        getString(R.string.tutorial_load_failed, t.message ?: t.toString())
                }
            }
        }
    }

    private fun render(root: JSONObject, savedStep: Int) {
        steps = TutorialStep.listFromJson(root.getJSONArray("steps"))
        totalPieces = root.optInt("total_pieces")
        // 标题以模型数据为准 (覆盖 Intent 附带的展示名, 两者本就一致)
        root.optString("name").takeIf { it.isNotBlank() }?.let {
            findViewById<TextView>(R.id.tutorial_title).text = it
        }

        doneCount = savedStep.coerceIn(0, steps.size)
        adapter.submit(steps, doneCount)
        loaded = true
        playClockStartMs = SystemClock.elapsedRealtime()

        findViewById<TextView>(R.id.tutorial_status).visibility = View.GONE
        findViewById<View>(R.id.tutorial_body).visibility = View.VISIBLE
        updateStepUi()
        // 会话开始即建档 (与桌面 TutorialViewport 同策略): 模型库 /
        // 进度页立刻显示 "进行中" (current_step=0 的新档不进进行中列表)
        saveProgressAsync()
    }

    // ---- 步骤导航 --------------------------------------------------------

    /** 上一步 (-1) / 下一步 (+1): 越界忽略, 变更即刷新三态并落盘。 */
    private fun navigate(delta: Int) {
        if (!loaded) return
        val next = doneCount + delta
        if (next < 0 || next > steps.size) return
        doneCount = next
        adapter.updateDoneCount(doneCount)
        updateStepUi()
        saveProgressAsync()
    }

    /** 进度头 / 进度条 / 按钮态 / 完成庆祝条 / 滚动定位一次刷齐。 */
    private fun updateStepUi() {
        val stepCount = steps.size
        val finished = stepCount > 0 && doneCount >= stepCount

        if (finished) {
            stepLabel.text = getString(
                R.string.tutorial_finished_label, stepCount, totalPieces)
        } else {
            val activeStep = (doneCount + 1).coerceAtMost(maxOf(stepCount, 1))
            val placedPieces = if (doneCount > 0) steps[doneCount - 1].piecesTotal else 0
            stepLabel.text = getString(
                R.string.tutorial_step_of, activeStep, stepCount, placedPieces, totalPieces)
        }
        finishedBanner.visibility = if (finished) View.VISIBLE else View.GONE
        progressBar.max = maxOf(stepCount, 1)
        progressBar.progress = doneCount.coerceIn(0, progressBar.max)

        prevButton.isEnabled = doneCount > 0
        nextButton.isEnabled = !finished
        nextButton.text = getString(
            if (doneCount >= stepCount - 1) R.string.tutorial_next_finish
            else R.string.tutorial_next)

        if (stepCount > 0) {
            // 当前步行定位 (完成态停在末步行, 供「上一步」回看)
            stepList.smoothScrollToPosition(doneCount.coerceAtMost(stepCount - 1))
        }
    }

    // ---- 进度落盘 (与桌面 TutorialViewport::flushProgress 同口径) --------

    /**
     * 写当前步到进度存档: 时长按增量累计 (上次落盘到现在的秒数,
     * 存储层只增不减); 走到最后一步由原生层记完成 + 解锁首搭成就。
     * 写入失败只降级 (进度仍在内存中), 不打断孩子搭建。
     */
    private fun saveProgressAsync() {
        val now = SystemClock.elapsedRealtime()
        val deltaSeconds = ((now - playClockStartMs) / 1000).coerceAtLeast(0)
        playClockStartMs = now
        val step = doneCount
        val stepCount = steps.size
        backgroundExecutor.execute {
            if (!MagTileNative.saveTutorialStep(modelId, step, stepCount, deltaSeconds)) {
                Log.w(TAG, "教程进度暂未落盘 (存档不可用), 本次会话内进度不受影响")
            }
        }
    }

    companion object {
        private const val TAG = "MagTileTutorial"

        /** Intent 附加项: 模型标识 (必填, 经模型库目录解析步骤数据)。 */
        const val EXTRA_MODEL_ID = "model_id"

        /** Intent 附加项: 模型中文名 (选填, 数据加载前先撑起标题)。 */
        const val EXTRA_MODEL_NAME = "model_name"
    }
}
