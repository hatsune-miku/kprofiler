from typing import List, Dict
import psutil
from threading import Thread
import subprocess
import time
import urllib.request
import json


class PerformanceCounter:
    def __init__(self, tss_interval: int, tss_arguments: List[str]) -> None:
        tss_arguments.insert(0, "tss/TaskStatsServer.exe")
        self.tss = subprocess.Popen(list(map(str, tss_arguments)))
        self.pid_to_cpu_percent_map = {}
        self.pid_to_gpu_percent_map = {}
        self.tss_interval = tss_interval
        self.tss_port = tss_arguments[1]
        Thread(target=self._request_tss, daemon=True).start()

    def _request_tss(self):
        time.sleep(1)
        while True:
            time.sleep(self.tss_interval / 1000)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.tss_port}") as f:
                    data = f.read().decode("utf-8")
                    json_data = json.loads(data)[0]  # TODO: 多进程支持
                    self.pid_to_cpu_percent_map[0] = float(
                        json_data["CPU"].replace("%", "").strip()
                    )
                    self.pid_to_gpu_percent_map[0] = float(
                        json_data["GPU"].replace("%", "").strip()
                    )
            except Exception as e:
                print("等待 TaskStatsServer 进程...", e)

    def invalidate_cache(self):
        pass

    def get_pid_to_cpu_percent_map(
        self, processes: List[psutil.Process]
    ) -> Dict[int, float]:
        return self.pid_to_cpu_percent_map

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        return self.pid_to_gpu_percent_map
