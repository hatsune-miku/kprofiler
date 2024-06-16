import psutil
from typing import List

class ProcessUtils:
    @staticmethod
    def get_processes_by_name(name: str) -> List[psutil.Process]:
        return [p for p in psutil.process_iter() if name == p.name()]
