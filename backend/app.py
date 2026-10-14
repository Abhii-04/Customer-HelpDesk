from fastapi import APIRouter,FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
router=APIRouter()

router.frontend("/",directory="frontend",fallback="index.html")
app.include_router(router,prefix="/app")

app.mount("/static",StaticFiles(directory="static"),name="static")