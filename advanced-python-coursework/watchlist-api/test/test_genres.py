"""
Тесты CRUD жанров (5 баллов).
"""


class TestGenres:
    """POST /genres, GET /genres."""

    def test_create_genre(self, client):
        r = client.post("/genres", json={"name": "horror"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "horror"
        assert "id" in data

    def test_create_genre_duplicate(self, client):
        """Повторный жанр с тем же именем -> 409."""
        client.post("/genres", json={"name": "test_dup"})
        r = client.post("/genres", json={"name": "test_dup"})
        assert r.status_code == 409

    def test_create_genre_empty_name(self, client):
        """Пустое имя -> 422."""
        r = client.post("/genres", json={"name": ""})
        assert r.status_code == 422

    def test_create_genre_no_body(self, client):
        """Без тела -> 422."""
        r = client.post("/genres")
        assert r.status_code == 422

    def test_list_genres(self, client):
        r = client.get("/genres")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all("id" in g and "name" in g for g in data)
