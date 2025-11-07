from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from typing import Callable, Optional

_engine = None
_SessionFactory = None


def init_engine(database_uri: str, echo: bool = False):
    """
    Initialize SQLAlchemy engine and a scoped_session factory.

    - For sqlite in-memory URIs, create a fresh engine that uses StaticPool and
      check_same_thread=False so the single in-memory DB is sharable across
      threads (useful for threaded/async tests).
    - For other URIs, reuse a single engine/session factory.
    """
    global _engine, _SessionFactory

    if database_uri.startswith("sqlite:///:memory:"):
        # create a fresh engine for each call (tests call create_app repeatedly)
        engine = create_engine(
            database_uri,
            echo=echo,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _SessionFactory = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
        _engine = engine
        return _engine

    # non-memory DB: initialize once
    if _engine is None:
        _engine = create_engine(database_uri, echo=echo, future=True)
        _SessionFactory = scoped_session(sessionmaker(bind=_engine, autoflush=False, autocommit=False))
    return _engine


def get_session_factory(engine: Optional[object] = None) -> Callable[[], scoped_session]:
    """
    Return the scoped_session factory. Raises if init_engine not called.
    """
    global _SessionFactory
    if _SessionFactory is None:
        raise RuntimeError("Engine/session factory not initialized. Call init_engine first.")
    return _SessionFactory


def get_db_session():
    """
    Convenience: return a session instance from the scoped factory.
    Caller should call session.close() when done.
    """
    if _SessionFactory is None:
        raise RuntimeError("Session factory not initialized.")
    return _SessionFactory()
