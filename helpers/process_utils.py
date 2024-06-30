import psutil
import time
import os
from typing import List


class ProcessUtils:
    @staticmethod
    def get_processes_by_name(name: str) -> List[psutil.Process]:
        return [p for p in psutil.process_iter() if name == p.name()]

    @staticmethod
    def get_process_cpu_percent(process: psutil.Process) -> float:
        percent = process.cpu_percent()
        if percent > 100:
            percent /= psutil.cpu_count(logical=False)
        return percent

    @staticmethod
    def get_processes_cpu_percent(processes: List[psutil.Process]) -> List[float]:
        count = len(processes)
        cpu_percents = [0] * count
        for i, p in enumerate(processes):
            cpu_percents[i] = max(
                cpu_percents[i], ProcessUtils.get_process_cpu_percent(p)
            )
        return cpu_percents

    @staticmethod
    def exit_immediately():
        os.kill(os.getpid(), 9)
        os._exit(0)
