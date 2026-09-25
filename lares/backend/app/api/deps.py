from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.db import get_db as _get_db

get_db = _get_db
