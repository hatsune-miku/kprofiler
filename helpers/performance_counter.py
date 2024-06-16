import ctypes
import time
import re
from typing import List, Dict


class COUNTERVALUE_DATA(ctypes.Union):
    _fields_ = [
        ("longValue", ctypes.c_long),
        ("doubleValue", ctypes.c_double),
        ("largeValue", ctypes.c_longlong),
        ("AnsiStringValue", ctypes.c_char_p),
        ("WideStringValue", ctypes.c_wchar_p),
    ]

class PDH_FMT_COUNTERVALUE(ctypes.Structure):
    _fields_ = [
        ("CStatus", ctypes.c_ulong),
        ("data", COUNTERVALUE_DATA),
    ]


class PerformanceCounter:
    PID_PATTERN = re.compile(r"[0-9]{1,5}")
    PDH_FMT_DOUBLE = 0x00000200

    @staticmethod
    def _prepare_pdh() -> ctypes.WinDLL:
        pdh = ctypes.windll.pdh
        pdh.PdhOpenQueryA.restype = ctypes.c_uint
        pdh.PdhOpenQueryA.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]

        pdh.PdhAddCounterA.restype = ctypes.c_uint
        pdh.PdhAddCounterA.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]

        pdh.PdhCollectQueryData.restype = ctypes.c_uint
        pdh.PdhCollectQueryData.argtypes = [ctypes.c_void_p]

        pdh.PdhGetFormattedCounterValue.restype = ctypes.c_uint
        pdh.PdhGetFormattedCounterValue.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(PDH_FMT_COUNTERVALUE),
        ]

        pdh.PdhEnumObjectItemsA.restype = ctypes.c_uint
        pdh.PdhEnumObjectItemsA.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        return pdh

    @staticmethod
    def _assert_status(status) -> None:
        if status != 0:
            raise Exception(f"WinError: {status} ({hex(status)})")

    def __init__(self) -> None:
        self.pdh = self._prepare_pdh()

    def _pid_from_instance(self, instance: str) -> int:
        pid = self.PID_PATTERN.search(instance)
        if pid is None:
            raise Exception(f"Could not find PID in instance name: {instance}")
        return int(pid.group())

    def _get_gpu_instances(self, pids: List[int]) -> List[str]:
        counter_list_buffer_size = ctypes.c_ulong(0)
        instance_list_buffer_size = ctypes.c_ulong(0)

        status = self.pdh.PdhEnumObjectItemsA(
            None,
            None,
            b"GPU Engine",
            None,
            ctypes.byref(counter_list_buffer_size),
            None,
            ctypes.byref(instance_list_buffer_size),
            0,
            0,
        )
        if status != 0x800007D2:  # PDH_MORE_DATA
            self._assert_status(status)

        counter_list_buffer = ctypes.create_string_buffer(
            counter_list_buffer_size.value
        )
        instance_list_buffer = ctypes.create_string_buffer(
            instance_list_buffer_size.value
        )

        self._assert_status(
            self.pdh.PdhEnumObjectItemsA(
                None,
                None,
                b"GPU Engine",
                counter_list_buffer,
                ctypes.byref(counter_list_buffer_size),
                instance_list_buffer,
                ctypes.byref(instance_list_buffer_size),
                0,
                0,
            )
        )
        instances = instance_list_buffer.raw.decode("ascii").strip("\x00").split("\x00")
        return [i for i in instances if self._pid_from_instance(i) in pids]

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        query_handle = ctypes.c_void_p()
        self._assert_status(
            self.pdh.PdhOpenQueryA(None, None, ctypes.byref(query_handle))
        )

        counter_handles = []
        gpu_instances = self._get_gpu_instances(pids)
        for instance in gpu_instances:
            counter_path = f"\\GPU Engine({instance})\\Utilization Percentage".encode(
                "ascii"
            )
            counter_handle = ctypes.c_void_p()
            self._assert_status(
                self.pdh.PdhAddCounterA(
                    query_handle,
                    ctypes.c_char_p(counter_path),
                    None,
                    ctypes.byref(counter_handle),
                )
            )
            counter_handles.append((instance, counter_handle))

        self._assert_status(self.pdh.PdhCollectQueryData(query_handle))
        time.sleep(1)
        self._assert_status(self.pdh.PdhCollectQueryData(query_handle))

        pid_to_gpu_percent_map = {}

        start = time.time()
        for instance, counter_handle in counter_handles:
            counter_value = PDH_FMT_COUNTERVALUE()
            counter_type = ctypes.c_uint()
            self._assert_status(
                self.pdh.PdhGetFormattedCounterValue(
                    counter_handle,
                    self.PDH_FMT_DOUBLE,
                    ctypes.byref(counter_type),
                    ctypes.byref(counter_value),
                )
            )
            instance = str(instance)
            pid = self._pid_from_instance(instance)
            pid_to_gpu_percent_map[pid] = counter_value.data.doubleValue

        self.pdh.PdhCloseQuery(query_handle)
        return pid_to_gpu_percent_map
