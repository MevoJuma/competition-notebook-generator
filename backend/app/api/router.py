from fastapi import APIRouter
from app.api.v1.competitions import router as competitions_router
from app.api.v1.files import router as files_router
from app.api.v1.notebooks import router as notebooks_router

api_router = APIRouter()

api_router.include_router(competitions_router)
api_router.include_router(files_router)
api_router.include_router(notebooks_router)
