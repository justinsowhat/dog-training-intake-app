from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import Base, async_engine
    async with async_engine.begin() as conn:
        print("[INFO] Database connection is being established")
        await conn.run_sync(Base.metadata.create_all)
        print("[INFO] Tables are being created")
    print("[INFO] Application booting up: Initializing OpenRouter connection pool")
    yield
    
    print("[INFO] Application shutting down: Cleanging up network sockets")
    
app = FastAPI(
    title="PawsitiveMind API",
    description="Asynchronous AI Animal Behavioral Consulting Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=['*']
)

app.include_router(chat.router)

@app.get("/health", tags=["Infrastructure"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "pawsitive-mind-backend"}