#include "bank.hpp"
#include <memory>
#include <mutex>
#include <shared_mutex>

namespace bank {

const std::string &user::name() const noexcept {
    return name_;
}

int user::balance_xts() const {
    const std::shared_lock<std::shared_mutex> lock(mutex_);
    return balance_xts_;
}

user &ledger::get_or_create_user(const std::string &name) {
    {
        const std::shared_lock<std::shared_mutex> lock(mutex_);
        auto it = users_.find(name);
        if (it != users_.end()) {
            return *it->second;
        }
    }
    const std::unique_lock<std::shared_mutex> lock(mutex_);
    auto it = users_.find(name);
    if (it != users_.end()) {
        return *it->second;
    }
    auto tmp = std::make_unique<user>(name);
    user &res = *tmp;
    users_[name] = std::move(tmp);
    return res;
}

void user::transfer(
    user &counterparty,
    int amount_xts,
    const std::string &comment
) {
    if (amount_xts <= 0) {
        throw invalid_amount_error();
    }
    if (this == &counterparty) {
        throw self_transfer_error();
    }
    const std::scoped_lock<std::shared_mutex, std::shared_mutex> lock(
        mutex_, counterparty.mutex_
    );
    if (balance_xts_ < amount_xts) {
        throw not_enough_funds_error();
    }
    balance_xts_ -= amount_xts;
    transactions_.emplace_back(&counterparty, -amount_xts, comment);
    counterparty.balance_xts_ += amount_xts;
    counterparty.transactions_.emplace_back(this, amount_xts, comment);
    cv_.notify_all();
    counterparty.cv_.notify_all();
}

user_transactions_iterator user::monitor() const {
    const std::shared_lock<std::shared_mutex> lock(mutex_);
    return {this, transactions_.size()};
}

transaction user::wait_next_transaction(std::size_t &next_id) const {
    std::unique_lock<std::shared_mutex> lock(mutex_);
    cv_.wait(lock, [this, next_id] { return next_id < transactions_.size(); });
    auto tmp = transactions_[next_id];
    next_id++;
    return tmp;
}

transaction user_transactions_iterator::wait_next_transaction() {
    return user_->wait_next_transaction(next_id_);
}

}  // namespace bank
