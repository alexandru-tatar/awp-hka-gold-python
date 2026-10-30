from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from platform_sdk import Portal

from . import views

portal = Portal.from_env()  # liest manifest.json und die Variablen PORTAL_*
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)  # keine offenen Seiten /docs, /openapi.json
portal.install(app)  # Anmeldung und /healthz: vor allen Routen, nicht entfernen
app.mount(portal.url("/static"), StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(views.build_router(portal))
