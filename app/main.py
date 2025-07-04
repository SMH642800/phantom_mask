from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api import pharmacies, users, summary, search, purchase

# Main FastAPI application entry point
app = FastAPI(
    title="Pharmacy Mask API",
    version="1.0"
)

# Register all API routers with their respective prefixes
def register_routers():
    app.include_router(pharmacies.router, prefix="/pharmacies")
    app.include_router(users.router, prefix="/users")
    app.include_router(summary.router, prefix="/summary")
    app.include_router(search.router, prefix="/search")
    app.include_router(purchase.router, prefix="/purchase")

# Register the routers when the app starts
register_routers()

# Root endpoint for health check and API info
@app.get("/")
def read_root():
    return {
        "message": "Pharmacy Mask API", 
        "version": "1.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Global exception handlers for consistent error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# For local development: run with `PYTHONPATH=. python app/main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)