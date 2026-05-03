from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
BookmarkStatus = Literal["watched", "will_watch"]


class GenreCreate(BaseModel):
    name: NonEmptyStr


class GenreRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    title: NonEmptyStr
    year: int
    genre_id: int


class MovieRead(BaseModel):
    id: int
    title: str
    year: int
    genre_id: int

    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    title: Optional[NonEmptyStr] = None
    year: Optional[int] = None
    genre_id: Optional[int] = None


class MovieWithRatingRead(BaseModel):
    id: int
    title: str
    year: int
    genre_id: int
    avg_rating: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class MovieTopRead(BaseModel):
    id: int
    title: str
    year: int
    genre_id: int
    avg_rating: Optional[float]
    reviews_count: int

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: NonEmptyStr
    email: NonEmptyStr


class UserRead(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    user_id: int
    movie_id: int
    rating: int = Field(ge=1, le=10)
    comment: Optional[str] = None


class ReviewRead(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: int
    comment: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BookmarkCreate(BaseModel):
    user_id: int
    movie_id: int
    status: BookmarkStatus


class BookmarkRead(BaseModel):
    id: int
    user_id: int
    movie_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class BookmarkUpdate(BaseModel):
    status: Optional[BookmarkStatus] = None
