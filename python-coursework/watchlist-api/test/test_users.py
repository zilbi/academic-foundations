"""
Тесты пользователей (5 баллов — часть блока users+reviews).
"""

import pytest


@pytest.fixture(scope="module")
def _data(client, seed_data):
    return seed_data


class TestUsers:
    """POST /users, GET /users/{id}."""

    def test_create_user(self, client):
        r = client.post("/users", json={
            "username": "testuser", "email": "testuser@test.com",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "testuser"
        assert "id" in data

    def test_create_user_duplicate_username(self, client):
        """Дубликат username -> 409."""
        client.post("/users", json={"username": "dup_user", "email": "dup1@test.com"})
        r = client.post("/users", json={"username": "dup_user", "email": "dup2@test.com"})
        assert r.status_code == 409

    def test_create_user_duplicate_email(self, client):
        """Дубликат email -> 409."""
        client.post("/users", json={"username": "emaildup1", "email": "same@test.com"})
        r = client.post("/users", json={"username": "emaildup2", "email": "same@test.com"})
        assert r.status_code == 409

    def test_create_user_missing_fields(self, client):
        r = client.post("/users", json={"username": "nomail"})
        assert r.status_code == 422

    def test_get_user(self, client, _data):
        uid = _data["users"]["alice"]
        r = client.get(f"/users/{uid}")
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "alice"

    def test_get_user_not_found(self, client):
        r = client.get("/users/99999")
        assert r.status_code == 404
