from .process_map import ProcessMap
from .history import History, ProcessKind
from helpers.config import Config
from helpers.memory_helper import CPUHelper, MemoryUtilization
from helpers.performance_counter import PerformanceCounter
from helpers.process_utils import ProcessUtils
from threading import Thread
from typing import List, Any, Dict
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
        self.config = config
        self.process_map = process_map
        self.history = history
        self.cpu_helper = CPUHelper()
        self.performance_counter = PerformanceCounter()
        self.should_stop = False
        self.gpu_thread = None
        self.worker_thread = None
        self.emit_reload = emit_reload
        self.pid_to_gpu_percent_cache = {}
        self.paused = False
        print(process_map)

    def start(self) -> None:
        worker = self._make_worker()
        self.worker_thread = Thread(target=worker, daemon=True)
        self.worker_thread.start()

        if not self.config.disable_gpu:
            gpu_worker = self._make_gpu_worker()
            self.gpu_thread = Thread(target=gpu_worker, daemon=True)
            self.gpu_thread.start()

    def wait_all(self) -> None:
        self.worker_thread.join()

    def notify_stop(self) -> None:
        self.should_stop = True

    def set_process_map(self, process_map: ProcessMap) -> None:
        self.process_map = process_map

    def _make_worker_routine(self, duration_millis: int, proc):
        def _routine():
            while not self.should_stop:
                start_time = time.time()
                proc()
                seconds_elapsed = time.time() - start_time
                time.sleep(max(0.1, duration_millis / 1000.0 - seconds_elapsed))

        return _routine

    def _make_gpu_worker(self):
        def _proc():
            pid_to_gpu = self.performance_counter.get_pid_to_gpu_percent_map(
                [p.pid for p in self.process_map.processes]
            )
            for pid, gpu_percent in pid_to_gpu.items():
                self.pid_to_gpu_percent_cache[pid] = gpu_percent

        return self._make_worker_routine(self.config.gpu_duration_millis, _proc)

    def _make_worker(self):
        def _proc():
            try:
                if not self.paused:
                    self._capture_profile(self.process_map.processes)
            except:
                pass

            reload_thread = Thread(target=self.emit_reload, daemon=True)
            reload_thread.start()

        return self._make_worker_routine(self.config.duration_millis, _proc)

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        ret = {}
        for pid in pids:
            if pid in self.pid_to_gpu_percent_cache:
                ret[pid] = self.pid_to_gpu_percent_cache[pid]
            else:
                ret[pid] = 0
        return ret

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _capture_profile(self, processes: List[psutil.Process]):
        pids = [process.pid for process in processes]
        pid_to_gpu_percent = self.get_pid_to_gpu_percent_map(pids)
        cpu_percents = ProcessUtils.get_processes_cpu_percent(processes)
        count = len(processes)

        cpu_percent_total = 0
        gpu_percent_total = 0
        system_total_memory_mb_total = 0
        system_free_memory_mb_total = 0
        uss_mb_total = 0
        rss_mb_total = 0
        vms_mb_total = 0
        wset_mb_total = 0
        pwset_mb_total = 0

        for i, process in enumerate(processes):
            memory_utilization = self.cpu_helper.query_process(process)
            cpu_percent = cpu_percents[i]
            gpu_percent = pid_to_gpu_percent.get(process.pid, 0)
            process_kind = ProcessKind(
                pid=process.pid,
                name=self.config.target,
                label=self.process_map.get_label(process.pid),
            )

            system_total_memory_mb_total = memory_utilization.system_total_memory_mb
            system_free_memory_mb_total = memory_utilization.system_free_memory_mb

            cpu_percent_total += cpu_percent
            gpu_percent_total += gpu_percent
            uss_mb_total += memory_utilization.uss_mb
            rss_mb_total += memory_utilization.rss_mb
            vms_mb_total += memory_utilization.vms_mb
            wset_mb_total += memory_utilization.wset_mb
            pwset_mb_total += memory_utilization.pwset_mb

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
                system_free_memory_mb=system_free_memory_mb_total,
                uss_mb=uss_mb_total,
                rss_mb=rss_mb_total,
                vms_mb=vms_mb_total,
                wset_mb=wset_mb_total,
                pwset_mb=pwset_mb_total,
            ),
            cpu_percent=cpu_percent_total,
            gpu_percent=gpu_percent_total,
        )

        if self.should_stop:
            return

        if self.config.write_logs:
            self.history.append_to_csv(
                f"history-{self.config.target}.csv", last_count=count
            )
