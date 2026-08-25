#pragma once

// =============================================================
// MagTile Studio (Qt) - 家长门后端桥
//
// ParentGatePage.qml 与 core::ParentGate 之间的桥: 题目生成 /
// 中文大写数字验证 / 3 次答错 60 秒冷却 / 15 分钟家长会话全部由
// 核心状态机负责 (与 GL 版完全同一模块, UI_UX_SPEC.md §9,
// SECURITY_AND_PRIVACY.md §6), 本桥只做 Q_PROPERTY 包装与秒级
// 倒计时通知。会话与冷却只存内存, 永不落盘 ("已通过" 标记不持久
// 化, 防重启绕过) —— 因此本类不接触 ProgressStore。
// =============================================================

#include <QObject>
#include <QString>
#include <QTimer>

#include "magtile/core/parent_gate.hpp"

namespace magtile::qtui {

class ParentGateBackend final : public QObject {
    Q_OBJECT
    /// 当前题面 (中文数字乘法题), 如 "叁 × 柒 = ?"。
    Q_PROPERTY(QString question READ question NOTIFY gateChanged)
    /// 本轮剩余可尝试次数 (答错提示 "还可尝试 N 次")。
    Q_PROPERTY(int attemptsRemaining READ attemptsRemaining NOTIFY gateChanged)
    /// 冷却剩余秒数 (> 0 时门界面切到温和的 "休息一下")。
    Q_PROPERTY(int cooldownSeconds READ cooldownSeconds NOTIFY gateChanged)
    /// 上一次提交是否答错 (温和提示 "再试一次吧"; 出新题 / 冷却时复位)。
    Q_PROPERTY(bool wrongAnswer READ wrongAnswer NOTIFY gateChanged)
    /// 家长会话是否有效 (15 分钟内免重复验证)。
    Q_PROPERTY(bool sessionActive READ sessionActive NOTIFY sessionChanged)
    /// 会话剩余秒数 (家长中心顶部展示, 到期自动退出家长区)。
    Q_PROPERTY(int sessionRemainingSeconds READ sessionRemainingSeconds NOTIFY sessionChanged)
    /// --parent-gate 深链: 启动即打开家长门 (评审 / 冒烟, 同 GL 版)。
    Q_PROPERTY(bool deepLinkRequested READ deepLinkRequested CONSTANT)

public:
    explicit ParentGateBackend(bool deep_link_requested = false, QObject* parent = nullptr);

    [[nodiscard]] QString question() const;
    [[nodiscard]] int attemptsRemaining() const noexcept { return gate_.attemptsRemaining(); }
    [[nodiscard]] int cooldownSeconds() const { return gate_.cooldownRemainingSeconds(); }
    [[nodiscard]] bool wrongAnswer() const noexcept { return wrong_answer_; }
    [[nodiscard]] bool sessionActive() const { return gate_.sessionActive(); }
    [[nodiscard]] int sessionRemainingSeconds() const { return gate_.sessionRemainingSeconds(); }
    [[nodiscard]] bool deepLinkRequested() const noexcept { return deep_link_requested_; }

    /// 进门 (无有效会话时调用): 出一道新题防背题, 复位答错提示。
    Q_INVOKABLE void openGate();

    /// 提交答案 (中文大写数字)。答对返回 true 并发 passed() (家长会话
    /// 已开启); 答错置 wrongAnswer, 连续 3 次进入冷却 ("休息一下")。
    Q_INVOKABLE bool submitAnswer(const QString& answer);

    /// 「锁定家长区」: 立即结束家长会话, 再次进入需重新验证。
    Q_INVOKABLE void lockSession();

    /// 当前题目标准答案 —— 仅供自动化冒烟 / 单元测试使用 (与
    /// core::ParentGate::expectedAnswer 同理: 门拦儿童, 不拦攻击者)。
    Q_INVOKABLE QString expectedAnswer() const;

signals:
    /// 题面 / 尝试次数 / 冷却倒计时 / 答错提示变化。
    void gateChanged();
    /// 家长会话开启 / 倒计时 / 到期 / 手动锁定。
    void sessionChanged();
    /// 答对过门 (QML 据此路由到家长中心)。
    void passed();

private:
    /// 冷却或会话进行期间以 1s 心跳通知 QML 刷新倒计时, 空闲自动停。
    void ensureTicking();

    core::ParentGate gate_;
    bool wrong_answer_ = false;
    bool deep_link_requested_ = false;
    QTimer ticker_;
};

}  // namespace magtile::qtui
