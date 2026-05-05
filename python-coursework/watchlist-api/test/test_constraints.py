"""
Тесты ограничений БД (10 баллов).

Проверяем, что сервер корректно обрабатывает:
  - FK violations (ссылка на несуществующую сущность)
  - UNIQUE violations (дубликаты)
  - CHECK violations (невалидные значения)
"""

import pytest


@pytest.fixture(scope="module")
def _data(client, seed_data):
    return seed_data


class TestForeignKeyConstraints:
    """FK -> 404 или 400, но НЕ 500."""

    def test_movie_invalid_genre_fk(self, client):
        r = client.post("/movies", json={
            "title": "FK Test", "year": 2020, "genre_id": 99999,
        })
        assert r.status_code in (400, 404), (
            f"FK violation должен вернуть 400 или 404, получили {r.status_code}"
        )

    def test_review_invalid_user_fk(self, client, _data):
        r = client.post("/reviews", json={
            "user_id": 99999,
            "movie_id": _data["movies"]["Inception"],
            "rating": 5,
        })
        assert r.status_code in (400, 404)

    def test_review_invalid_movie_fk(self, client, _data):
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": 99999,
            "rating": 5,
        })
        assert r.status_code in (400, 404)

    def test_bookmark_invalid_user_fk(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": 99999,
            "movie_id": _data["movies"]["Inception"],
            "status": "watched",
        })
        assert r.status_code in (400, 404)

    def test_bookmark_invalid_movie_fk(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["alice"],
            "movie_id": 99999,
            "status": "watched",
        })
        assert r.status_code in (400, 404)


class TestUniqueConstraints:
    """UNIQUE violation -> 409, но НЕ 500."""

    def test_genre_duplicate_name(self, client):
        client.post("/genres", json={"name": "unique_test"})
        r = client.post("/genres", json={"name": "unique_test"})
        assert r.status_code == 409, (
            f"UNIQUE violation должен вернуть 409, получили {r.status_code}"
        )

    def test_user_duplicate_username(self, client):
        client.post("/users", json={"username": "uniq_u", "email": "u1@test.com"})
        r = client.post("/users", json={"username": "uniq_u", "email": "u2@test.com"})
        assert r.status_code == 409

    def test_user_duplicate_email(self, client):
        client.post("/users", json={"username": "uniq_e1", "email": "uniq@test.com"})
        r = client.post("/users", json={"username": "uniq_e2", "email": "uniq@test.com"})
        assert r.status_code == 409


class TestCheckConstraints:
    """Невалидные данные -> 422, но НЕ 500."""

    def test_review_rating_zero(self, client, _data):
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Whiplash"],
            "rating": 0,
        })
        assert r.status_code == 422

    def test_review_rating_eleven(self, client, _data):
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Whiplash"],
            "rating": 11,
        })
        assert r.status_code == 422

    def test_bookmark_invalid_status(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["bob"],
            "movie_id": _data["movies"]["Whiplash"],
            "status": "dunno",
        })
        assert r.status_code == 422


class TestNoInternalServerErrors:
    """
    Ни один из вышеперечисленных тестов не должен
    возвращать 500. Если вы видите 500 — ловите
    исключения от БД и возвращайте нормальный HTTP-код.
    """

    def test_no_500_on_fk_violation(self, client):
        r = client.post("/movies", json={
            "title": "Test", "year": 2020, "genre_id": 99999,
        })
        assert r.status_code != 500, (
            "Сервер вернул 500 вместо корректного HTTP-кода ошибки. "
            "Ловите IntegrityError и возвращайте 400/404/409."
        )

    def test_no_500_on_unique_violation(self, client):
        client.post("/genres", json={"name": "no500_test"})
        r = client.post("/genres", json={"name": "no500_test"})
        assert r.status_code != 500, (
            "Сервер вернул 500 вместо 409. "
            "Ловите IntegrityError и возвращайте 409."
        )
