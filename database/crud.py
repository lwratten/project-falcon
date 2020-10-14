from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .config import DATABASE_URI
from .models import Base

engine = create_engine(DATABASE_URI)

# Global Session object factory.
# Create new sessions using Session(), which is done for you in session_scope() below.
Session = sessionmaker(bind=engine)

# Import session_scope to use the database.
# Doing so will run the above engine binding and create the global Session.
# Use it by "with session_scope() as session:"
@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Creates the database tables. Usually only done once.
def create_database():
    Base.metadata.create_all(engine)

# Recreate database will destroy the database and re-build it with empty tables (use only for development).
def recreate_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
