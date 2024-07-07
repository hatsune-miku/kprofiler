from typing import NamedTuple, List, Optional, Dict, Any
from helpers.memory_helper import MemoryUtilization
import time


class ProcessKind(NamedTuple):
    pid: int
    name: str
    label: str


class HistoryRecord(NamedTuple):
    timestamp_seconds: int
    process: ProcessKind
    memory_utilization: MemoryUtilization
    cpu_percent: float
    gpu_percent: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_seconds": self.timestamp_seconds,
            "process_id": self.process.pid,
            "process_name": self.process.name,
            "process_label": self.process.label,
            "cpu_percent": self.cpu_percent,
            "gpu_percent": self.gpu_percent,
            "uss_mb": self.memory_utilization.uss_mb,
            "rss_mb": self.memory_utilization.rss_mb,
            "vms_mb": self.memory_utilization.vms_mb,
            "wset_mb": self.memory_utilization.wset_mb,
            "pwset_mb": self.memory_utilization.pwset_mb,
            "system_total_memory_mb": self.memory_utilization.system_total_memory_mb,
            "system_free_memory_mb": self.memory_utilization.system_free_memory_mb,
        }

    def serialize(self) -> str:
        pairs = self.to_dict()
        return ",".join(map(str, pairs.values()))

    @staticmethod
    def parse(s: str) -> "HistoryRecord":
        values = s.split(",")
        return HistoryRecord(
            timestamp_seconds=int(values[0]),
            process=ProcessKind(pid=int(values[1]), name=values[2], label=values[3]),
            cpu_percent=float(values[4]),
            gpu_percent=float(values[5]),
            memory_utilization=MemoryUtilization(
                uss_mb=float(values[6]),
                rss_mb=float(values[7]),
                vms_mb=float(values[8]),
                wset_mb=float(values[9]),
                pwset_mb=float(values[10]),
                system_total_memory_mb=float(values[11]),
                system_free_memory_mb=float(values[12]),
            ),
        )


class History:
    def __init__(self, history_upperbound: int) -> None:
        self.records: List[HistoryRecord] = []
        self.history_upperbound = history_upperbound
        self.version = 0

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
        if len(self.records) > self.history_upperbound:
            self.records = self.records[-self.history_upperbound :]

    def get_all(
        self, time_window=None, pid: Optional[int] = None
    ) -> List[HistoryRecord]:
        return [
            r
            for r in self.records
            if r.timestamp_seconds >= time_window.start
            and r.timestamp_seconds <= time_window.end
            and (pid is None or r.process.pid == pid)
        ]

    def get_latest(self, count: int, pid: Optional[int] = None) -> List[HistoryRecord]:
        records = (
            self.records
            if pid is None
            else [r for r in self.records if r.process.pid == pid]
        )
        return records[-count:]

    def get_offset(self, offset: int) -> List[HistoryRecord]:
        return self.records[offset:]

    def serialize(self, last_count: Optional[int] = None) -> str:
        records = self.get_latest(last_count) if last_count else self.records
        if len(records) == 0:
            return ""
        header: str = ",".join(map(str, records[0].to_dict().keys()))
        data: str = "\n".join([record.serialize() for record in records])
        return header + "\n" + data

    @staticmethod
    def parse(s: Optional[str], history_upperbound: int) -> "History":
        ret = History(history_upperbound)
        if not s or s == "":
            return ret
        lines = s.split("\n")[1:]
        records = []
        for line in lines:
            try:
                records.append(HistoryRecord.parse(line))
            except:
                pass
        ret.records = records
        return ret

    def parse_and_load(self, s: str, history_upperbound: int) -> None:
        """
        与parse返回新对象不同，parse_and_load就地修改当前对象
        """
        history = History.parse(s, history_upperbound)
        self.records = history.records

    def parse_file_and_load(self, path: str, history_upperbound: int) -> None:
        """
        与parse返回新对象不同，parse_file_and_load就地修改当前对象
        """
        with open(path, "r", encoding="utf-8") as f:
            self.parse_and_load(f.read(), history_upperbound)

    def upgrade(self):
        self.version += 1

    def append_to_csv(self, path: str, last_count: Optional[int]) -> None:
        """
        不存在会创建
        """
        records = self.get_latest(last_count) if last_count else self.records
        with open(path, "a", encoding="utf-8") as f:
            for record in records:
                row = record.to_dict()
                if f.tell() == 0:
                    f.write(",".join(row.keys()) + "\n")
                row_str = ",".join([str(row[key]) for key in row])
                f.write(row_str + "\n")
