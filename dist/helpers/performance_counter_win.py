from typing import List, Dict
import psutil
from threading import Thread
import subprocess
import time
import requests
import json
import sys


class PerformanceCounter:
    def __init__(self, tss_interval: int, tss_arguments: List[str]) -> None:
        tss_arguments.insert(0, "tss/TaskStatsServer.exe")
        self.tss_arguments = tss_arguments
        self._launch_tss()
        self.pid_to_cpu_percent_map = {}
        self.pid_to_gpu_percent_map = {}
        self.pid_to_memory_mb_map = {}
        self.tss_interval = tss_interval
        self.tss_port = tss_arguments[1]
        Thread(target=self._request_tss, daemon=True).start()

    def _launch_tss(self):
        self.tss = subprocess.Popen(list(map(str, self.tss_arguments)))

    def _request_tss(self):
        time.sleep(1)
        while True:
            time.sleep(self.tss_interval / 1000)
            url = f"http://127.0.0.1:{self.tss_port}"
            try:
                processes = requests.get(url).json()
                for process in processes:
                    try:
                        pid = int(process["PID"])
                        self.pid_to_cpu_percent_map[pid] = float(
                            process["CPU"].replace("%", "").strip()
                        )
                        self.pid_to_gpu_percent_map[pid] = float(
                            process["GPU"].replace("%", "").strip()
                        )
                        self.pid_to_memory_mb_map[pid] = float(
                            process["内存"].replace("MB", "").strip()
                        )
                    except Exception as e:
                        print("无法解析 TaskStatsServer 数据", process, e)
                        continue                    
            except Exception as e:
                print("无法连接 TaskStatsServer", e)

    def invalidate_cache(self):
        pass

    def get_pid_to_cpu_percent_map(
        self, processes: List[psutil.Process]
    ) -> Dict[int, float]:
        return self.pid_to_cpu_percent_map

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        return self.pid_to_gpu_percent_map

    def get_pid_to_memory_mb_map(self, pids: List[int]) -> Dict[int, float]:
        return self.pid_to_memory_mb_map
