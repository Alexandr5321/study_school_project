import os

import psycopg2
from flask import g
from psycopg2.extras import RealDictCursor


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)
    return g.db


def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()
