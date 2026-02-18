"""Database models — SQLAlchemy ORM for PostgreSQL via Supabase."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    avatar_url = Column(Text)
    plan = Column(String(50), default="free", nullable=False)
    entries_this_month = Column(Integer, default=0)
    month_reset_at = Column(DateTime, default=datetime.utcnow)

    # OAuth
    github_id = Column(String(100), unique=True, nullable=True)
    google_id = Column(String(100), unique=True, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    chains = relationship("Chain", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), default="Default")
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False)  # pv_live_ or pv_test_
    scopes = Column(JSON, default=["read", "write"])
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="api_keys")


class Chain(Base):
    __tablename__ = "chains"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=[])
    chain_type = Column(String(50), default="custom")
    length = Column(Integer, default=0)
    root_xy = Column(String(67))
    head_xy = Column(String(67))
    head_y = Column(String(64))
    auto_redact = Column(Boolean, default=True)
    share_id = Column(String(36), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="chains")
    entries = relationship("Entry", back_populates="chain", cascade="all, delete-orphan",
                           order_by="Entry.index")
    checkpoints = relationship("ChainCheckpoint", back_populates="chain", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="chain", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chains_user_id", "user_id"),
    )


class Entry(Base):
    __tablename__ = "entries"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    chain_id = Column(String(36), ForeignKey("chains.id"), nullable=False)
    index = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    operation = Column(String(255), nullable=False)
    x = Column(String(64), nullable=False)
    y = Column(String(64), nullable=False)
    xy = Column(String(67), nullable=False)
    x_state = Column(JSON)
    y_state = Column(JSON)
    status = Column(String(20), default="success")
    verified = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default={})
    signature = Column(Text)
    signer_id = Column(String(255))
    public_key = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    chain = relationship("Chain", back_populates="entries")

    __table_args__ = (
        Index("idx_entries_chain_index", "chain_id", "index", unique=True),
    )


class ChainCheckpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    chain_id = Column(String(36), ForeignKey("chains.id"), nullable=False)
    name = Column(String(255), nullable=False)
    entry_index = Column(Integer, nullable=False)
    snapshot_data = Column(JSON)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    chain = relationship("Chain", back_populates="checkpoints")

    __table_args__ = (
        Index("idx_checkpoints_chain_id", "chain_id"),
    )


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    chain_id = Column(String(36), ForeignKey("chains.id"), nullable=False)
    task = Column(Text, nullable=False)
    started = Column(Float)
    completed = Column(Float)
    duration = Column(Float)
    entry_count = Column(Integer)
    first_x = Column(String(64))
    final_y = Column(String(64))
    root_xy = Column(String(67))
    head_xy = Column(String(67))
    all_verified = Column(Boolean, default=True)
    all_signatures_valid = Column(Boolean, default=True)
    receipt_hash = Column(String(64))
    agent_type = Column(String(100))
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime, default=func.now(), nullable=False)

    chain = relationship("Chain", back_populates="receipts")

    __table_args__ = (
        Index("idx_receipts_chain_id", "chain_id"),
    )


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    url = Column(Text, nullable=False)
    events = Column(JSON, default=["chain.created", "entry.appended"])
    secret = Column(String(64))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="webhooks")

    __table_args__ = (
        Index("idx_webhooks_user_id", "user_id"),
    )


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    status = Column(String(20), default="completed")
    chain_id = Column(String(36), nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    findings = Column(JSON, default=[])
    receipt_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_scan_results_user_id", "user_id"),
    )


# ──── Database Engine with Connection Pooling ────


def get_engine(database_url: str, pool_size: int = 10, max_overflow: int = 20):
    """Create a SQLAlchemy engine with connection pooling.

    Args:
        database_url: PostgreSQL connection string (or sqlite for testing).
        pool_size: Number of connections to maintain in the pool.
        max_overflow: Max connections beyond pool_size allowed temporarily.
    """
    # Pool settings only apply to PostgreSQL; SQLite uses SingletonThreadPool
    if database_url.startswith("sqlite"):
        return create_engine(database_url, echo=False)
    return create_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False,
    )


def get_session_factory(database_url: str, pool_size: int = 10) -> sessionmaker:
    """Create a session factory with connection pooling."""
    engine = get_engine(database_url, pool_size=pool_size)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db(session_factory: sessionmaker):
    """Dependency that yields a database session."""
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
