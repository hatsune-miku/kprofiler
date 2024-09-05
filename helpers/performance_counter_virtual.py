from typing import List, Dict
import psutil


class PerformanceCounter:
    def __init__(self) -> None:
        pass

    def invalidate_cache(self):
        pass

    def get_pid_to_cpu_percent_map(
        self, processes: List[psutil.Process]
    ) -> Dict[int, float]:
        return {}

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        return {}
