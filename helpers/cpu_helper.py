import psutil
from typing import NamedTuple


class CPUUtilization(NamedTuple):
    cpu_utilization_percent: float
    system_total_memory_mb: int
    process_used_memory_mb: int
    system_free_memory_mb: int


class HardwareUtilization(NamedTuple):
    cpu: CPUUtilization


class CPUHelper:
    @staticmethod
    def _typed_tuples_from_nvml(process: psutil.Process) -> HardwareUtilization:
        memory_info = process.memory_info()
        vm = psutil.virtual_memory()
        return HardwareUtilization(
            cpu=CPUUtilization(
                cpu_utilization_percent=process.cpu_percent(interval=None),
                system_total_memory_mb=vm.total / 1024 / 1024,
                process_used_memory_mb=memory_info.rss / 1024 / 1024,
                system_free_memory_mb=vm.free / 1024 / 1024,
            ),
        )

    def query_process(self, pid: int) -> HardwareUtilization:
        # Build process gpu usage map
        process = psutil.Process(pid)
        return self._typed_tuples_from_nvml(process)
