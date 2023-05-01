from fastapi import APIRouter

from api.api_v1.endpoint.auth import auth_router
from api.api_v1.endpoint.lesson import lesson_router
from api.api_v1.endpoint.dashboard import dashboard_router
from api.api_v1.endpoint.public import public_router
from api.api_v1.endpoint.oss import oss_router
from api.api_v1.endpoint.admin import admin_router


router = APIRouter()

router.include_router(
    dashboard_router, prefix="/dashboard", tags=["dashboard"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(lesson_router, prefix="/lesson", tags=["lesson"])
router.include_router(public_router, prefix="/public", tags=["public"])
router.include_router(oss_router, prefix="/oss", tags=["oss"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
