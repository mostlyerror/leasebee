"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import leases, extractions, health, auth, organizations, teams

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(leases.router, prefix="/api/leases", tags=["leases"])
app.include_router(extractions.router, prefix="/api/extractions", tags=["extractions"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "🐝 LeaseBee API - Buzzing through leases in seconds",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
