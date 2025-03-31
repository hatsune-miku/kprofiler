from psutil import Process
from typing import List
from helpers.config import Config


class ProcessMap:
    def __init__(self, processes: List[Process], config: Config) -> None:
        self.config = config
        self.update_processes(processes)

    def update_processes(self, processes: List[Process]):
        self.pid_to_label = {}
        self.processes = processes
        self.available_labels = set()
        criteria = self.config.label_criteria
        for process in processes:
            try:
                cmdline = " ".join(process.cmdline())
            except:
                continue
            labelled = False
            for criterion in criteria:
                self.available_labels.add(criterion.label)
                if criterion.keyword in cmdline:
                    self.pid_to_label[process.pid] = criterion.label
                    labelled = True
                    break
            if not labelled:
                self.available_labels.add("主进程")
                self.pid_to_label[process.pid] = "主进程"

    def get_label(self, pid: int) -> str:
        if pid == 0:
            return "总值"
        return self.pid_to_label.get(pid)

    def exists(self, pid: int) -> bool:
        return pid in self.pid_to_label

    @property
    def labels(self) -> List[str]:
        return list(self.available_labels)

    def count_label(self, label: str) -> int:
        return sum([1 for l in self.pid_to_label.values() if l == label])
