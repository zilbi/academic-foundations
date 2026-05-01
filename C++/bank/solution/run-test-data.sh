#!/bin/bash
set -euo pipefail
# Array should not be empty on macOS (old Bash expands empty array to unset variable and errs)
BANK_TEST_COMMAND=(./bank-test)
BANK_SERVER_COMMAND=(./bank-server)
TIMEOUT=30s  # Careful of Valgrind

FAIL=0
# Warning: use \033 instead of \e for compatibility with old Bash on macOS.

echo -n "Detecting tasks... "
TASKS=$(timeout --foreground -k 0.1s "$TIMEOUT" ./tasks-info)
echo "$TASKS"

echo "Running tests with ${BANK_TEST_COMMAND[@]}"
if ! timeout --foreground -k 0.1s "$TIMEOUT" "${BANK_TEST_COMMAND[@]}"; then
    FAIL=1
fi

if [[ $TASKS -ge 3 ]]; then
    echo
    echo
    echo "Running server with ${BANK_SERVER_COMMAND[@]}"
    if ! timeout --foreground -k 0.1s "$TIMEOUT" ./run-test-server.py "${BANK_SERVER_COMMAND[@]}"; then
        FAIL=1
    fi
fi

if [[ "$FAIL" == "0" ]]; then
    echo -e "===== \033[32;1mALL PASS\033[0m ====="
else
    echo -e "===== \033[31;1mSOME FAIL\033[0m ====="
fi
exit $FAIL
