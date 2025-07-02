from fastapi import FastAPI
from app.api import pharmacies, users, summary, search, purchase


app = FastAPI(
    title="Pharmacy Mask API",
    version="1.0"
)

# Register routers
app.include_router(pharmacies.router, prefix="/pharmacies")
app.include_router(users.router, prefix="/users")
app.include_router(summary.router, prefix="/summary")
app.include_router(search.router, prefix="/search")
app.include_router(purchase.router, prefix="/purchase")


# sAdd a root endpoint
@app.get("/")
def read_root():
    return {"message": "Pharmacy Mask API", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)