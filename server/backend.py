from fastapi import FastAPI
from typing import Union
import uvicorn

app = FastAPI()


@app.get("/")
def index():
    return {"data": "miku"}


@app.get("/items/{id}")
def get_item(id: int, q: str | None = None):
    return {"item_id": id, "q": q}


def run_backend():
    uvicorn.run(app, host="0.0.0.0", port=6308)
