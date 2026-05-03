"""
Тесты закладок (15 баллов).
"""

import pytest


@pytest.fixture(scope="module")
def _data(client, seed_data):
    return seed_data


class TestCreateBookmark:
    """POST /bookmarks."""

    def test_create_bookmark_will_watch(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Inception"],
            "status": "will_watch",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "will_watch"
        assert "id" in data

    def test_create_bookmark_watched(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Parasite"],
            "status": "watched",
        })
        assert r.status_code == 201
        assert r.json()["status"] == "watched"

    def test_create_bookmark_duplicate(self, client, _data):
        """Дубликат (user + movie) -> 409."""
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Inception"],
            "status": "watched",
        })
        assert r.status_code == 409

    def test_create_bookmark_invalid_status(self, client, _data):
        """Невалидный status -> 422."""
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Whiplash"],
            "status": "maybe",
        })
        assert r.status_code == 422

    def test_create_bookmark_invalid_user(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": 99999,
            "movie_id": _data["movies"]["Inception"],
            "status": "watched",
        })
        assert r.status_code in (400, 404)

    def test_create_bookmark_invalid_movie(self, client, _data):
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["alice"],
            "movie_id": 99999,
            "status": "watched",
        })
        assert r.status_code in (400, 404)


class TestListBookmarks:
    """GET /users/{id}/bookmarks."""

    def test_list_bookmarks(self, client, _data):
        uid = _data["users"]["alice"]
        r = client.get(f"/users/{uid}/bookmarks")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_bookmarks_filter_status(self, client, _data):
        uid = _data["users"]["alice"]
        r = client.get(f"/users/{uid}/bookmarks", params={"status": "will_watch"})
        assert r.status_code == 200
        data = r.json()
        assert all(b["status"] == "will_watch" for b in data)

    def test_list_bookmarks_empty(self, client, _data):
        uid = _data["users"]["bob"]
        r = client.get(f"/users/{uid}/bookmarks")
        assert r.status_code == 200
        # bob может иметь 0 закладок
        assert isinstance(r.json(), list)

    def test_list_bookmarks_user_not_found(self, client):
        r = client.get("/users/99999/bookmarks")
        assert r.status_code == 404


class TestUpdateBookmark:
    """PATCH /bookmarks/{id}."""

    def test_update_bookmark_status(self, client, _data):
        # Создаём закладку для bob
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["bob"],
            "movie_id": _data["movies"]["Inception"],
            "status": "will_watch",
        })
        bm_id = r.json()["id"]

        # Меняем статус
        r = client.patch(f"/bookmarks/{bm_id}", json={"status": "watched"})
        assert r.status_code == 200
        assert r.json()["status"] == "watched"

    def test_update_bookmark_not_found(self, client):
        r = client.patch("/bookmarks/99999", json={"status": "watched"})
        assert r.status_code == 404

    def test_update_bookmark_invalid_status(self, client, _data):
        # Используем существующую закладку alice -> Inception
        uid = _data["users"]["alice"]
        r = client.get(f"/users/{uid}/bookmarks")
        bm = r.json()[0]
        r = client.patch(f"/bookmarks/{bm['id']}", json={"status": "maybe"})
        assert r.status_code == 422


class TestDeleteBookmark:
    """DELETE /bookmarks/{id}."""

    def test_delete_bookmark(self, client, _data):
        # Создаём и удаляем
        r = client.post("/bookmarks", json={
            "user_id": _data["users"]["bob"],
            "movie_id": _data["movies"]["Parasite"],
            "status": "will_watch",
        })
        bm_id = r.json()["id"]

        r = client.delete(f"/bookmarks/{bm_id}")
        assert r.status_code == 204

    def test_delete_bookmark_not_found(self, client):
        r = client.delete("/bookmarks/99999")
        assert r.status_code == 404
