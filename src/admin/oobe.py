# Tips: The OOBE endpoint can only be used if the DB configuration is not complete.
import subprocess
import os

from fastapi import APIRouter, Response, Form
from fastapi.templating import Jinja2Templates

app = APIRouter(prefix="/admin/oobe")
templates = Jinja2Templates(directory="templates/admin")


@app.get("/", name="outofbox")
async def oobe(response: Response):
    return templates.TemplateResponse("oobe.html", {"request": response.request})


@app.post("/", name="outofbox")
async def oobe_setup(
    response: Response,
    dbType: str = Form(...),
    dbHost: str = Form(None),
    dbName: str = Form(None),
    dbUser: str = Form(None),
    dbFile: str = Form(None),
    dbPassword: str = Form(...),
    adminEmail: str = Form(...),
    adminPassword: str = Form(...),
    adminPasswordConfirm: str = Form(...),
):
    env = os.environ
    if dbType != "sqlite":
        env["DATABASE_URL"] = f"{dbType}://{dbUser}:{dbPassword}@{dbHost}/{dbName}"
    else:
        env["DATABASE_URL"] = f"file://{dbFile}"
    subprocess.run("prisma db push", shell=True, env=env)
    return templates.TemplateResponse("dashboard.html", {"request": response.request})
