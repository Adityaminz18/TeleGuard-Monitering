from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to TeleGuard API", "version": settings.VERSION}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# We will import routers here later
# from app.api.v1.endpoints import auth, telegram
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
