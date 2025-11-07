from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from typing import Callable, Optional

_engine = None
_SessionFactory = None


def init_engine(database_uri: str, echo: bool = False):
    
    global _engine, _SessionFactory

    if database_uri.startswith("sqlite:///:memory:"):
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
