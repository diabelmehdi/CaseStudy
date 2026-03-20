from fastapi import FastAPI
from app.api.routes import router
from app.db.session import engine, Base
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Prime Number Generator API",
    description="Microservice that generates prime numbers within a given range",
    version="1.0.0",
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
