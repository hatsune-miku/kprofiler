from helpers.config import Config
from helpers.process_utils import ProcessUtils
from core.kprofiler_worker import KProfilerWorker
from core.process_map import ProcessMap
from psutil import Process
from typing import List


class KProfiler:
    def __init__(self) -> None:
        self.worker = None

    def start(self) -> None:
        config = self.load_config()
        target = config.target
        processes = self.list_processes(target)
        process_map = ProcessMap(processes, config)
        self.worker = KProfilerWorker(process_map, config)
        self.worker.start()

    def load_config(self) -> Config:
        try:
            return Config("config.yaml")
        except:
            print("配置文件加载失败，请确保 config.yaml 存在于 main.py 旁边")
            exit(1)

    def notify_stop(self) -> None:
        self.worker.notify_stop()

    def wait_all(self) -> None:
        self.worker.wait_all()

    def list_processes(self, target: str) -> List[Process]:
        processes = ProcessUtils.get_processes_by_name(target)
        if len(processes) == 0:
            print(f"没找到 {target} 进程，请先运行 {target} 再运行本程序")
            exit(1)
        return processes
