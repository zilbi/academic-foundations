#include <iostream>
#include "test_utils.hpp"

int main() {
    std::cout <<
#if !defined(TEST_USER_TRANSACTIONS_ITERATOR)
        1
#elif !defined(TEST_SERVER)
        2
#else
        3
#endif
        ;
}
