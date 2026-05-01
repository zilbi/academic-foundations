#ifndef BANKHPP_
#define BANKHPP_

#include <condition_variable>
#include <deque>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <stdexcept>
#include <string>
#include <unordered_map>

namespace bank {

struct user;
struct user_transactions_iterator;

struct transaction {
    const user *const
        counterparty;  // NOLINT(misc-non-private-member-variables-in-classes)
    const int
        balance_delta_xts;  // NOLINT(misc-non-private-member-variables-in-classes)
    const std::string
        comment;  // NOLINT(misc-non-private-member-variables-in-classes)

    transaction(
        const user *counterparty,
        int balance_delta_xts,
        std::string comment  // cppcheck-suppress passedByValue
    ) noexcept
        : counterparty(counterparty),
          balance_delta_xts(balance_delta_xts),
          comment(std::move(comment)) {
    }
};

struct user {
    const std::string &name() const noexcept;

    void
    transfer(user &counterparty, int amount_xts, const std::string &comment);
    int balance_xts() const;
    template <typename Callback>
    auto snapshot_transactions(Callback &&callback) const;

    [[nodiscard]] user_transactions_iterator monitor() const;
    transaction wait_next_transaction(std::size_t &next_id) const;

    explicit user(std::string name) : name_(std::move(name)) {
        transactions_.emplace_back(
            nullptr, 100, "Initial deposit for " + name_
        );
    }

private:
    std::string name_;
    int balance_xts_ = 100;
    std::deque<transaction> transactions_;
    mutable std::shared_mutex mutex_;
    mutable std::condition_variable_any cv_;
};

struct user_transactions_iterator {
    transaction wait_next_transaction();

    user_transactions_iterator(const user *user, std::size_t next_id)
        : user_(user), next_id_(next_id) {
    }

private:
    const user *user_;
    std::size_t next_id_;
};

struct ledger {
    user &get_or_create_user(const std::string &name);

private:
    std::unordered_map<std::string, std::unique_ptr<user>> users_;
    mutable std::shared_mutex mutex_;
};

template <typename Callback>
auto user::snapshot_transactions(Callback &&callback) const {
    const std::shared_lock<std::shared_mutex> lock(mutex_);
    callback(transactions_, balance_xts_);
    return user_transactions_iterator(this, transactions_.size());
}

struct transfer_error : std::runtime_error {
    explicit transfer_error(const std::string &msg) : std::runtime_error(msg) {
    }
};

struct not_enough_funds_error : transfer_error {
    not_enough_funds_error()
        : transfer_error(
              "Zilbi bank: Not enough funds to complete this transaction."
          ) {
    }
};

struct invalid_amount_error : transfer_error {
    invalid_amount_error()
        : transfer_error(
              "Zilbi bank: An incorrect transaction amount has been entered."
          ) {
    }
};

struct self_transfer_error : transfer_error {
    self_transfer_error()
        : transfer_error("Zilbi bank: You can not transfer money to yourself!"
          ) {
    }
};

}  // namespace bank

#endif  // BANKHPP_