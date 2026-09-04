from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.capture import CameraWorker
from src.config import settings
from src.database import init_db
from src.routes import manager, router

workers: list[CameraWorker] = []


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    for cam in settings.cameras:
        worker = CameraWorker(cam, manager)
        worker.start()
        workers.append(worker)
    yield
    for worker in workers:
        worker.stop()
    for worker in workers:
        worker.join(timeout=5)
    workers.clear()


app = FastAPI(title="Cormorant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
