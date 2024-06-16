from psutil import Process
from typing import List
from helpers.config import Config
from prettytable import PrettyTable

class ProcessMap:
    def __init__(self, processes: List[Process], config: Config) -> None:
        self.pid_to_label = {}
        self.processes = processes
        self.available_labels = set()
        self.config = config
        criteria = config.label_criteria
        for process in processes:
            labelled = False
            for criterion in criteria:
                self.available_labels.add(criterion.label)
                cmdline = ' '.join(process.cmdline())
                if criterion.keyword in cmdline:
                    self.pid_to_label[process.pid] = criterion.label
                    labelled = True
                    break
            if not labelled:
                self.available_labels.add('主进程')
                self.pid_to_label[process.pid] = '主进程'
    
    def get_label(self, pid: int) -> str:
        return self.pid_to_label.get(pid)
    
    @property
    def labels(self) -> List[str]:
        return list(self.available_labels)

    def count_label(self, label: str) -> int:
        return sum([1 for l in self.pid_to_label.values() if l == label])

    def __str__(self) -> str:
        table = PrettyTable(["类型", "数量"])
        for label in self.labels:
            table.add_row([label, self.count_label(label)])
        return f"共找到 {len(self.processes)} 个 {self.config.target} 进程\n{table}"
