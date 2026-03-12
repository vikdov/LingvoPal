import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# 1. Path Setup
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(basedir, 'db.sqlite')}"

# 2. Engine & Connection Pooling
# For SQLite, we often use StaticPool if using in-memory,
# but for a file, the default QueuePool is fine.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite + Multi-threading
    pool_size=5,  # Max connections in pool
    max_overflow=10,  # Extra connections if pool is full
)

# 3. Session Management
# sessionmaker is a factory for Session objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
