from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


def add_otp_columns():
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS otp_code VARCHAR(6),
            ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMPTZ
        """))
        conn.commit()
        print("OTP columns added!")


def add_model_answer_column():
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE session_questions
            ADD COLUMN IF NOT EXISTS model_answer TEXT
        """))
        conn.commit()
        print("model_answer column added!")