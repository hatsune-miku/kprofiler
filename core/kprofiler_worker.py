from .process_map import ProcessMap
from .history import History, ProcessKind
from helpers.config import Config
from helpers.memory_helper import CPUHelper
from helpers.performance_counter import PerformanceCounter
from helpers.process_utils import ProcessUtils
from threading import Thread
from typing import List
import psutil
import time


class KProfilerWorker:
    def __init__(self, process_map: ProcessMap, config: Config, history: History):
        self.thread = None
        self.config = config
        self.process_map = process_map
        self.history = history
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

                # -2 即少等 2s，这是因为 psutil + performance_counter 至少要消耗 2s 才能获取到数据
                time.sleep(max(0, self.config.duration_millis / 1000.0 - 2))

        return _worker

    def _capture_profile(self, processes: List[psutil.Process]):
        pids = [process.pid for process in processes]
        pid_to_gpu_percent = self.performance_counter.get_pid_to_gpu_percent_map(pids)
        cpu_percents = ProcessUtils.get_processes_cpu_percent(processes)
        count = len(processes)

        for i, process in enumerate(processes):
            memory_utilization = self.cpu_helper.query_process(process.pid)
            cpu_percent = cpu_percents[i]
            gpu_percent = pid_to_gpu_percent.get(process.pid, 0)
            process_kind = ProcessKind(
                name=self.config.target,
                type=self.process_map.get_label(process.pid),
            )
            self.history.add_record(
                process=process_kind,
                memory_utilization=memory_utilization,
                cpu_percent=cpu_percent,
                gpu_percent=gpu_percent,
            )

        if self.should_stop:
            return
        
        self.history.save_to_csv(f"history-{self.config.target}.csv", last_count=count)

        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"{now} - {count} records saved to history-{self.config.target}.csv")
