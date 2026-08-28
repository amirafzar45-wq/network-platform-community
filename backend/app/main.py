from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import Base, engine
from app.core.config import settings
from app.api import auth, devices, discovery
import app.models  # noqa

Base.metadata.create_all(bind=engine)
app = FastAPI(title='NetHealth Community', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.api_cors_origins.split(',')], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(auth.router, prefix='/api')
app.include_router(devices.router, prefix='/api')
app.include_router(discovery.router, prefix='/api')

@app.get('/api/health')
def health(): return {'status':'ok','service':'nethealth-backend','version':'0.1.0'}
