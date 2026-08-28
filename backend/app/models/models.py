from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Administrator")

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    ip: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(120))
    password_enc: Mapped[str] = mapped_column(Text)
    port: Mapped[int] = mapped_column(Integer, default=443)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    vendor: Mapped[str] = mapped_column(String(50), default="MikroTik")
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    serial: Mapped[str | None] = mapped_column(String(120), nullable=True)
    routeros_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    firmware: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mac: Mapped[str | None] = mapped_column(String(64), nullable=True)
    uptime: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    health: Mapped[float] = mapped_column(Float, default=0)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_metrics: Mapped[dict] = mapped_column(JSON, default=dict)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    cpu: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory: Mapped[float | None] = mapped_column(Float, nullable=True)
    health: Mapped[float] = mapped_column(Float, default=0)
    wan_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    packet_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    dhcp_used: Mapped[float | None] = mapped_column(Float, nullable=True)

class Backup(Base):
    __tablename__ = "backups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
