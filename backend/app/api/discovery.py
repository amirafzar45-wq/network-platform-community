import ipaddress, subprocess, socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import current_user
from app.models import User

router = APIRouter(prefix='/discovery', tags=['discovery'])

def scan_ip(ip: str):
    try:
        p = subprocess.run(['ping','-c','1','-W','1',ip],capture_output=True,timeout=2)
        if p.returncode == 0:
            try: host=socket.gethostbyaddr(ip)[0]
            except Exception: host=None
            return {'ip':ip,'alive':True,'hostname':host}
    except Exception: pass
    return None

@router.post('/scan')
def scan(cidr: str, _: User = Depends(current_user)):
    try: net=ipaddress.ip_network(cidr, strict=False)
    except ValueError: raise HTTPException(400,'Invalid CIDR')
    hosts=list(net.hosts())
    if len(hosts)>1024: raise HTTPException(400,'Community discovery limited to /22 or smaller')
    result=[]
    with ThreadPoolExecutor(max_workers=64) as ex:
        futures=[ex.submit(scan_ip,str(ip)) for ip in hosts]
        for f in as_completed(futures):
            x=f.result()
            if x: result.append(x)
    return sorted(result,key=lambda x: ipaddress.ip_address(x['ip']))
