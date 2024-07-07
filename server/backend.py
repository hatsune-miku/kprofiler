from fastapi import FastAPI, staticfiles
from typing import Union
from core import kprofiler, process_map as pmap, history as phistory
import uvicorn


class KProfilerBackend:
    def __init__(
        self,
        profiler: kprofiler.KProfiler,
        process_map: pmap.ProcessMap,
        history: phistory.History,
    ) -> None:
        app = FastAPI()
        self.profiler = profiler
        self.process_map = process_map
        self.history = history
        self.app = app

        app.mount("/", staticfiles.StaticFiles(directory="frontend/dist", html=True))

        @app.get("/api/items/{id}")
        def get_item(id: int, q: str | None = None):
            return {"item_id": id, "q": q}

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=6308)
