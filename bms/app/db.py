from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Callable

_engine = None
_SessionFactory = None

def init_engine(database_uri: str, echo: bool = False):
    """
    Initialize SQLAlchemy engine and a scoped_session factory.
    Returns the engine.
    """
    global _engine, _SessionFactory
    if _engine is None:
        _engine = create_engine(database_uri, echo=echo, future=True)
        _SessionFactory = scoped_session(sessionmaker(bind=_engine, autoflush=False, autocommit=False))
    return _engine


def get_session_factory(engine=None) -> Callable[[], scoped_session]:
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
    Caller should call session.close() (or session.remove() on the factory) when done.
    """
    if _SessionFactory is None:
        raise RuntimeError("Session factory not initialized.")
    return _SessionFactory()
