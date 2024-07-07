import ctypes
import time
import re
from typing import List, Dict


class PerformanceCounter:
    def __init__(self) -> None:
        pass

    def _pid_from_instance(self, instance: str) -> int:
        return 0

    def _get_gpu_instances(self, pids: List[int]) -> List[str]:
        return []

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        return {}
