import os, ipaddress, json, time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.core.db import get_db
from app.models import User, Device, Metric, Alert, Backup
from app.schemas.schemas import DeviceCreate, DeviceOut, AlertOut
from app.services.crypto import encrypt, decrypt
from app.services.monitor import collect_device, ping
from app.vendors.mikrotik import MikroTikProvider
from app.core.config import settings

router = APIRouter(prefix='/devices', tags=['devices'])

def serialize(d: Device):
    return DeviceOut(id=d.id,name=d.name,ip=d.ip,vendor=d.vendor,model=d.model,routeros_version=d.routeros_version,uptime=d.uptime,status=d.status,health=d.health,last_seen=d.last_seen.isoformat() if d.last_seen else None)

@router.get('', response_model=list[DeviceOut])
def devices(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [serialize(x) for x in db.scalars(select(Device).order_by(Device.id)).all()]

@router.get('/summary')
def summary(_: User = Depends(current_user), db: Session = Depends(get_db)):
    ds = db.scalars(select(Device)).all(); alerts = db.scalars(select(Alert).where(Alert.active == True)).all()
    health = round(sum(d.health for d in ds)/len(ds),1) if ds else 0
    return {'network_health': health, 'devices': len(ds), 'online': sum(d.status=='online' for d in ds),
            'critical': sum(a.severity=='critical' for a in alerts), 'warning': sum(a.severity=='warning' for a in alerts)}

@router.get('/alerts', response_model=list[AlertOut])
def alerts(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [AlertOut(id=a.id,device_id=a.device_id,severity=a.severity,title=a.title,message=a.message,active=a.active,created_at=a.created_at.isoformat()) for a in db.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(100)).all()]

@router.post('', response_model=DeviceOut)
def add_device(data: DeviceCreate, _: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(Device).where(Device.ip == data.ip)): raise HTTPException(409, 'Device IP already exists')
    d = Device(name=data.name, ip=data.ip, username=data.username, password_enc=encrypt(data.password), port=data.port, use_ssl=data.use_ssl)
    db.add(d); db.commit(); db.refresh(d)
    try: collect_device(d)
    except Exception: pass
    return serialize(d)

@router.post('/{device_id}/test')
def test_device(device_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d: raise HTTPException(404, 'Not found')
    lat, loss = ping(d.ip)
    try:
        p = MikroTikProvider(d.ip,d.username,decrypt(d.password_enc),d.port,d.use_ssl)
        snap = p.get_snapshot()
        return {'ok': True, 'latency_ms': lat, 'packet_loss': loss, 'model': snap.get('model'), 'version': snap.get('routeros_version')}
    except Exception as exc:
        return {'ok': False, 'latency_ms': lat, 'packet_loss': loss, 'error': str(exc)}

@router.post('/{device_id}/monitor')
def monitor(device_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d: raise HTTPException(404, 'Not found')
    collect_device(d)
    db.refresh(d)
    return serialize(d)

@router.get('/{device_id}/detail')
def detail(device_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d: raise HTTPException(404, 'Not found')
    metrics = db.scalars(select(Metric).where(Metric.device_id==device_id).order_by(Metric.timestamp.desc()).limit(100)).all()
    return {'device': serialize(d), 'metrics': [
        {'timestamp': m.timestamp.isoformat(),'cpu':m.cpu,'memory':m.memory,'health':m.health,'latency':m.wan_latency_ms,'loss':m.packet_loss}
        for m in metrics
    ], 'snapshot': d.last_metrics}

@router.post('/{device_id}/backup')
def backup(device_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Device, device_id)
    if not d: raise HTTPException(404, 'Not found')
    p = MikroTikProvider(d.ip,d.username,decrypt(d.password_enc),d.port,d.use_ssl)
    content = p.export_config()
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    Path(settings.backup_dir).mkdir(parents=True, exist_ok=True)
    name = f'{d.name.replace(" ", "_")}_{ts}.rsc'
    path = Path(settings.backup_dir) / name
    path.write_text(content, encoding='utf-8')
    b = Backup(device_id=d.id,filename=name,path=str(path)); db.add(b); db.commit()
    return {'ok': True, 'filename': name, 'path': str(path)}
