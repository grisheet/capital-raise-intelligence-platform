from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dashboard, companies, atm, convertibles, placements, filings, watchlists, raise_events, meta

app = FastAPI(
    title="Capital Raise Intelligence Platform",
    description="Production-grade API for monitoring SEC filings, dilution risk, and capital raise events.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(atm.router, prefix="/api/atm", tags=["atm"])
app.include_router(convertibles.router, prefix="/api/convertibles", tags=["convertibles"])
app.include_router(placements.router, prefix="/api/placements", tags=["placements"])
app.include_router(filings.router, prefix="/api/filings", tags=["filings"])
app.include_router(watchlists.router, prefix="/api/watchlists", tags=["watchlists"])
app.include_router(raise_events.router, prefix="/api/raise-events", tags=["raise_events"])
app.include_router(meta.router, prefix="/api/meta", tags=["meta"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "capital-raise-intelligence-platform"}
