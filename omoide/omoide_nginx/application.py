"""Special endpoints for nginx."""

from fastapi import APIRouter
from fastapi import FastAPI

from omoide.omoide_nginx.download import download_controllers


def get_nginx() -> FastAPI:
    """Create API instance."""
    return FastAPI(
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )


def apply_nginx_routes_v1(current_api: FastAPI) -> None:
    """Register NGINX routes."""
    nginx_router_v1 = APIRouter()
    nginx_router_v1.include_router(download_controllers.nginx_download_router)
    current_api.include_router(nginx_router_v1)
