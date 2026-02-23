"""
URL configuration for si3ln_api project.
"""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from game.api import router as game_router
from game.auth.auth_api import router as auth_router

# Customize admin site
admin.site.site_header = "SI3LN Game Administration"
admin.site.site_title = "SI3LN Admin"
admin.site.index_title = "Game Management Dashboard"

# API Configuration
api = NinjaAPI(
    title="SI3LN Game API",
    version="1.0.0",
    description="API for Space Invaders III Last Night game",
    auth=None  # Global auth disabled, we'll use it per-endpoint
)

# Register routers
api.add_router("/auth/", auth_router, tags=["Authentication"])
api.add_router("/game/", game_router, tags=["Game"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
