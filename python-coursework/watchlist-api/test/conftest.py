"""
Фикстуры для тестов Watchlist API.

Тесты работают через HTTP (чёрный ящик):
  - Не импортируют модели/БД напрямую
  - Используют TestClient (sync) для корректности
  - Используют httpx.AsyncClient для нагрузочного теста
"""

import os
import subprocess
import sys
import time

import httpx
import pytest


# ── Константы ───────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
STARTUP_TIMEOUT = 10  # секунд на запуск сервера


# ── Сервер ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def server():
    """Запускает uvicorn перед тестами, останавливает после."""
    # Ограничиваем пул синхронных потоков — увеличением pool_size не обойти.
    # Единственный способ пройти нагрузочный тест — использовать async def
    # с асинхронным драйвером БД (asyncpg / async SQLAlchemy).
    env = {**os.environ, "ANYIO_THREADPOOL_SIZE": "3"}

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "solution.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    # Ждём, пока сервер ответит
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/genres", timeout=1)
            if r.status_code in (200, 404, 405):
                break
        except httpx.ConnectError:
            time.sleep(0.3)
    else:
        proc.terminate()
        out, err = proc.communicate(timeout=5)
        pytest.fail(
            f"Сервер не запустился за {STARTUP_TIMEOUT}s.\n"
            f"stdout: {out.decode()}\nstderr: {err.decode()}"
        )

    yield proc

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def client():
    """Sync HTTP-клиент для тестов корректности."""
    with httpx.Client(base_url=BASE_URL, timeout=5) as c:
        yield c


# ── Хелперы для тестов ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seed_data(client):
    """Создаёт базовые данные для тестов. Вызывается один раз."""
    # Жанры
    genres = {}
    for name in ("action", "comedy", "drama"):
        r = client.post("/genres", json={"name": name})
        assert r.status_code == 201, f"POST /genres failed: {r.text}"
        genres[name] = r.json()["id"]

    # Фильмы
    movies = {}
    films = [
        ("Inception", 2010, "action"),
        ("The Hangover", 2009, "comedy"),
        ("Parasite", 2019, "drama"),
        ("Interstellar", 2014, "action"),
        ("Whiplash", 2014, "drama"),
    ]
    for title, year, genre in films:
        r = client.post("/movies", json={
            "title": title, "year": year, "genre_id": genres[genre],
        })
        assert r.status_code == 201, f"POST /movies failed: {r.text}"
        movies[title] = r.json()["id"]

    # Пользователи
    users = {}
    for name, email in [("alice", "alice@test.com"), ("bob", "bob@test.com")]:
        r = client.post("/users", json={"username": name, "email": email})
        assert r.status_code == 201, f"POST /users failed: {r.text}"
        users[name] = r.json()["id"]

    return {"genres": genres, "movies": movies, "users": users}
