from helpers.config import Config
from helpers.process_utils import ProcessUtils
from core.kprofiler_worker import KProfilerWorker
from core.process_map import ProcessMap
from core.history import History
from psutil import Process
from typing import List, Tuple, NamedTuple


class ProcessDiff(NamedTuple):
    new_processes: List[Process]
    disappeared_processes: List[Process]
    current_processes: List[Process]
    any_new: bool
    any_disappeared: bool
    any_change: bool


class KProfiler:
    def __init__(self, history: History, config: Config) -> None:
        self.history = history
        self.config = config
        self.worker: KProfilerWorker = None
        self.process_map = ProcessMap([], self.config)
        self.subscribers = []
        self.reload_processes(skip_optimization=True)

    def subscribe_to_process_change(self, callback) -> None:
        self.subscribers.append(callback)

    def trigger_subscribers(self) -> None:
        for subscriber in self.subscribers:
            subscriber()

    def reload_processes(self, skip_optimization: bool = False) -> None:
        diff = self._new_processes_diff(
            current=self.process_map.processes,
            next_state=self.list_processes(self.config.target),
        )
        if not skip_optimization:
            if not diff.any_change:
                # 进程列表未发生变化，无需重新加载
                return
        self.processes = diff.current_processes
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
    def _new_processes_diff(
        current: List[Process], next_state: List[Process]
    ) -> ProcessDiff:
        """
        增量地获得进程列表，从而尽量不销毁现有对象
        返回值的第二个元素表示是否有新的进程加入
        """
        new_processes = []
        disappeared_processes = []
        any_new = False
        any_disappeared = False

        present_pids = [process.pid for process in current]
        may_contain_new_pids = [process.pid for process in next_state]

        for process in next_state:
            if process.pid not in present_pids:
                new_processes.append(process)
                any_new = True

        for process in current:
            if process.pid not in may_contain_new_pids:
                disappeared_processes.append(process)
                any_disappeared = True

        current_processes = new_processes + [
            process for process in current if process not in disappeared_processes
        ]

        return ProcessDiff(
            new_processes=new_processes,
            disappeared_processes=disappeared_processes,
            current_processes=current_processes,
            any_new=any_new,
            any_disappeared=any_disappeared,
            any_change=any_new or any_disappeared,
        )
