from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
from routes import auth, alerts, ports, devices, graphs,address
import asyncio

scheduler = AsyncIOScheduler()
loop = None

# Función para llamar la ruta desde dentro del servidor
async def scheduled_save_alerts():
    from routes.alerts import save_alerts_to_db
    await save_alerts_to_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global loop
    loop = asyncio.get_running_loop()  # guardamos el event loop principal
    # Ejecutar una vez al iniciar
    asyncio.create_task(scheduled_save_alerts())

    # Ejecutar cada 5 minutos
    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_alerts(), loop if loop is not None else asyncio.get_event_loop()),
        trigger=IntervalTrigger(minutes=180)
    )

    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(devices.router)
app.include_router(ports.router)
app.include_router(graphs.router)
app.include_router(address.router)