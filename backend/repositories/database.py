"""Database setup — SQLite for dev, swappable to Alibaba Cloud RDS via DATABASE_URL."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, Float, DateTime, String, JSON
import datetime

from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class DisputeRow(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(String, index=True)
    dispute_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    buyer_id: Mapped[str] = mapped_column(String)
    seller_id: Mapped[str] = mapped_column(String)
    buyer_narrative: Mapped[str] = mapped_column(Text)
    seller_narrative: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class CaseFileRow(Base):
    __tablename__ = "case_files"

    dispute_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_value: Mapped[float] = mapped_column(Float)
    case_json: Mapped[dict] = mapped_column(JSON)
    assembled_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class DecisionRow(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    dispute_id: Mapped[str] = mapped_column(String, index=True)
    gate_result: Mapped[str] = mapped_column(String)
    resolution: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    actor: Mapped[str] = mapped_column(String)
    decision_json: Mapped[dict] = mapped_column(JSON)
    decided_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class HumanQueueRow(Base):
    __tablename__ = "human_queue"

    decision_id: Mapped[str] = mapped_column(String, primary_key=True)
    dispute_id: Mapped[str] = mapped_column(String, index=True)
    brief_json: Mapped[dict] = mapped_column(JSON)
    resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class AuditRow(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    dispute_id: Mapped[str] = mapped_column(String, index=True)
    event: Mapped[str] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str] = mapped_column(String, nullable=True)
    data_json: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
