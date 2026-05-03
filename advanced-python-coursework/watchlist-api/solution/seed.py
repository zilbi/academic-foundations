import random
import sys

from solution.database import Base, SessionLocal, engine

try:
    from solution.models import Bookmark, Genre, Movie, Review, User
except ImportError:
    print("Ошибка: не удалось импортировать модели.")
    print("Убедитесь, что в solution/models.py определены:")
    print("  Genre, Movie, User, Review, Bookmark")
    sys.exit(1)


GENRES = ["action", "comedy", "drama", "sci_fi", "horror"]

MOVIES = [
    ("Inception", 2010, "sci_fi"),
    ("The Dark Knight", 2008, "action"),
    ("Interstellar", 2014, "sci_fi"),
    ("Parasite", 2019, "drama"),
    ("The Matrix", 1999, "sci_fi"),
    ("Pulp Fiction", 1994, "drama"),
    ("The Shawshank Redemption", 1994, "drama"),
    ("Fight Club", 1999, "drama"),
    ("Forrest Gump", 1994, "comedy"),
    ("The Grand Budapest Hotel", 2014, "comedy"),
    ("Whiplash", 2014, "drama"),
    ("Get Out", 2017, "horror"),
    ("Hereditary", 2018, "horror"),
    ("Mad Max: Fury Road", 2015, "action"),
    ("John Wick", 2014, "action"),
    ("Dune", 2021, "sci_fi"),
    ("Dune: Part Two", 2024, "sci_fi"),
    ("The Hangover", 2009, "comedy"),
    ("Superbad", 2007, "comedy"),
    ("Alien", 1979, "horror"),
]

USERS = [
    ("alice", "alice@example.com"),
    ("bob", "bob@example.com"),
    ("charlie", "charlie@example.com"),
    ("diana", "diana@example.com"),
    ("eve", "eve@example.com"),
]


def seed():
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        # Очистка (порядок важен из-за FK)
        session.query(Bookmark).delete()
        session.query(Review).delete()
        session.query(Movie).delete()
        session.query(Genre).delete()
        session.query(User).delete()
        session.commit()

        # Жанры
        genre_map = {}
        for name in GENRES:
            g = Genre(name=name)
            session.add(g)
            session.flush()
            genre_map[name] = g.id

        # Фильмы
        movie_ids = []
        for title, year, genre_name in MOVIES:
            m = Movie(title=title, year=year, genre_id=genre_map[genre_name])
            session.add(m)
            session.flush()
            movie_ids.append(m.id)

        # Пользователи
        user_ids = []
        for username, email in USERS:
            u = User(username=username, email=email)
            session.add(u)
            session.flush()
            user_ids.append(u.id)

        # Отзывы (случайные, но уникальные user+movie)
        random.seed(42)
        pairs = set()
        for _ in range(40):
            while True:
                uid = random.choice(user_ids)
                mid = random.choice(movie_ids)
                if (uid, mid) not in pairs:
                    pairs.add((uid, mid))
                    break
            r = Review(
                user_id=uid,
                movie_id=mid,
                rating=random.randint(1, 10),
                comment=random.choice([
                    "Great movie!", "Meh.", "Masterpiece!",
                    "Not my style.", "Would watch again.",
                    None,
                ]),
            )
            session.add(r)

        # Закладки
        bm_pairs = set()
        for _ in range(15):
            while True:
                uid = random.choice(user_ids)
                mid = random.choice(movie_ids)
                if (uid, mid) not in bm_pairs:
                    bm_pairs.add((uid, mid))
                    break
            b = Bookmark(
                user_id=uid,
                movie_id=mid,
                status=random.choice(["watched", "will_watch"]),
            )
            session.add(b)

        session.commit()

    print(f"Seed done: {len(GENRES)} genres, {len(MOVIES)} movies, "
          f"{len(USERS)} users, {len(pairs)} reviews, {len(bm_pairs)} bookmarks")


if __name__ == "__main__":
    seed()
