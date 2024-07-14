from typing import List, Dict
import psutil


class PerformanceCounter:
    def __init__(self) -> None:
        pass

    def _pid_from_instance(self, instance: str) -> int:
        return 0

    def _get_gpu_instances(self, pids: List[int]) -> List[str]:
        return []

    def get_pid_to_cpu_percent_map(
        self, processes: List[psutil.Process]
    ) -> Dict[int, float]:
        return {}

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        return {}

    def invalidate_cache(self):
        pass
