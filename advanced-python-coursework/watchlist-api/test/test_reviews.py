"""
Тесты отзывов (15 баллов — часть блока users+reviews).
"""

import pytest


@pytest.fixture(scope="module")
def _data(client, seed_data):
    return seed_data


class TestCreateReview:
    """POST /reviews."""

    def test_create_review(self, client, _data):
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Inception"],
            "rating": 9,
            "comment": "Masterpiece!",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["rating"] == 9
        assert data["comment"] == "Masterpiece!"
        assert "id" in data

    def test_create_review_no_comment(self, client, _data):
        """comment — необязательное поле."""
        r = client.post("/reviews", json={
            "user_id": _data["users"]["bob"],
            "movie_id": _data["movies"]["Inception"],
            "rating": 7,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["comment"] is None or "comment" not in data or data["comment"] == ""

    def test_create_review_duplicate(self, client, _data):
        """Повторный отзыв (тот же user + movie) -> 409."""
        payload = {
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Inception"],
            "rating": 8,
        }
        # Первый уже создан в test_create_review
        r = client.post("/reviews", json=payload)
        assert r.status_code == 409

    def test_create_review_invalid_rating_low(self, client, _data):
        """rating < 1 -> 422."""
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Parasite"],
            "rating": 0,
        })
        assert r.status_code == 422

    def test_create_review_invalid_rating_high(self, client, _data):
        """rating > 10 -> 422."""
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": _data["movies"]["Parasite"],
            "rating": 11,
        })
        assert r.status_code == 422

    def test_create_review_invalid_user(self, client, _data):
        """Несуществующий user -> 404."""
        r = client.post("/reviews", json={
            "user_id": 99999,
            "movie_id": _data["movies"]["Inception"],
            "rating": 5,
        })
        assert r.status_code in (400, 404)

    def test_create_review_invalid_movie(self, client, _data):
        """Несуществующий movie -> 404."""
        r = client.post("/reviews", json={
            "user_id": _data["users"]["alice"],
            "movie_id": 99999,
            "rating": 5,
        })
        assert r.status_code in (400, 404)


class TestListReviews:
    """GET /movies/{id}/reviews."""

    def test_list_reviews(self, client, _data):
        mid = _data["movies"]["Inception"]
        r = client.get(f"/movies/{mid}/reviews")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # alice и bob

    def test_list_reviews_empty(self, client, _data):
        """Фильм без отзывов -> пустой список."""
        mid = _data["movies"]["Whiplash"]
        r = client.get(f"/movies/{mid}/reviews")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_reviews_not_found(self, client):
        """Несуществующий фильм -> 404."""
        r = client.get("/movies/99999/reviews")
        assert r.status_code == 404


class TestMovieWithAvgRating:
    """GET /movies/{id} должен содержать avg_rating."""

    def test_movie_has_avg_rating(self, client, _data):
        mid = _data["movies"]["Inception"]
        r = client.get(f"/movies/{mid}")
        assert r.status_code == 200
        data = r.json()
        assert "avg_rating" in data
        # alice: 9, bob: 7 -> avg = 8.0
        assert data["avg_rating"] == pytest.approx(8.0, abs=0.1)

    def test_movie_no_reviews_avg_null(self, client, _data):
        """Фильм без отзывов -> avg_rating = null."""
        mid = _data["movies"]["Whiplash"]
        r = client.get(f"/movies/{mid}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("avg_rating") is None


class TestMoviesTop:
    """GET /movies/top — топ по среднему рейтингу."""

    def test_movies_top(self, client, _data):
        r = client.get("/movies/top")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

        # Проверяем, что отсортировано по убыванию avg_rating
        ratings = [m["avg_rating"] for m in data if m["avg_rating"] is not None]
        assert ratings == sorted(ratings, reverse=True)

    def test_movies_top_limit(self, client, _data):
        r = client.get("/movies/top", params={"limit": 2})
        assert r.status_code == 200
        data = r.json()
        assert len(data) <= 2

    def test_movies_top_has_reviews_count(self, client, _data):
        """Каждый фильм в топе содержит reviews_count."""
        r = client.get("/movies/top")
        assert r.status_code == 200
        data = r.json()
        if data:
            assert "reviews_count" in data[0]
            assert isinstance(data[0]["reviews_count"], int)
