"""
Нагрузочный тест (15 баллов).

Проверяет, что сервер обрабатывает конкурентные запросы эффективно.
Если тест не проходит — подумайте, что ограничивает параллелизм
вашего сервера.
"""

import asyncio

import httpx
import pytest

BASE_URL = "http://localhost:8000"


async def _setup_data():
    """Создаёт данные для нагрузочного теста, если их ещё нет."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        # Жанр
        r = await client.post("/genres", json={"name": "perf_test_genre"})
        if r.status_code == 201:
            genre_id = r.json()["id"]
        else:
            r = await client.get("/genres")
            genres = r.json()
            genre_id = next(g["id"] for g in genres if g["name"] == "perf_test_genre")

        # 2 пользователя для отзывов
        user_ids = []
        for i in range(2):
            r = await client.post("/users", json={
                "username": f"perf_user_{i}",
                "email": f"perf{i}@test.com",
            })
            if r.status_code == 201:
                user_ids.append(r.json()["id"])
            else:
                r = await client.get(f"/users")  # noqa
                pass  # пользователи уже существуют

        # 50 фильмов с отзывами — делает /movies/top тяжелее
        for i in range(50):
            r = await client.post("/movies", json={
                "title": f"PerfMovie {i}",
                "year": 2000 + i % 25,
                "genre_id": genre_id,
            })
            if r.status_code == 201 and user_ids:
                movie_id = r.json()["id"]
                for uid in user_ids:
                    await client.post("/reviews", json={
                        "user_id": uid, "movie_id": movie_id,
                        "rating": (i % 9) + 1,
                    })


@pytest.fixture(scope="module")
def setup_perf_data():
    asyncio.run(_setup_data())


@pytest.mark.asyncio
async def test_concurrent_reads(setup_perf_data):
    """
    100 параллельных GET /movies должны завершиться менее чем за 1 секунду.

    Если тест падает — подумайте:
      * Как FastAPI обрабатывает def-эндпоинты под нагрузкой?
      * Чем async def отличается от def с точки зрения параллелизма?
      * Какой драйвер БД позволяет не блокировать event loop?
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        tasks = [client.get("/movies") for _ in range(100)]

        start = asyncio.get_running_loop().time()
        responses = await asyncio.gather(*tasks)
        elapsed = asyncio.get_running_loop().time() - start

    failed = [r for r in responses if r.status_code != 200]
    assert not failed, (
        f"{len(failed)} из 100 запросов вернули ошибку. "
        f"Первая ошибка: {failed[0].status_code} {failed[0].text[:200]}"
    )

    assert elapsed < 1.0, (
        f"100 параллельных GET /movies заняли {elapsed:.2f}s (лимит: 1.0s).\n"
        f"Подсказка: def-эндпоинты выполняются в ограниченном пуле потоков.\n"
        f"Изучите разницу между def и async def в FastAPI, а также\n"
        f"как asyncpg или async SQLAlchemy помогают не блокировать event loop."
    )


@pytest.mark.asyncio
async def test_concurrent_mixed(setup_perf_data):
    """
    50 параллельных запросов к разным эндпоинтам.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        tasks = []
        for i in range(50):
            if i % 3 == 0:
                tasks.append(client.get("/movies"))
            elif i % 3 == 1:
                tasks.append(client.get("/genres"))
            else:
                tasks.append(client.get("/movies/top", params={"limit": 5}))

        start = asyncio.get_running_loop().time()
        responses = await asyncio.gather(*tasks)
        elapsed = asyncio.get_running_loop().time() - start

    ok = [r for r in responses if r.status_code == 200]
    assert len(ok) >= 45, (
        f"Только {len(ok)} из 50 запросов вернули 200."
    )

    assert elapsed < 1.0, (
        f"50 параллельных запросов заняли {elapsed:.2f}s (лимит: 1.0s).\n"
        f"Подсказка: async def + асинхронный драйвер БД обрабатывают\n"
        f"конкурентные запросы в одном event loop без блокировок."
    )
