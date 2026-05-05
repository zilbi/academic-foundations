# Watchlist API

## Overview

A Python backend coursework project implementing a REST API for a personal movie watchlist service. The project models genres, movies, users, reviews, and per-user bookmarks, then exposes them through FastAPI endpoints backed by PostgreSQL and SQLAlchemy.

## Project highlights

- FastAPI REST endpoints for genres, movies, users, reviews, and bookmarks
- SQLAlchemy ORM models for a normalized relational schema
- PostgreSQL-backed persistence
- Pydantic schemas for request validation and structured responses
- Database-level constraints for uniqueness, foreign keys, rating ranges, and bookmark status values
- Aggregate rating logic for movie details and top-movie rankings
- Automated HTTP tests for API behavior, constraints, bookmarks, reviews, users, movies, and performance

## What this project demonstrates

- Python backend engineering
- REST API design and endpoint organization
- Relational data modeling with per-user bookmark state
- Validation of input and output data with Pydantic
- Structured handling of invalid input, missing entities, and duplicate data
- Query logic for filtering, averages, review counts, and rankings
- Read-oriented optimization through cached catalogue endpoints protected by a lock

## How to run

The original project expects PostgreSQL and a database named `watchlist`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
createdb watchlist
make run
```

Equivalent server command:

```bash
uvicorn solution.main:app --reload
```

## How to test

With PostgreSQL available and the service dependencies installed:

```bash
make test
```

Equivalent test command:

```bash
pytest test -s
```

## Implementation note

This directory contains the original Advanced Python homework implementation. The source code and tests were preserved without refactoring; only public portfolio presentation files were added.

## Original assignment scope

The homework required implementing a Watchlist REST API with:

- genre creation and listing;
- movie CRUD, filtering by year and genre, average ratings, and top-movie rankings;
- user creation and lookup;
- reviews with one review per user/movie pair and ratings from 1 to 10;
- bookmarks with per-user `watched` or `will_watch` state;
- proper HTTP error handling for invalid data, missing entities, duplicates, and database constraints;
- performance-oriented tests for concurrent read requests.
