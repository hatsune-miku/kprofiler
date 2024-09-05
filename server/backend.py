from fastapi import FastAPI, APIRouter, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from core import kprofiler, process_map as pmap, history as phistory
from pydantic import BaseModel
import uvicorn


class LoadHistoryRequest(BaseModel):
    full_history: str


def _create_fastapi_app(router: APIRouter) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


class KProfilerBackend:
    def __init__(
        self,
        profiler: kprofiler.KProfiler,
        process_map: pmap.ProcessMap,
        history: phistory.History,
    ) -> None:
        self.profiler = profiler
        self.process_map = process_map
        self.history = history

        router = APIRouter()
        router.add_api_route("/api/config", self.get_config, methods=["GET"])
        router.add_api_route("/api/history", self.get_history, methods=["GET"])
        router.add_api_route("/api/processes", self.get_processes, methods=["GET"])
        router.add_api_route("/api/download", self.request_download, methods=["POST"])
        router.add_api_route("/api/load", self.request_load, methods=["POST"])
        router.add_api_route("/api/clear", self.request_clear, methods=["POST"])
        self.router = router

        app = _create_fastapi_app(self.router)
        app.mount("/", staticfiles.StaticFiles(directory="frontend/dist", html=True))
        self.app = app

    def get_config(self):
        config = self.profiler.config
        return {
            "targetProcessName": config.target,
            "durationMillis": config.duration_millis,
            "shouldShowRealtimeDiagram": config.realtime_diagram,
            "pageUpdateIntervalMillis": config.page_update_interval,
            "shouldWriteLogs": config.write_logs,
            "shouldDisableGpu": config.disable_gpu,
            "shouldShowTotalOnly": config.total_only,
            "port": config.port,
            "historyUpperBound": config.history_upperbound,
            "cpuDurationMillis": config.cpu_duration_millis,
            "gpuDurationMillis": config.gpu_duration_millis,
            "labelCriteria": [
                {"keyword": c.keyword, "label": c.label} for c in config.label_criteria
            ],
        }

    def get_history(self, offset: int, version: int):
        need_upgrade = version != self.history.version
        if need_upgrade:
            records = self.history.get_offset(0)
        else:
            records = self.history.get_offset(offset)

        translatedRecords = []
        for record in records:
            translatedRecords.append(
                {
                    "timestampSeconds": record.timestamp_seconds,
                    "process": {
                        "processId": record.process.pid,
                        "name": record.process.name,
                        "label": record.process.label,
                    },
                    "cpuPercentage": record.cpu_percent,
                    "gpuPercentage": record.gpu_percent,
                    "memoryUtilization": {
                        "uniqueSetSize": record.memory_utilization.uss_mb,
                        "residentSetSize": record.memory_utilization.rss_mb,
                        "virtualSize": record.memory_utilization.vms_mb,
                        "workingSet": record.memory_utilization.wset_mb,
                        "privateWorkingSet": record.memory_utilization.pwset_mb,
                        "systemTotal": record.memory_utilization.system_total_memory_mb,
                        "systemAvailable": record.memory_utilization.system_free_memory_mb,
                    },
                }
            )

        return {
            "history": {
                "records": translatedRecords,
            },
            "version": (self.history.version if need_upgrade else None),
        }

    def get_processes(self):
        self.profiler.reload_processes()
        return {
            "processes": list(
                map(
                    lambda p: {
                        "processId": p.pid,
                        "name": p.name(),
                        "label": self.process_map.get_label(p.pid),
                    },
                    self.process_map.processes,
                )
            )
        }

    def request_download(self):
        full_history = self.history.serialize()
        return {"fullHistory": full_history}

    def request_load(self, data: LoadHistoryRequest):
        self.history.parse_and_load(
            data.full_history,
            history_upperbound=self.profiler.config.history_upperbound,
        )

    def request_clear(self):
        self.history.records.clear()

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=6308, log_level="error")
