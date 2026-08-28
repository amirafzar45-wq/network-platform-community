from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)

class LoginIn(RegisterIn):
    pass

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    ip: str
    username: str
    password: str
    port: int = 443
    use_ssl: bool = True

class DeviceOut(BaseModel):
    id: int
    name: str
    ip: str
    vendor: str
    model: str | None
    routeros_version: str | None
    uptime: str | None
    status: str
    health: float
    last_seen: str | None

class AlertOut(BaseModel):
    id: int
    device_id: int
    severity: str
    title: str
    message: str
    active: bool
    created_at: str
