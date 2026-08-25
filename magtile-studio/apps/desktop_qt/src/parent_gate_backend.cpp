#include "parent_gate_backend.hpp"

namespace magtile::qtui {

namespace {

QString fromUtf8(const std::string& s) {
    return QString::fromUtf8(s.c_str(), static_cast<int>(s.size()));
}

}  // namespace

ParentGateBackend::ParentGateBackend(bool deep_link_requested, QObject* parent)
    : QObject(parent), deep_link_requested_(deep_link_requested) {
    ticker_.setInterval(1000);
    connect(&ticker_, &QTimer::timeout, this, [this]() {
        emit gateChanged();     // 冷却倒计时 (到 0 时门界面自动回到题面)
        emit sessionChanged();  // 会话倒计时 (到 0 时家长区自动退出)
        if (!gate_.coolingDown() && !gate_.sessionActive()) ticker_.stop();
    });
}

QString ParentGateBackend::question() const { return fromUtf8(gate_.question()); }

void ParentGateBackend::openGate() {
    gate_.newChallenge();  // 每次进门都是新题, 防背题 (与 GL 版一致)
    wrong_answer_ = false;
    ensureTicking();  // 可能仍处于上一轮的冷却期, 倒计时要继续走
    emit gateChanged();
}

bool ParentGateBackend::submitAnswer(const QString& answer) {
    switch (gate_.submitAnswer(answer.trimmed().toStdString())) {
        case core::ParentGateResult::Passed:
            wrong_answer_ = false;
            ensureTicking();
            emit gateChanged();
            emit sessionChanged();
            emit passed();
            return true;
        case core::ParentGateResult::WrongAnswer:
            wrong_answer_ = true;
            emit gateChanged();
            return false;
        case core::ParentGateResult::CoolingDown:
            wrong_answer_ = false;  // 冷却界面自带温和提示 (与 GL 版一致)
            ensureTicking();
            emit gateChanged();
            return false;
    }
    return false;  // 防御: 枚举外值
}

void ParentGateBackend::lockSession() {
    gate_.endSession();
    emit sessionChanged();
}

QString ParentGateBackend::expectedAnswer() const { return fromUtf8(gate_.expectedAnswer()); }

void ParentGateBackend::ensureTicking() {
    if (!ticker_.isActive() && (gate_.coolingDown() || gate_.sessionActive())) {
        ticker_.start();
    }
}

}  // namespace magtile::qtui
