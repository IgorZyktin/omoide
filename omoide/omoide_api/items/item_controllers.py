"""Item related API operations."""
from fastapi import APIRouter

items_router = APIRouter(prefix='/items', tags=['Items'])
