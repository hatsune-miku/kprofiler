import psutil
import time
import os
from typing import List


class ProcessUtils:
    @staticmethod
    def get_processes_by_name(name: str) -> List[psutil.Process]:
        return [p for p in psutil.process_iter() if name == p.name()]

    @staticmethod
    def get_processes_cpu_percent(
        processes: List[psutil.Process], sample_seconds: int = 1
    ) -> List[float]:
        count = len(processes)
        cpu_percents = [0] * count
        for i, p in enumerate(processes):
            cpu_percents[i] = max(cpu_percents[i], p.cpu_percent() / psutil.cpu_count())
        time.sleep(sample_seconds)
        for i, p in enumerate(processes):
            cpu_percents[i] = max(cpu_percents[i], p.cpu_percent() / psutil.cpu_count())
        return cpu_percents

    @staticmethod
    def exit_immediately():
        os.kill(os.getpid(), 9)
        os._exit(0)
