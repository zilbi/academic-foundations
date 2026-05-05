from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from psycopg2 import errorcodes
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from solution import schemas
from solution.database import SessionLocal, engine
from solution.models import Base, Bookmark, Genre, Movie, Review, User

app = FastAPI(title="Watchlist API")
Base.metadata.create_all(bind=engine)


@dataclass
class ReadCache:
    genres: list[schemas.GenreRead] = field(default_factory=list)
    movies: list[schemas.MovieRead] = field(default_factory=list)
    top_movies: list[schemas.MovieTopRead] = field(default_factory=list)
    lock: RLock = field(default_factory=RLock)


cache = ReadCache()


def _clone_models(items):
    return [item.model_copy(deep=True) for item in items]


def _movie_to_read(movie: Movie) -> schemas.MovieRead:
    return schemas.MovieRead.model_validate(movie, from_attributes=True)


def _refresh_genres_cache(session) -> None:
    items = session.execute(select(Genre).order_by(Genre.id)).scalars().all()
    with cache.lock:
        cache.genres = [schemas.GenreRead.model_validate(item, from_attributes=True) for item in items]


def _refresh_movies_cache(session) -> None:
    items = session.execute(select(Movie).order_by(Movie.id)).scalars().all()
    with cache.lock:
        cache.movies = [_movie_to_read(item) for item in items]


def _refresh_top_movies_cache(session) -> None:
    rows = session.execute(
        select(
            Movie.id,
            Movie.title,
            Movie.year,
            Movie.genre_id,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("reviews_count"),
        )
        .join(Review, Review.movie_id == Movie.id)
        .group_by(Movie.id)
        .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc(), Movie.id.asc())
    ).all()

    with cache.lock:
        cache.top_movies = [
            schemas.MovieTopRead(
                id=row.id,
                title=row.title,
                year=row.year,
                genre_id=row.genre_id,
                avg_rating=float(row.avg_rating) if row.avg_rating is not None else None,
                reviews_count=row.reviews_count,
            )
            for row in rows
        ]


def _refresh_all_read_caches() -> None:
    with SessionLocal() as session:
        _refresh_genres_cache(session)
        _refresh_movies_cache(session)
        _refresh_top_movies_cache(session)


@app.on_event("startup")
def startup() -> None:
    _refresh_all_read_caches()


def _raise_integrity_error(exc: IntegrityError) -> None:
    pgcode = getattr(getattr(exc, "orig", None), "pgcode", None)
    if pgcode == errorcodes.UNIQUE_VIOLATION:
        raise HTTPException(status_code=409, detail="duplicate value")
    if pgcode == errorcodes.FOREIGN_KEY_VIOLATION:
        raise HTTPException(status_code=400, detail="referenced entity not found")
    if pgcode == errorcodes.CHECK_VIOLATION:
        raise HTTPException(status_code=400, detail="invalid data")
    raise HTTPException(status_code=400, detail="database constraint error")


@app.get("/genres", response_model=list[schemas.GenreRead], status_code=200)
async def list_genres():
    with cache.lock:
        return _clone_models(cache.genres)


@app.post("/genres", response_model=schemas.GenreRead, status_code=201)
async def create_genre(data: schemas.GenreCreate):
    with SessionLocal() as session:
        thing = Genre(name=data.name)
        session.add(thing)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        _refresh_genres_cache(session)
        return thing


@app.post("/movies", response_model=schemas.MovieRead, status_code=201)
async def create_movie(data: schemas.MovieCreate):
    with SessionLocal() as session:
        genre = session.get(Genre, data.genre_id)
        if genre is None:
            raise HTTPException(status_code=404, detail="genre not found")

        thing = Movie(title=data.title, year=data.year, genre_id=data.genre_id)
        session.add(thing)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        _refresh_movies_cache(session)
        _refresh_top_movies_cache(session)
        return thing


@app.get("/movies", response_model=list[schemas.MovieRead], status_code=200)
async def list_movies(
    year: Optional[int] = None,
    genre_id: Optional[int] = None,
):
    with cache.lock:
        items = _clone_models(cache.movies)
    if year is not None:
        items = [item for item in items if item.year == year]
    if genre_id is not None:
        items = [item for item in items if item.genre_id == genre_id]
    return items


@app.get("/movies/top", response_model=list[schemas.MovieTopRead], status_code=200)
async def top_movies(limit: int = Query(default=10, ge=1)):
    with cache.lock:
        return _clone_models(cache.top_movies[:limit])


