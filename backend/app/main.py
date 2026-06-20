"""FastAPI entrypoint. Run locally with: uvicorn app.main:app --reload"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_health, routes_ingest, routes_match, routes_trials
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Clinical Trial Matching API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (routes_health, routes_match, routes_trials, routes_ingest):
        app.include_router(module.router, prefix="/api")
    return app


app = create_app()
