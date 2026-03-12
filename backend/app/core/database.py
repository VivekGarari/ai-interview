from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

# Use sync psycopg2 engine
SYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
).replace(
    "postgresql+psycopg2+psycopg2", "postgresql+psycopg2"
)

engine = create_engine(SYNC_DATABASE_URL, echo=settings.DEBUG)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def create_tables():
    from app.models.users import User
    from app.models.session import InterviewSession, SessionQuestion
    from app.models.submission import CodingProblem, CodeSubmission
    Base.metadata.create_all(bind=engine)