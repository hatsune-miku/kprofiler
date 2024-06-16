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
        self.subscribers = []
        self.reload_processes()

    def reload_processes(self) -> None:
        self.processes = self.list_processes(self.config.target)
        self.process_map: ProcessMap = None
        try:
            self.process_map = ProcessMap(self.processes, self.config)
            if self.worker is not None:
                self.worker.set_process_map(self.process_map)
            for subscriber in self.subscribers:
                subscriber(self.process_map)
        except:
            print(f"权限不足，无法访问进程 {self.config.target}，快使出万能的sudo啊！")
            print(
                "备注：Windows下使用sudo - https://github.com/gerardog/gsudo?tab=readme-ov-file#installation"
            )
            ProcessUtils.exit_immediately()

    def subscribe_to_reload(self, callback) -> None:
        self.subscribers.append(callback)

    def start(self) -> None:
        self.worker = KProfilerWorker(self.process_map, self.config, self.history)
        self.worker.start()

    def notify_stop(self) -> None:
        self.worker.notify_stop()

    def wait_all(self) -> None:
        self.worker.wait_all()

    def list_processes(self, target: str) -> List[Process]:
        return ProcessUtils.get_processes_by_name(target)
