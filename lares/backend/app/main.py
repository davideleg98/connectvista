from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    coverage,
    infrastructures,
    map as map_router,
    organisations,
    procurement,
    review_queue,
    search,
    sources,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Lares — European Strategic Infrastructure Intelligence",
    description="See lares/ARCHITECTURE.md and lares/ONTOLOGY.md.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    # both hostnames are the same local dev server; browsers treat
    # localhost/127.0.0.1 as different origins for CORS purposes.
    allow_origins=[settings.lares_web_origin, settings.lares_web_origin.replace("localhost", "127.0.0.1")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(infrastructures.router)
app.include_router(organisations.router)
app.include_router(map_router.router)
app.include_router(search.router)
app.include_router(procurement.router)
app.include_router(sources.router)
app.include_router(coverage.router)
app.include_router(review_queue.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
