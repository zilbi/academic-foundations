# Banking System Simulation

## Overview

A C++ project implementing a simplified banking system with a thread-safe ledger, user accounts, transaction history, blocking transaction monitoring, and a TCP-based client-server interface.

## Project highlights

- Const-thread-safe bank ledger and user model
- Money transfers with exception-safe state handling
- Transaction history and blocking transaction iterator
- Multithreaded logic using mutexes and condition variables
- TCP server interface using Boost.Asio

## Original assignment

## Contents

- [Task](#task)
  - [Advice](#advice)
  - [A Digression](#a-digression)
- [Solution Correctness Requirements](#solution-correctness-requirements)
  - [Basic Requirements](#basic-requirements)
  - [Additional Requirements](#additional-requirements)
  - [Ledger](#ledger)
  - [Blocking Iterator](#blocking-iterator)
  - [Network Server](#network-server)


## Task

This task consists of three parts. You may implement only a prefix of them and [receive partial credit](#grading-system).

1. **Ledger**.
   Write const-thread-safe classes `bank::ledger`, `bank::user`, and `bank::transaction` representing a toy bank.
   Each user:
    * Has a unique name.
    * Can get their current balance in the `XTS` currency and their transaction history.
    * Is created at the moment of first access and receives 100 XTS (this is a [test currency from ISO 4217](https://en.wiktionary.org/wiki/XTS)).
    * Can transfer currency to any other user.
    * If a logical error occurs during a transfer,
      an exception derived from `bank::transfer_error` is thrown with a detailed `what()`, and the ledger state is not changed.
2. **Blocking iterator**.
   Add the ability to track a user's transactions in a thread-safe blocking mode using the `bank::user_transactions_iterator` class:
    * The `wait_next_transaction()` method blocks until the user's next transaction appears, then returns it.
    * It must be possible to inspect the current user state and create a `bank::user_transactions_iterator` in one atomic operation.
      Otherwise, some transactions may be lost between reading the state and creating the iterator.
3. **Network server**.
   Write a TCP server that creates one ledger and lets TCP clients act as bank users
   through a [stateful protocol](https://en.wikipedia.org/w/index.php?title=Stateful_protocol&redirect=no):
    * Each TCP client connects as one of the users and acts on that user's behalf.
    * All methods of the `bank::user` class are supported, as well as error messages.
    * Use `boost::asio::ip::tcp::iostream` for blocking network interaction.
    * TCP clients may connect and disconnect at any moment, and one user may be controlled by several clients at the same time.

See the tests for the exact supported methods, and the requirements below for the subtleties of their semantics.

### Advice

* Implement the parts from top to bottom.
  * In the first part (ledger), you will only need `std::mutex` and `std::unique_lock`/`std::scoped_lock`.
  * In the second part (blocking iterator), `std::condition_variable` is added.
  * In the third part, `std::thread` and `boost::asio::ip::tcp` are added.
* Clearly describe what is protected by which mutexes and what conditions each condition variable is responsible for.
* Be careful with deadlocks; they are very easy to get when transferring money from one user to another.
* Do not rely on the provided autotests to catch all multithreading problems.
* Use ThreadSanitizer or Helgrind.
  * Be careful: they may produce false positives about different mutex lock orders or parts of the standard library.
  * Warnings about different mutex lock orders can be suppressed by passing `--track-lockorders=no` when running.
* If you write your own autotests, make them large and with many threads that try to read and write the same resource simultaneously.
* Use `netcat` for debugging the network server.
* Note that locking a mutex is not `noexcept`.
* Remember that correct communication with a TCP client requires flushing the buffer
  and regularly checking whether the input/output streams are still valid, since the client may have disconnected.
* If the `bank::ledger` class is boring, have some fun with `emplace_hint` and `piecewise_construct`.
* Be careful: [`boost::asio::ip::tcp::iostream` may specifically be non-movable under Clang](https://github.com/chriskohlhoff/asio/issues/997).
* The construct `friend struct Bar;` inside a `Foo` structure may be useful: it makes
  the entire `Bar` structure a friend of `Foo`.
  In particular, all methods and fields of `Bar` get access to the private fields and methods of `Foo`.
* The construct `const T*` may be useful: it means "a non-const pointer to a const `T`",
  while `T *const` means "a const pointer to a non-const `T`".

### A Digression

* Read operations in multithreaded programs are rare, but they are included here for educational reasons.
  * For example, if we read a user's balance using `.balance_xts()`, we cannot really use that data: the balance may have just changed in another thread.
  * A similar problem exists with the `.monitor()` method: we do not know from what moment we actually started watching transactions.
  * That is why higher-level complex methods such as `snapshot_transactions` are usually required.
* Since money can be measured in different units, all methods and variables have the unit suffix `_xts`.
  * Here there is only one unit, so it is hard to get confused, but in more complex programs this matters more.
    For example: `timeout_millis`, `timeout_micros`, `timeout_ms` (milli or micro?), `timeout_sec`.
* The automatic multithreading tests are written somewhat awkwardly:
  * `CHECK`/`REQUIRE` are never called from a non-main thread, even though `doctest` is thread-safe.
    Instead, data is only collected there and then checked in the main thread.
  * This is done so the autotests can run under MinGW.
    The required `thread_local` construct has worked poorly there for the last ten years (that is, always),
    which can make doctest (and other libraries) [crash under a debugger](https://github.com/onqtam/doctest/issues/501#issuecomment-827577621).
* It would be nice to learn how to exit the `monitor` command on the server, but we cannot do that without contortions:
  both I/O through `tcp::iostream` is blocking (which is half the problem), and the iterator is blocking (which is the other half).
  That is, we cannot wait for either a command or the next transaction in one operation; we have to choose.
  * In general, we could create a second thread for the `monitor` command that waits for transactions, and a third thread
    that turns the blocking iterator into a non-blocking one... But we will not do that.

## Solution Correctness Requirements

### Basic Requirements

The [standard requirements](../common/) apply.
Note that a race condition is UB and is forbidden, even if it does not visibly break anything.

The maximum total number of lines, including blank lines, in `.hpp` and `.cpp` files is 500.
The full author's solution takes 403 lines.

When run under Valgrind, the solution is compiled with the `-DEXPECT_VALGRIND` flag so the tests become slightly smaller.
When run under AddressSanitizer on Linux (but not on macOS), the solution is compiled with the `-DEXPECT_ASAN` flag
so that one particular test becomes slightly smaller and does not require a lot of memory on the grading machine.

### Additional Requirements

* If several threads work with disjoint subsets of already-created users, they must not interfere with one another.
    * In particular, creating one global mutex for all operations on all users will not work.
    * And if one thread is creating a new user, other threads may not access the ledger at that time.
* Blocking I/O under a mutex is forbidden, because it may hang for an indefinite time.
    * Hint: be careful with `snapshot_transactions`.
* Different kinds of exceptions must have different classes.
* It is forbidden to change `CMakeLists.txt` and/or add new files.
  If you really need to, discuss it with the instructor.

#### Forbidden Techniques

Violating any of the requirements below gives zero points for the corresponding part and the parts that depend on it.

* It is forbidden to hack thread synchronization together using `std::this_thread::sleep_for` and similar tricks.
* The blocking iterator should generally use blocking waiting, such as through a condition variable, rather than active waiting.

### Ledger

An instance of the `bank::ledger` class owns the users of the corresponding ledger.
The `get_or_create_user(name)` method atomically returns a reference to the user `name`,
which remains valid while the ledger is alive.
If that user did not exist yet, it is added to the ledger.
Users are not moved in memory, so a pointer to a user can be used as an identifier.

Each user can report, thread-safely and in constant time:
* Their name: `.name()`
* Their current balance: `.balance_xts()`, which fits in an `int` and is non-negative.

There must also be a way to inspect part of a user's transactions in a thread-safe way without copying all of them.
For this, the `.snapshot_transactions(f)` method accepts a functor `f` and calls it under a mutex,
passing the transactions and the current balance as parameters.
This lets you read any part of the transactions without interference from other threads.
The balance must be passed so that `f` can obtain it in constant time without calling `.balance_xts()` (otherwise a reentrant mutex would be required).

You may store transactions and pass them to the `snapshot_transactions(f)` parameter
in any sequential container.
Old transactions come first.
A transaction must be represented by a `bank::transaction` structure with constant public fields:
* `counterparty`: a pointer to the user on the other side of the transaction, or `nullptr`
  if that side is the bank itself (during the initial money deposit).
* `balance_delta_xts`: how much the user's balance changed because of the transaction.
* `comment`: an arbitrary transaction comment.

The `.transfer(counterparty, amount_xts, comment)` method on a `user`
atomically transfers `amount_xts` XTS to `counterparty`.
After that, each user must have exactly one new transaction.
If this cannot be done, an exception derived from `bank::transfer_error`
must be thrown with details.
If `user` does not have enough money, a `bank::not_enough_funds_error` exception
must be thrown with a fixed message (see the tests).
This is not the only possible transfer error; you need to infer the others yourself
from common sense and the task requirements.

### Blocking Iterator

The `snapshot_transactions(f)` method now, in addition to giving access to transactions, atomically returns
an instance of the `user_transactions_iterator` class.

This iterator has a single method, `wait_next_transaction`, which returns
the next transaction that did not get into `snapshot_transactions`.
If such a transaction has not happened yet, it blocks until one appears.
Because `snapshot_transactions()` works atomically, this allows any thread
to fully know the state of any user.
Inside `snapshot_transactions`, you can inspect all transactions up to a certain moment
(the call to `snapshot_transactions`),
and the iterator lets you inspect all transactions after that moment.

Several independent iterators may exist at the same time.

The `monitor()` method is also added to `bank::user`; it simply returns an iterator
that lets you watch all transactions from the moment `monitor()` is called.
It is used in some tests, but in general [it is a bad API](#a-digression).

### Network Server

The console application is launched as follows:

```
./bank-server <port> <port-file>
```

On startup, it immediately creates a TCP server on the port `<port>`.
`<port>` may be zero; that is exactly what should be passed to the `tcp::endpoint` constructor,
and then `tcp::acceptor` will choose a random free port. This is convenient for automatically
testing several solutions on one machine in parallel.
The selected server port must be saved to the file `<port-file>`.
If that fails, print the message `Unable to store port to file <port-file>` to the standard error stream.

The server creates one global ledger for itself, which all clients work with.
Bank users are never deleted from it or recreated.
The server may use only the public class methods described in the task.

All server messages are printed to the standard output stream; flushing the buffer after each message is mandatory:

* At the start, print the message `Listening at <endpoint>`,
  where `<endpoint>` is `acceptor.local_endpoint()`, where the server is available locally.
* When a client connects, print the message `Connected <remote> --> <local>`,
  where `<remote>` and `<local>` are `remote_endpoint()` and `local_endpoint()` for the client, respectively.
  `local_endpoint()` will be a special case of `acceptor.local_endpoint()`.
* When a client disconnects (for any reason), print the analogous `Disconnected <remote> --> <local>`.

All TCP clients are handled in parallel in different threads.
If one client disconnects, nothing happens to the others.
All server responses end with a newline.
Each client corresponds to one bank user;
all user names are non-empty and consist of characters with codes 33-127.
Each user may be operated by several clients at the same time.
A session with each client starts with user authorization:

* Server: `What is your name?\n`.
* Client: `<username>` and a whitespace character.
* Server: `Hi <username>\n`.

After that, the server waits for commands from the client.
Commands, and their arguments, are separated from each other by whitespace characters:

* `balance`.
  The response is one integer (the user's current balance) and a newline.
* `transactions <n>`.
  The response is the user's last `n` transactions on `n+2` lines.
  * See the `run-test-server.py` test for the exact format.
  * Cells in a table row are separated by one tab character.
  * It is guaranteed that `<n>` is non-negative and fits in an `int`.
  * If there are fewer than `n` transactions, all of the user's transactions are printed.
* `monitor <n>`.
  Similar to `transactions <n>`, but after the last transaction
  the server does not wait for the next command; instead, it starts endlessly printing the user's transaction stream.
  * This lets users watch their transactions "in real time".
  * It is impossible to exit this command.
    Moreover, for simplicity, it is not required to print the `Disconnected` message immediately when the client disconnects.
* `transfer <counterparty> <amount> <comment>`: transfer to the user `<counterparty>`.
  * There is exactly one whitespace character between `<amount>` and `<comment>`,
    `<comment>` is non-empty and ends with `\n`.
  * In particular, `<comment>` may contain spaces: `transfer Bob 100 Some real comment`.
  * The response is `OK\n` if the transfer succeeds, or the error message from `.what()` followed by a newline
    if the transfer fails.
  * Since the server may use only public methods, if the user `<counterparty>` did not exist,
    they are created automatically according to the behavior of `get_or_create_user`.
* Any other command. The response is `Unknown command: '<entered-command>'\n`.
  * For example, if the user enters `hello world\n`, it is treated as two unknown commands: `hello` and `world`.

We assume that if the command name is entered correctly, then all command parameters are also valid.
However, the connection with the client may still break at any moment.
We also assume that in a correct implementation, every user's balance fits in an `int` at every moment in time.
