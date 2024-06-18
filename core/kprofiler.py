from helpers.config import Config
from helpers.process_utils import ProcessUtils
from core.kprofiler_worker import KProfilerWorker
from core.process_map import ProcessMap
from core.history import History
from psutil import Process
from typing import List


class KProfiler:
    @staticmethod
    def load_config() -> Config:
        try:
            return Config("config.yaml")
        except:
            print("配置文件加载失败，请确保 config.yaml 存在于 main.py 旁边")
            exit(1)

    def __init__(self, history: History) -> None:
        self.history = history
        self.config = self.load_config()
        self.worker: KProfilerWorker = None
        self.process_map = ProcessMap([], self.config)
        self.subscribers = []
        self.last_processes = []
        self.reload_processes(skip_optimization=True)

    def subscribe_to_process_change(self, callback) -> None:
        self.subscribers.append(callback)

    def trigger_subscribers(self) -> None:
        for subscriber in self.subscribers:
            subscriber()

    def reload_processes(self, skip_optimization: bool = False) -> None:
        processes = self.list_processes(self.config.target)
        if not skip_optimization:
            if self._is_processes_equal(self.last_processes, processes):
                # 进程列表未发生变化，无需重新加载
                return
            self.last_processes = processes
        self.processes = processes
        self.process_map.update_processes(self.processes)
        self.trigger_subscribers()

    def start(self) -> None:
        self.worker = KProfilerWorker(
            self.process_map, self.config, self.history, self.reload_processes
        )
        self.worker.start()

    def notify_stop(self) -> None:
        self.worker.notify_stop()

    def wait_all(self) -> None:
        self.worker.wait_all()

    def list_processes(self, target: str) -> List[Process]:
        return ProcessUtils.get_processes_by_name(target)

    @staticmethod
    def _is_processes_equal(p1: List[Process], p2: List[Process]) -> bool:
        if len(p1) != len(p2):
            return False
        p1.sort(key=lambda x: x.pid)
        p2.sort(key=lambda x: x.pid)
        for i in range(0, len(p1)):
            if p1[i].pid != p2[i].pid:
                return False
        return True
