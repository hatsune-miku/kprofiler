from .process_map import ProcessMap
from helpers.config import Config
from helpers.cpu_helper import CPUHelper
from helpers.performance_counter import PerformanceCounter
from threading import Thread
from typing import List
import psutil
import time


class KProfilerWorker:
    def __init__(self, process_map: ProcessMap, config: Config):
        self.thread = None
        self.config = config
        self.process_map = process_map
        self.cpu_helper = CPUHelper()
        self.performance_counter = PerformanceCounter()
        self.should_stop = False
        self.thread = None
        print(process_map)

    def start(self) -> None:
        worker = self._make_worker(self.process_map.processes)
        self.thread = Thread(target=worker)
        self.thread.start()

    def wait_all(self) -> None:
        self.thread.join()

    def notify_stop(self) -> None:
        self.should_stop = True

    def _make_worker(self, processes: List[psutil.Process]) -> None:
        def _worker():
            while not self.should_stop:
                self._capture_profile(processes)

                # -1 即少等 1s，这是因为 performance_counter 至少要消耗 1s 才能获取到数据
                time.sleep(max(0, self.config.duration_millis / 1000.0 - 1))

        return _worker

    def _capture_profile(self, processes: List[psutil.Process]):
        pids = [process.pid for process in processes]
        pid_to_gpu_percent = self.performance_counter.get_pid_to_gpu_percent_map(pids)

        for process in processes:
            hardware_utilization = self.cpu_helper.query_process(process.pid)
            gpu_percent = pid_to_gpu_percent.get(process.pid, 0)
            print(hardware_utilization, gpu_percent)
            pass
