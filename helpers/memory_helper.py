import psutil
from typing import NamedTuple
from .process_utils import ProcessUtils


class MemoryUtilization(NamedTuple):
    system_total_memory_mb: int
    system_free_memory_mb: int
    uss_mb: int
    rss_mb: int
    vms_mb: int
    wset_mb: int
    pwset_mb: int


class CPUHelper:
    def __init__(self) -> None:
        self.cpu_count = psutil.cpu_count()

    def _typed_tuple_from_process(self, process: psutil.Process) -> MemoryUtilization:
        memory_info = process.memory_full_info()
        vm = psutil.virtual_memory()
        return MemoryUtilization(
            system_total_memory_mb=vm.total / 1024 / 1024,
            system_free_memory_mb=vm.free / 1024 / 1024,
            uss_mb=memory_info.uss / 1024 / 1024,
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            wset_mb=memory_info.wset / 1024 / 1024,
            pwset_mb=memory_info.private / 1024 / 1024,
        )

    def query_process(self, process: psutil.Process) -> MemoryUtilization:
        return self._typed_tuple_from_process(process)
