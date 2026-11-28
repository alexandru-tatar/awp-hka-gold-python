from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from platform_sdk import Portal, User

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")  # autoescape ist an

# Alle Texte der Seite auf Deutsch und Englisch (Regel R-UI-7); portal.language(request) nennt die Sprache der Person.
TEXTS = {
    "de": {"title": "Meine App", "lead": "Hier entsteht Ihre Anwendung."},
    "en": {"title": "My app", "lead": "Your application is being built here."},
}


def build_router(portal: Portal) -> APIRouter:
    router = portal.router()

    @router.get("/", response_class=HTMLResponse)
    async def home(request: Request, user: User = Depends(portal.user)) -> str:
        tx = TEXTS[portal.language(request)]
        body = templates.get_template("page.html").render(tx=tx)
        return await portal.layout(title=tx["title"], body=body, current=portal.url("/"), user=user)

    return router
