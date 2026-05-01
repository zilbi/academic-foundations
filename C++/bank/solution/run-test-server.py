#!/usr/bin/env python3
import atexit
import pathlib
import socket
import subprocess
import sys
import tempfile
import time


def check_eq(expected: bytes, actual: bytes) -> None:
    if expected != actual:
        print(f'Check failed: expected {repr(expected)}, got {repr(actual)}')
        sys.exit(1)


def main() -> None:
    _, *server_cmd = sys.argv
    assert server_cmd, 'Expected usage: ./run-test-server.py <command-to-run>'

    pfile = tempfile.NamedTemporaryFile(delete=False)
    pfile.close()

    print(f'Starting the server and waiting for the port file {pfile.name}...', flush=True)
    server = subprocess.Popen(args=[*server_cmd, '0', pfile.name])
    def kill_server():
        try:
            server.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            server.kill()
    atexit.register(kill_server)

    while not (port_str := pathlib.Path(pfile.name).read_text()):
        time.sleep(0.1)
        assert server.poll() is None, 'Server has unexpectedly terminated while we were waiting for a port.'
    port = int(port_str)
    assert port != 0, 'A real port cannot be equal 0.  Print the port selected by a TCP listener.'
    print(f'    ok, port is {port}')
    print('Trying to open two connections...', flush=True)

    with socket.socket() as sock_alice, socket.socket() as sock_bob:
        sock_alice.connect(('localhost', port))
        sock_bob.connect(('localhost', port))

        # Binary mode to make sure \n is sent on all systems, otherwise
        # OS-specific newline like \r\n gets sent.
        f_alice = sock_alice.makefile(mode='rwb')
        f_bob = sock_bob.makefile(mode='rwb')

        check_eq(b'What is your name?\n', f_alice.readline())
        check_eq(b'What is your name?\n', f_bob.readline())

        print('    ok')

        print(f'Authenticating as Alice at {sock_alice.getsockname()} and Bob at {sock_bob.getsockname()}...', flush=True)
        f_alice.write(b'Alice\n')
        f_alice.flush()
        f_bob.write(b'Bob\n')
        f_bob.flush()
        check_eq(b'Hi Alice\n', f_alice.readline())
        check_eq(b'Hi Bob\n', f_bob.readline())
        print('    ok')

        print('Transfer from Alice to Bob...', flush=True)
        f_alice.write(b'transfer Bob 90 This is a comment\n')
        f_alice.flush()
        check_eq(b'OK\n', f_alice.readline())
        print('    ok')

        print('Invalid transfer from Alice to Bob...', flush=True)
        f_alice.write(b'transfer Bob 90 This is an another comment\n')
        f_alice.flush()
        check_eq(b'Not enough funds: 10 XTS available, 90 XTS requested\n', f_alice.readline())
        print('    ok')

        print('Checking balance in several packets...', flush=True)
        f_alice.write(b'balance\n')
        f_alice.flush()
        f_bob.write(b'bala')
        f_bob.flush()
        f_bob.write(b'nce\n')
        f_bob.flush()
        check_eq(b'10\n', f_alice.readline())
        check_eq(b'190\n', f_bob.readline())
        print('    ok')

        print('Checking last transactions...', flush=True)
        f_alice.write(b'transactions 10\n')
        f_alice.flush()
        check_eq(b'CPTY\tBAL\tCOMM\n', f_alice.readline())
        check_eq(b'-\t100\tInitial deposit for Alice\n', f_alice.readline())
        check_eq(b'Bob\t-90\tThis is a comment\n', f_alice.readline())
        check_eq(b'===== BALANCE: 10 XTS =====\n', f_alice.readline())
        print('    ok')

        print('Checking some of last transactions...', flush=True)
        f_alice.write(b'transactions 1\n')
        f_alice.flush()
        check_eq(b'CPTY\tBAL\tCOMM\n', f_alice.readline())
        check_eq(b'Bob\t-90\tThis is a comment\n', f_alice.readline())
        check_eq(b'===== BALANCE: 10 XTS =====\n', f_alice.readline())
        print('    ok')

        print('Starting monitoring...', flush=True)
        f_alice.write(b'monitor 1\n')
        f_alice.flush()
        check_eq(b'CPTY\tBAL\tCOMM\n', f_alice.readline())
        check_eq(b'Bob\t-90\tThis is a comment\n', f_alice.readline())
        check_eq(b'===== BALANCE: 10 XTS =====\n', f_alice.readline())
        print('    ok')

        print('Doing another transfer and waiting for monitoring to display it...', flush=True)
        f_bob.write(b'transfer Alice 50  Another comment\n')
        f_bob.flush()
        check_eq(b'OK\n', f_bob.readline())
        check_eq(b'Bob\t50\t Another comment\n', f_alice.readline())
        print('    ok')

        print('Issuing invalid command in several packets...', flush=True)
        f_bob.write(b'wt')
        f_bob.flush()
        f_bob.write(b'f\n')
        f_bob.flush()
        check_eq(b"Unknown command: 'wtf'\n", f_bob.readline())
        print('    ok')
    print('All ok.')


if __name__ == '__main__':
    main()
