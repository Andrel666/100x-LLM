"""
Database connection and session management for AEO Tracker
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from ..config import DATABASE_PATH
from .models import Base

# Create database engine
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Initialize the database - create all tables"""
    Base.metadata.create_all(bind=engine)
    return True


def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    return True


@contextmanager
def get_db():
    """
    Context manager for database sessions.

    Usage:
        with get_db() as db:
            db.query(Brand).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_session():
    """
    Get a new database session.
    Caller is responsible for closing the session.
    """
    return SessionLocal()
