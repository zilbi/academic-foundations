"""
Тесты CRUD фильмов (20 баллов).
"""

import pytest


@pytest.fixture(scope="module")
def _data(client, seed_data):
    return seed_data


class TestCreateMovie:
    """POST /movies."""

    def test_create_movie(self, client, _data):
        r = client.post("/movies", json={
            "title": "Dune", "year": 2021, "genre_id": _data["genres"]["action"],
        })
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Dune"
        assert data["year"] == 2021
        assert "id" in data

    def test_create_movie_invalid_genre(self, client):
        """FK на несуществующий жанр -> 404 или 400."""
        r = client.post("/movies", json={
            "title": "Ghost", "year": 2020, "genre_id": 99999,
        })
        assert r.status_code in (400, 404)

    def test_create_movie_missing_title(self, client, _data):
        """Без title -> 422."""
        r = client.post("/movies", json={
            "year": 2020, "genre_id": _data["genres"]["action"],
        })
        assert r.status_code == 422

    def test_create_movie_missing_year(self, client, _data):
        """Без year -> 422."""
        r = client.post("/movies", json={
            "title": "NoYear", "genre_id": _data["genres"]["action"],
        })
        assert r.status_code == 422


class TestReadMovies:
    """GET /movies, GET /movies/{id}."""

    def test_list_movies(self, client, _data):
        r = client.get("/movies")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_filter_by_year(self, client, _data):
        r = client.get("/movies", params={"year": 2014})
        assert r.status_code == 200
        data = r.json()
        assert all(m["year"] == 2014 for m in data)

    def test_filter_by_genre(self, client, _data):
        genre_id = _data["genres"]["drama"]
        r = client.get("/movies", params={"genre_id": genre_id})
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2
        assert all(m["genre_id"] == genre_id for m in data)

    def test_filter_by_year_and_genre(self, client, _data):
        genre_id = _data["genres"]["action"]
        r = client.get("/movies", params={"year": 2010, "genre_id": genre_id})
        assert r.status_code == 200
        data = r.json()
        assert all(m["year"] == 2010 and m["genre_id"] == genre_id for m in data)

    def test_get_movie_by_id(self, client, _data):
        mid = _data["movies"]["Inception"]
        r = client.get(f"/movies/{mid}")
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Inception"
        assert data["id"] == mid

    def test_get_movie_not_found(self, client):
        r = client.get("/movies/99999")
        assert r.status_code == 404


class TestUpdateMovie:
    """PATCH /movies/{id}."""

    def test_update_movie(self, client, _data):
        mid = _data["movies"]["Inception"]
        r = client.patch(f"/movies/{mid}", json={"title": "Inception (2010)"})
        assert r.status_code == 200
        assert r.json()["title"] == "Inception (2010)"

        # Вернём обратно
        client.patch(f"/movies/{mid}", json={"title": "Inception"})

    def test_update_movie_not_found(self, client):
        r = client.patch("/movies/99999", json={"title": "X"})
        assert r.status_code == 404


class TestDeleteMovie:
    """DELETE /movies/{id}."""

    def test_delete_movie(self, client, _data):
        # Создаём фильм для удаления
        r = client.post("/movies", json={
            "title": "ToDelete", "year": 2020,
            "genre_id": _data["genres"]["comedy"],
        })
        mid = r.json()["id"]

        r = client.delete(f"/movies/{mid}")
        assert r.status_code == 204

        r = client.get(f"/movies/{mid}")
        assert r.status_code == 404

    def test_delete_movie_not_found(self, client):
        r = client.delete("/movies/99999")
        assert r.status_code == 404
