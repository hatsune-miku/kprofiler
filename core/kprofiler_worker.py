from .process_map import ProcessMap
from .history import History, ProcessKind
from helpers.config import Config
from helpers.memory_helper import CPUHelper, MemoryUtilization
from helpers.performance_counter import PerformanceCounter
from helpers.process_utils import ProcessUtils
from threading import Thread
from typing import List, Any
import psutil
import time


class KProfilerWorker:
    def __init__(
        self,
        process_map: ProcessMap,
        config: Config,
        history: History,
        emit_reload: Any,
    ):
        self.thread = None
        self.config = config
        self.process_map = process_map
        self.history = history
        self.cpu_helper = CPUHelper()
        self.performance_counter = PerformanceCounter()
        self.should_stop = False
        self.thread = None
        self.emit_reload = emit_reload
        print(process_map)

    def start(self) -> None:
        worker = self._make_worker()
        self.thread = Thread(target=worker)
        self.thread.start()

    def wait_all(self) -> None:
        self.thread.join()

    def notify_stop(self) -> None:
        self.should_stop = True

    def set_process_map(self, process_map: ProcessMap) -> None:
        self.process_map = process_map

    def _make_worker(self) -> None:
        def _worker():
            while not self.should_stop:
                try:
                    self._capture_profile(self.process_map.processes)
                except:
                    pass

                self.emit_reload()

                # -2 即少等 2s，这是因为 psutil 和 performance_counter 至少要消耗 2s 才能获取到数据
                time.sleep(max(0, self.config.duration_millis / 1000.0 - 2))

        return _worker

    def _capture_profile(self, processes: List[psutil.Process]):
        pids = [process.pid for process in processes]
        pid_to_gpu_percent = self.performance_counter.get_pid_to_gpu_percent_map(pids)
        cpu_percents = ProcessUtils.get_processes_cpu_percent(processes)
        count = len(processes)

        cpu_percent_total = 0
        gpu_percent_total = 0
        system_total_memory_mb_total = 0
        process_used_memory_mb_total = 0
        system_free_memory_mb_total = 0

        for i, process in enumerate(processes):
            memory_utilization = self.cpu_helper.query_process(process.pid)
            cpu_percent = cpu_percents[i]
            gpu_percent = pid_to_gpu_percent.get(process.pid, 0)
            process_kind = ProcessKind(
                pid=process.pid,
                name=self.config.target,
                label=self.process_map.get_label(process.pid),
            )
            cpu_percent_total += cpu_percent
            gpu_percent_total += gpu_percent
            system_total_memory_mb_total = memory_utilization.system_total_memory_mb
            process_used_memory_mb_total += memory_utilization.process_used_memory_mb
            system_free_memory_mb_total = memory_utilization.system_free_memory_mb
            self.history.add_record(
                process=process_kind,
                memory_utilization=memory_utilization,
                cpu_percent=cpu_percent,
                gpu_percent=gpu_percent,
            )
        self.history.add_record(
            process=ProcessKind(pid=0, name=self.config.target, label="总值"),
            memory_utilization=MemoryUtilization(
                system_total_memory_mb=system_total_memory_mb_total,
                process_used_memory_mb=process_used_memory_mb_total,
                system_free_memory_mb=system_free_memory_mb_total,
            ),
            cpu_percent=cpu_percent_total,
            gpu_percent=gpu_percent_total,
        )

        if self.should_stop:
            return

        if self.config.write_logs:
            self.history.save_to_csv(
                f"history-{self.config.target}.csv", last_count=count
            )

            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(
                f"{now} - {count} record(s) saved to history-{self.config.target}.csv"
            )
