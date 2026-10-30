from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from platform_sdk import Portal, User

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")  # autoescape ist an


def build_router(portal: Portal) -> APIRouter:
    router = portal.router()

    @router.get("/", response_class=HTMLResponse)
    async def home(user: User = Depends(portal.user)) -> str:
        body = templates.get_template("page.html").render()
        return await portal.layout(title="Meine App", body=body, current=portal.url("/"), user=user)

    return router
