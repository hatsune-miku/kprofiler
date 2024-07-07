import psutil
import os
from typing import List


class ProcessUtils:
    @staticmethod
    def get_processes_by_name(name: str) -> List[psutil.Process]:
        processes = []
        iterator = psutil.process_iter()
        for process in iterator:
            try:
                if process.name() == name:
                    processes.append(process)
            except:
                pass
        return processes

    @staticmethod
    def get_process_cpu_percent(process: psutil.Process) -> float:
        percent = process.cpu_percent()
        return percent / psutil.cpu_count(logical=False)

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
