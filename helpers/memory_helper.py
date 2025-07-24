import psutil
from typing import NamedTuple
from .process_utils import ProcessUtils


class MemoryUtilization(NamedTuple):
    system_total_memory_mb: float
    system_free_memory_mb: float
    taskmgr_mb: float
    uss_mb: float
    rss_mb: float
    vms_mb: float
    wset_mb: float
    pwset_mb: float
    vsize: float


class CPUHelper:
    def __init__(self) -> None:
        self.cpu_count = psutil.cpu_count()

    def _typed_tuple_from_process(self, process: psutil.Process) -> MemoryUtilization:
        memory_info = process.memory_full_info()
        vm = psutil.virtual_memory()

        return MemoryUtilization(
            system_total_memory_mb=vm.total / 1024 / 1024,
            system_free_memory_mb=vm.free / 1024 / 1024,
            taskmgr_mb=0,
            uss_mb=memory_info.uss / 1024 / 1024,
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            wset_mb=memory_info.wset / 1024 / 1024,
            pwset_mb=memory_info.private / 1024 / 1024,
            vsize=0,
        )

    def query_process(self, process: psutil.Process) -> MemoryUtilization:
        return self._typed_tuple_from_process(process)
