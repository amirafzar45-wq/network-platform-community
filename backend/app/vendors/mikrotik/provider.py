import time
from urllib.parse import quote
import requests
from app.vendors.base import NetworkProvider

class MikroTikError(RuntimeError):
    pass

class MikroTikProvider(NetworkProvider):
    """RouterOS REST API provider for RouterOS 7+.

    RouterOS REST is the JSON wrapper around the RouterOS console/API.
    We keep this provider isolated so a future native API provider can coexist.
    """
    vendor = "MikroTik"

    def __init__(self, host: str, username: str, password: str, port: int = 443, use_ssl: bool = True, verify_tls: bool = False):
        scheme = 'https' if use_ssl else 'http'
        self.base = f'{scheme}://{host}:{port}/rest'
        self.auth = (username, password)
        self.verify_tls = verify_tls

    def _request(self, method: str, path: str, body: dict | None = None):
        url = f"{self.base}/{path.lstrip('/')}"
        try:
            r = requests.request(method, url, auth=self.auth, json=body, verify=self.verify_tls, timeout=12)
        except requests.RequestException as exc:
            raise MikroTikError(str(exc)) from exc
        if r.status_code >= 400:
            raise MikroTikError(f'HTTP {r.status_code}: {r.text[:500]}')
        if not r.text.strip(): return []
        try: return r.json()
        except Exception as exc: raise MikroTikError(f'Invalid JSON from RouterOS: {r.text[:300]}') from exc

    def _print(self, path: str, proplist=None, query=None):
        body = {}
        if proplist: body['.proplist'] = proplist
        if query: body['.query'] = query
        return self._request('POST', f'{path.rstrip("/")}/print', body)

    def get_snapshot(self) -> dict:
        resource = self._request('GET', '/system/resource')
        identity = self._request('GET', '/system/identity')
        board = self._request('GET', '/system/routerboard')
        interfaces = self._print('/interface', ['.id','name','type','running','disabled','rx-byte','tx-byte','rx-packet','tx-packet','rx-error','tx-error','rx-drop','tx-drop','speed','full-duplex'])
        routes = self._print('/ip/route', ['.id','dst-address','gateway','distance','active','disabled','dynamic','scope'])
        dhcp_pools = self._print('/ip/pool', ['.id','name','ranges'])
        dhcp_used = self._print('/ip/pool/used', ['pool','address','owner'])
        resource = resource[0] if isinstance(resource, list) and resource else {}
        identity = identity[0] if isinstance(identity, list) and identity else {}
        board = board[0] if isinstance(board, list) and board else {}
        def num(v, default=0.0):
            try: return float(v)
            except Exception: return default
        cpu = num(resource.get('cpu-load'))
        total_mem = num(resource.get('total-memory'))
        free_mem = num(resource.get('free-memory'))
        memory = max(0.0, (1 - free_mem / total_mem) * 100) if total_mem else 0.0
        interfaces_up = sum(1 for i in interfaces if str(i.get('running','false')).lower() in ('true','yes'))
        routes_active = sum(1 for r in routes if str(r.get('active','false')).lower() in ('true','yes'))
        return {
            'name': identity.get('name') or self.base,
            'model': board.get('model') or resource.get('board-name'),
            'serial': board.get('serial-number'),
            'routeros_version': resource.get('version'),
            'uptime': resource.get('uptime'),
            'firmware': board.get('current-firmware'),
            'architecture': resource.get('architecture-name'),
            'cpu': cpu, 'memory': memory,
            'interfaces_total': len(interfaces), 'interfaces_up': interfaces_up,
            'routes_total': len(routes), 'routes_active': routes_active,
            'interfaces': interfaces[:200], 'routes': routes[:200],
            'dhcp_pools': dhcp_pools[:100], 'dhcp_used': dhcp_used[:500],
            'seen_at': time.time(), 'ok': True
        }

    def export_config(self) -> str:
        # RouterOS explicitly supports /rest/export with a file parameter.
        filename = f'nethealth-{int(time.time())}.rsc'
        self._request('POST', '/export', {'compact': '', 'terse': '', 'file': filename})
        info = self._print('/file', ['name','size'], [f'name={filename}'])
        size = 0
        if info:
            try: size = int(float(info[0].get('size', 0)))
            except Exception: size = 0
        chunks = []
        offset = 0
        # RouterOS file/read accepts up to 32,768 bytes per chunk.
        while offset < max(size, 1):
            result = self._request('POST', '/file/read', {'file': filename, 'offset': str(offset), 'chunk-size': '32768'})
            if not result: break
            data = result[0].get('data', '') if isinstance(result, list) else result.get('data','')
            chunks.append(str(data))
            got = len(str(data).encode('utf-8'))
            if got <= 0: break
            offset += got
            if offset >= size: break
        return ''.join(chunks)
