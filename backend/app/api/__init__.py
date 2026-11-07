from fastapi import APIRouter

from app.api.config import router as config_router
from app.api.don_gia import router as don_gia_router
from app.api.export import router as export_router
from app.api.project import router as project_router
from app.api.vat_tu import router as vat_tu_router
from app.api.compare import router as compare_router
from app.api.cvc import router as cvc_router
from app.api.coefficients import router as coefficients_router
from app.api.svdt import router as svdt_router
from app.api.auth import router as auth_router
from app.api.bid_package import router as bid_package_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(config_router)
api_router.include_router(don_gia_router)
api_router.include_router(project_router)
api_router.include_router(export_router)
api_router.include_router(vat_tu_router)
api_router.include_router(cvc_router)
api_router.include_router(coefficients_router)
api_router.include_router(svdt_router)
api_router.include_router(compare_router)
api_router.include_router(bid_package_router)
