import time
from app.core.db import SessionLocal
from app.models import Device
from app.services.monitor import collect_device
from app.core.config import settings

while True:
    db=SessionLocal()
    try:
        devices=db.query(Device).all()
    finally:
        db.close()
    for device in devices[:1]:
        collect_device(device)
    time.sleep(max(10, settings.poll_interval_seconds))