@app.get("/movies/{id}", response_model=schemas.MovieWithRatingRead, status_code=200)
async def get_movie(id: int):
    with SessionLocal() as session:
        row = session.execute(
            select(
                Movie.id,
                Movie.title,
                Movie.year,
                Movie.genre_id,
                func.avg(Review.rating).label("avg_rating"),
            )
            .outerjoin(Review, Review.movie_id == Movie.id)
            .where(Movie.id == id)
            .group_by(Movie.id)
        ).first()

        if row is None:
            raise HTTPException(status_code=404, detail="movie not found")

        return schemas.MovieWithRatingRead(
            id=row.id,
            title=row.title,
            year=row.year,
            genre_id=row.genre_id,
            avg_rating=float(row.avg_rating) if row.avg_rating is not None else None,
        )


@app.patch("/movies/{id}", response_model=schemas.MovieRead, status_code=200)
async def update_movie(id: int, data: schemas.MovieUpdate):
    with SessionLocal() as session:
        thing = session.get(Movie, id)
        if thing is None:
            raise HTTPException(status_code=404, detail="movie not found")

        if data.genre_id is not None:
            genre = session.get(Genre, data.genre_id)
            if genre is None:
                raise HTTPException(status_code=404, detail="genre not found")
            thing.genre_id = data.genre_id

        if data.title is not None:
            thing.title = data.title
        if data.year is not None:
            thing.year = data.year

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        _refresh_movies_cache(session)
        _refresh_top_movies_cache(session)
        return thing


@app.delete("/movies/{id}", status_code=204)
async def delete_movie(id: int):
    with SessionLocal() as session:
        thing = session.get(Movie, id)
        if thing is None:
            raise HTTPException(status_code=404, detail="movie not found")

        session.delete(thing)
        session.commit()
        _refresh_movies_cache(session)
        _refresh_top_movies_cache(session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/users", response_model=schemas.UserRead, status_code=201)
async def create_user(data: schemas.UserCreate):
    with SessionLocal() as session:
        thing = User(username=data.username, email=data.email)
        session.add(thing)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        return thing


@app.get("/users/{id}", response_model=schemas.UserRead, status_code=200)
async def get_user(id: int):
    with SessionLocal() as session:
        thing = session.get(User, id)
        if thing is None:
            raise HTTPException(status_code=404, detail="user not found")
        return thing

@app.post("/reviews", response_model=schemas.ReviewRead, status_code=201)
async def create_review(data: schemas.ReviewCreate):
    with SessionLocal() as session:
        user = session.get(User, data.user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")

        movie = session.get(Movie, data.movie_id)
        if movie is None:
            raise HTTPException(status_code=404, detail="movie not found")

        thing = Review(
            user_id=data.user_id,
            movie_id=data.movie_id,
            rating=data.rating,
            comment=data.comment,
        )
        session.add(thing)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        _refresh_top_movies_cache(session)
        return thing


@app.get("/movies/{id}/reviews", response_model=list[schemas.ReviewRead], status_code=200)
async def list_movie_reviews(id: int):
    with SessionLocal() as session:
        movie = session.get(Movie, id)
        if movie is None:
            raise HTTPException(status_code=404, detail="movie not found")

        return session.execute(select(Review).where(Review.movie_id == id).order_by(Review.id)).scalars().all()



@app.post("/bookmarks", response_model=schemas.BookmarkRead, status_code=201)
async def create_bookmark(data: schemas.BookmarkCreate):
    with SessionLocal() as session:
        user = session.get(User, data.user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")

        movie = session.get(Movie, data.movie_id)
        if movie is None:
            raise HTTPException(status_code=404, detail="movie not found")

        thing = Bookmark(user_id=data.user_id, movie_id=data.movie_id, status=data.status)
        session.add(thing)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        return thing


@app.get("/users/{id}/bookmarks", response_model=list[schemas.BookmarkRead], status_code=200)
async def list_user_bookmarks(
    id: int,
    status: Optional[schemas.BookmarkStatus] = None,
):
    with SessionLocal() as session:
        user = session.get(User, id)
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")

        query = select(Bookmark).where(Bookmark.user_id == id).order_by(Bookmark.id)
        if status is not None:
            query = query.where(Bookmark.status == status)
        return session.execute(query).scalars().all()


@app.patch("/bookmarks/{id}", response_model=schemas.BookmarkRead, status_code=200)
async def update_bookmark(id: int, data: schemas.BookmarkUpdate):
    with SessionLocal() as session:
        thing = session.get(Bookmark, id)
        if thing is None:
            raise HTTPException(status_code=404, detail="bookmark not found")

        if data.status is not None:
            thing.status = data.status

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            _raise_integrity_error(exc)

        session.refresh(thing)
        return thing


@app.delete("/bookmarks/{id}", status_code=204)
async def delete_bookmark(id: int):
    with SessionLocal() as session:
        thing = session.get(Bookmark, id)
        if thing is None:
            raise HTTPException(status_code=404, detail="bookmark not found")

        session.delete(thing)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
