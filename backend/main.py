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

async def scheduled_save_graphs():
    from routes.graphs import save_graph_data
    await save_graph_data()

async def scheduled_save_predictions():
    from routes.graphs import save_prediction_data
    await save_prediction_data()

async def scheduled_save_ports_failures():
    from routes.ports import save_failures_data
    await save_failures_data()

async def scheduled_save_consumption_internet():
    from routes.ports import save_internet_consumption_data
    await save_internet_consumption_data()

async def scheduled_save_consumption_non_internet():
    from routes.ports import save_non_internet_consumption_data
    await save_non_internet_consumption_data()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global loop
    loop = asyncio.get_running_loop()  # guardamos el event loop principal

    # asyncio.create_task(scheduled_save_consumption_internet())
    # asyncio.create_task(scheduled_save_consumption_non_internet())

    # Ejecutar cada 5 minutos
    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_alerts(), loop if loop is not None else asyncio.get_event_loop()),
        trigger=IntervalTrigger(minutes=180)
    )

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_graphs(), loop),
        trigger=IntervalTrigger(hours=24),
        id="save_graphs"
    )
    
    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_predictions(), loop),
        trigger=IntervalTrigger(hours=24),
        id="save_predictions"
    )

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_ports_failures(), loop),
        trigger=IntervalTrigger(hours=24),
        id="save_ports_failures"
    )

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_consumption_internet(), loop),
        trigger=IntervalTrigger(hours=24),
        id="save_consumption_internet"
    )

    scheduler.add_job(
        lambda: asyncio.run_coroutine_threadsafe(scheduled_save_consumption_non_internet(), loop),
        trigger=IntervalTrigger(hours=24),
        id="save_consumption_non_internet"
    )

    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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