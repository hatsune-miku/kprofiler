from typing import NamedTuple, List, Optional
from helpers.memory_helper import MemoryUtilization
import time


class ProcessKind(NamedTuple):
    name: str
    type: str


class HistoryRecord(NamedTuple):
    timestamp_seconds: int
    process: ProcessKind
    memory_utilization: MemoryUtilization
    cpu_percent: float
    gpu_percent: float


class History:
    def __init__(self) -> None:
        self.records: List[HistoryRecord] = []

    def add_record(
        self,
        process: ProcessKind,
        cpu_percent: float,
        memory_utilization: MemoryUtilization,
        gpu_percent: float,
    ) -> None:
        self.records.append(
            HistoryRecord(
                int(time.time()),
                process,
                memory_utilization,
                cpu_percent,
                gpu_percent,
            )
        )

    def get_latest(self, count: int) -> List[HistoryRecord]:
        return self.records[-count:]

    def save_to_csv(self, path: str, last_count: Optional[int]) -> None:
        records = self.get_latest(last_count) if last_count else self.records

        with open(path, "a", encoding="utf-8") as f:
            for record in records:
                memory = record.memory_utilization
                process = record.process
                row = {
                    "timestamp_seconds": record.timestamp_seconds,
                    "process_name": process.name,
                    "process_type": process.type,
                    "cpu_percent": record.cpu_percent,
                    "gpu_percent": record.gpu_percent,
                    "process_used_memory_mb": memory.process_used_memory_mb,
                    "system_total_memory_mb": memory.system_total_memory_mb,
                    "system_free_memory_mb": memory.system_free_memory_mb,
                }
                if f.tell() == 0:
                    f.write(",".join(row.keys()) + "\n")
                row_str = ",".join([str(row[key]) for key in row])
                f.write(row_str + "\n")
