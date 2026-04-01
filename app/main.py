from fastapi import FastAPI
from sqlalchemy import text
from db.session import engine

app = FastAPI(title="Room booking Service")

@app.get("/")
def read_root():
    return {"message": "Hello"}

@app.get("/_info")
async def info():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status}