from fastapi import APIRouter

from app.api.routes.accommodations import router as accommodations_router
from app.api.routes.activity import router as activity_router
from app.api.routes.balances import router as balances_router
from app.api.routes.auth import router as auth_router
from app.api.routes.expense_shares import router as expense_shares_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.flights import router as flights_router
from app.api.routes.health import router as health_router
from app.api.routes.invitations import router as invitations_router
from app.api.routes.participants import router as participants_router
from app.api.routes.trips import router as trips_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(trips_router)
api_router.include_router(activity_router)
api_router.include_router(flights_router)
api_router.include_router(accommodations_router)
api_router.include_router(expenses_router)
api_router.include_router(expense_shares_router)
api_router.include_router(balances_router)
api_router.include_router(participants_router)
api_router.include_router(invitations_router)
