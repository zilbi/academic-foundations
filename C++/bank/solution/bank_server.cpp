#ifdef _MSC_VER
#include <crtdbg.h>
#endif

#include <boost/asio.hpp>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include "bank.hpp"
using boost::asio::ip::tcp;

namespace {
std::mutex &log_mutex() {
    static std::mutex mutex;
    return mutex;
}

void log_line(const std::string &line) {
    const std::lock_guard<std::mutex> lock(log_mutex());
    std::cout << line << '\n';
    std::cout.flush();
}
}  // namespace

void print_transaction(tcp::iostream &stream, const bank::transaction &tr) {
    if (tr.counterparty == nullptr) {
        stream << "-";
    } else {
        stream << tr.counterparty->name();
    }
    stream << "\t" << tr.balance_delta_xts << "\t" << tr.comment << "\n";
}

template <typename Transactions>
void print_transactions_snapshot(
    tcp::iostream &stream,
    const Transactions &transactions,
    int balance_xts,
    int n
) {
    stream << "CPTY\tBAL\tCOMM\n";

    const int sz = static_cast<int>(transactions.size());
    int from = sz - n;
    if (from < 0) {
        from = 0;
    }

    for (int i = from; i < sz; ++i) {
        print_transaction(stream, transactions[i]);
    }

    stream << "===== BALANCE: " << balance_xts << " XTS =====\n";
}

void print_last_transactions(
    tcp::iostream &stream,
    const bank::user &user,
    int n
) {
    user.snapshot_transactions([&](const auto &transactions, int balance_xts) {
        print_transactions_snapshot(stream, transactions, balance_xts, n);
    });
    stream.flush();
}

void monitor_transactions(
    tcp::iostream &stream,
    const bank::user &user,
    int n
) {
    bank::user_transactions_iterator it =
        user.snapshot_transactions([&](const auto &transactions,
                                       int balance_xts) {
            print_transactions_snapshot(stream, transactions, balance_xts, n);
        });
    stream.flush();

    while (true) {
        const bank::transaction tr = it.wait_next_transaction();
        print_transaction(stream, tr);
        stream.flush();
        if (!stream) {
            return;
        }
    }
}

void handler(tcp::iostream &stream, bank::ledger &ledger) {
    const auto remote = stream.socket().remote_endpoint();
    const auto local = stream.socket().local_endpoint();

    log_line(
        "Connected " + remote.address().to_string() + ":" +
        std::to_string(remote.port()) + " --> " + local.address().to_string() +
        ":" + std::to_string(local.port())
    );

    stream << "What is your name?\n";
    stream.flush();

    std::string name;
    if (!(stream >> name)) {
        log_line(
            "Disconnected " + remote.address().to_string() + ":" +
            std::to_string(remote.port()) + " --> " +
            local.address().to_string() + ":" + std::to_string(local.port())
        );
        return;
    }

    bank::user &user = ledger.get_or_create_user(name);

    stream << "Hi " << user.name() << "\n";
    stream.flush();

    std::string command;
    while (stream >> command) {
        if (command == "balance") {
            stream << user.balance_xts() << "\n";
            stream.flush();
        } else if (command == "transactions") {
            int count = 0;
            stream >> count;
            if (!stream) {
                break;
            }
            print_last_transactions(stream, user, count);
        } else if (command == "monitor") {
            int count = 0;
            stream >> count;
            if (!stream) {
                break;
            }
            monitor_transactions(stream, user, count);
            return;
        } else if (command == "transfer") {
            std::string counterparty_name;
            int amount_xts = 0;
            stream >> counterparty_name >> amount_xts;
            if (!stream) {
                break;
            }

            stream.get();

            std::string comment;
            std::getline(stream, comment);

            try {
                bank::user &counterparty =
                    ledger.get_or_create_user(counterparty_name);
                user.transfer(counterparty, amount_xts, comment);
                stream << "OK\n";
            } catch (const bank::not_enough_funds_error &) {
                stream << "Not enough funds: " << user.balance_xts()
                       << " XTS available, " << amount_xts
                       << " XTS requested\n";
            } catch (const bank::transfer_error &e) {
                stream << e.what() << "\n";
            }
            stream.flush();
        } else {
            stream << "Unknown command: '" << command << "'\n";
            stream.flush();
        }
    }

    log_line(
        "Disconnected " + remote.address().to_string() + ":" +
        std::to_string(remote.port()) + " --> " + local.address().to_string() +
        ":" + std::to_string(local.port())
    );
}

int main(int argc, char *argv[]) {
#ifdef _MSC_VER
    _CrtSetReportMode(_CRT_ASSERT, _CRTDBG_MODE_FILE | _CRTDBG_MODE_DEBUG);
    _CrtSetReportFile(_CRT_ASSERT, _CRTDBG_FILE_STDERR);
    _CrtSetReportMode(_CRT_ERROR, _CRTDBG_MODE_FILE | _CRTDBG_MODE_DEBUG);
    _CrtSetReportFile(_CRT_ERROR, _CRTDBG_FILE_STDERR);
#endif
    if (argc != 3) {
        return 1;
    }
    try {
        boost::asio::io_context io_context;
        bank::ledger ledger;
        // NOLINTBEGIN(cppcoreguidelines-pro-bounds-pointer-arithmetic)
        const std::string port_str(argv[1]);
        const auto port = static_cast<unsigned short>(std::stoi(port_str));
        const std::string port_file(argv[2]);
        // NOLINTEND(cppcoreguidelines-pro-bounds-pointer-arithmetic)
        tcp::acceptor acceptor(io_context, tcp::endpoint(tcp::v4(), port));

        {
            std::ofstream out(port_file);
            if (!out) {
                std::cerr << "Unable to store port to file " << port_file
                          << '\n';
                return 1;
            }
            out << acceptor.local_endpoint().port() << "\n";
        }
        {
            const auto ep = acceptor.local_endpoint();
            log_line(
                "Listening at " + ep.address().to_string() + ":" +
                std::to_string(ep.port())
            );
        }

        while (true) {
            auto stream = std::make_shared<tcp::iostream>();
            acceptor.accept(stream->socket());

            std::thread([&ledger, stream]() {
                try {
                    handler(*stream, ledger);
                } catch (const std::exception &) {
                }
            }).detach();
        }
    } catch (const std::exception &) {
        return 1;
    }
}
