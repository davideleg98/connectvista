from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, engine

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def db() -> Session:
    """Each test runs inside a transaction that is rolled back afterwards,
    so tests never leave data behind in the dev database."""
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()
