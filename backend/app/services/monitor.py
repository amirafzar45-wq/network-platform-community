import os, statistics, subprocess, time
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.db import SessionLocal
from app.models import Device, Metric, Alert
from app.services.crypto import decrypt
from app.vendors.mikrotik import MikroTikProvider
from app.services.notifications import notify_telegram


def ping(host: str) -> tuple[float | None, float]:
    try:
        started = time.perf_counter()
        p = subprocess.run(['ping', '-c', '2', '-W', '2', host], capture_output=True, text=True, timeout=6)
        latency = (time.perf_counter() - started) * 1000 / 2
        loss = 100.0 if p.returncode != 0 else 0.0
        for line in p.stdout.splitlines():
            if 'packet loss' in line:
                try: loss = float(line.split('%')[0].split()[-1])
                except Exception: pass
        return latency, loss
    except Exception:
        return None, 100.0


def health_score(snapshot: dict, latency: float | None, packet_loss: float) -> float:
    score = 100.0
    cpu = float(snapshot.get('cpu', 0)); mem = float(snapshot.get('memory', 0))
    if cpu > 90: score -= 25
    elif cpu > 80: score -= 10
    if mem > 90: score -= 25
    elif mem > 80: score -= 10
    if packet_loss > 5: score -= 20
    elif packet_loss > 1: score -= 8
    if latency is None: score -= 30
    elif latency > 150: score -= 12
    return max(0, min(100, round(score, 1)))


def upsert_alert(db, device, severity, title, message):
    existing = db.scalar(select(Alert).where(Alert.device_id == device.id, Alert.title == title, Alert.active == True))
    if existing: return
    alert = Alert(device_id=device.id, severity=severity, title=title, message=message)
    db.add(alert); db.commit()
    notify_telegram(f'🚨 {severity.upper()}\n{device.name}\n{title}\n{message}')


def resolve_alert(db, device, title):
    existing = db.scalar(select(Alert).where(Alert.device_id == device.id, Alert.title == title, Alert.active == True))
    if existing:
        existing.active = False; existing.resolved_at = datetime.now(timezone.utc); db.commit()


def collect_device(device: Device):
    db = SessionLocal()
    try:
        provider = MikroTikProvider(device.ip, device.username, decrypt(device.password_enc), device.port, device.use_ssl)
        snapshot = provider.get_snapshot()
        latency, loss = ping(device.ip)
        score = health_score(snapshot, latency, loss)
        device.status = 'online'; device.last_seen = datetime.now(timezone.utc); device.health = score
        device.model = snapshot.get('model'); device.serial = snapshot.get('serial'); device.routeros_version = snapshot.get('routeros_version')
        device.uptime = snapshot.get('uptime'); device.last_metrics = {'latency_ms': latency, 'packet_loss': loss, **snapshot}
        db.add(Metric(device_id=device.id, cpu=snapshot.get('cpu'), memory=snapshot.get('memory'), health=score,
                      wan_latency_ms=latency, packet_loss=loss))
        if snapshot.get('cpu', 0) > 90: upsert_alert(db, device, 'critical', 'High CPU', f"CPU is {snapshot.get('cpu')}%")
        else: resolve_alert(db, device, 'High CPU')
        if snapshot.get('memory', 0) > 90: upsert_alert(db, device, 'critical', 'High Memory', f"Memory usage is {snapshot.get('memory'):.1f}%")
        else: resolve_alert(db, device, 'High Memory')
        if loss > 5: upsert_alert(db, device, 'critical', 'Packet Loss', f"Packet loss to router is {loss:.1f}%")
        else: resolve_alert(db, device, 'Packet Loss')
        db.commit()
    except Exception as exc:
        device.status = 'offline'; device.health = 0; device.last_metrics = {'error': str(exc)}
        db.commit()
        upsert_alert(db, device, 'critical', 'Router Offline', str(exc))
    finally:
        db.close()
