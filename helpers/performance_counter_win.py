import ctypes
import time
import re
import psutil
from typing import List, Dict, Tuple, NamedTuple

import win32gui, win32ui
from ctypes import windll
import numpy as np
import cv2
import easyocr
import re
import time
import pytesseract as tss

PDH_MORE_DATA = 0x800007D2


reader = easyocr.Reader(["ch_sim", "en"])


def is_valid_percent_text(text: str) -> bool:
    regex = r"^[0-9]+(\.[0-9]+)?%$"
    return re.match(regex, text) is not None


def read_cpu_percent(hwnd: int) -> float:
    rect = win32gui.GetWindowRect(hwnd)
    width, height = rect[2] - rect[0], rect[3] - rect[1]

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    save_bitmap = win32ui.CreateBitmap()

    save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(save_bitmap)

    windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
    bmpinfo = save_bitmap.GetInfo()
    bmpstr = save_bitmap.GetBitmapBits(True)

    capture = np.frombuffer(bmpstr, dtype=np.uint8).reshape(
        (bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4)
    )
    capture = np.ascontiguousarray(capture[..., :-1])

    win32gui.DeleteObject(save_bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    capture = cv2.cvtColor(capture, cv2.COLOR_BGRA2GRAY)
    capture = capture[233:273, 448:533]

    blocks = reader.recognize(capture, allowlist="%.1234567890")
    if len(blocks) != 1:
        print(f"Invalid blocks: {blocks}")
        return 0

    box, text, confidence = blocks[0]
    if not is_valid_percent_text(text):
        print(f"Invalid text: {text}")
        return 0

    tss_text = ""
    try:
        tss_text = tss.image_to_string(capture, config="--psm 6").strip()
    except:
        print("tss failed")

    if not is_valid_percent_text(tss_text):
        print(f"Invalid tss text: {tss_text}")
        return 0

    print(f"Text: {text}")
    print(f"tss: {tss_text}")

    text_value = float(text[:-1])
    tss_value = float(tss_text[:-1])
    return min(text_value, tss_value)


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


class InstanceCounterHandle(NamedTuple):
    instance: str
    counter_handle: ctypes.c_void_p


class ProcessCounterHandle(NamedTuple):
    process: psutil.Process
    counter_handle: ctypes.c_void_p


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
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
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
        self.pdh: ctypes.WinDLL = self._prepare_pdh()
        self.gpu_process_counter_cache: Dict[str, InstanceCounterHandle] = {}
        self.cpu_process_counter_cache: Dict[psutil.Process, ProcessCounterHandle] = {}
        self.cpu_query_handle = ctypes.c_void_p()
        self.gpu_query_handle = ctypes.c_void_p()
        self.cpu_process_recent_history: Dict[int, List[float]] = {}
        self._assert_status(
            self.pdh.PdhOpenQueryA(None, None, ctypes.byref(self.cpu_query_handle))
        )
        self._assert_status(
            self.pdh.PdhOpenQueryA(None, None, ctypes.byref(self.gpu_query_handle))
        )

        self.hwnd = win32gui.FindWindow(None, "任务管理器")
        if self.hwnd == 0:
            raise Exception("Task Manager not found")

        rect = win32gui.GetWindowRect(self.hwnd)
        width, height = rect[2] - rect[0], rect[3] - rect[1]
        win32gui.ShowWindow(self.hwnd, 1)
        win32gui.MoveWindow(self.hwnd, -114514, -114514, width, height, True)

    def __del__(self) -> None:
        try:
            self.pdh.PdhCloseQuery(self.cpu_query_handle)
            self.pdh.PdhCloseQuery(self.gpu_query_handle)
        except:
            pass

    def invalidate_cache(self):
        self.cpu_process_counter_cache = {}
        self.gpu_process_counter_cache = {}
        self._assert_status(
            self.pdh.PdhOpenQueryA(None, None, ctypes.byref(self.cpu_query_handle))
        )
        self._assert_status(
            self.pdh.PdhOpenQueryA(None, None, ctypes.byref(self.gpu_query_handle))
        )
        print("Reloaded performance counter cache")

    def _pid_from_instance(self, instance: str) -> int:
        pid = self.PID_PATTERN.search(instance)
        if pid is None:
            raise Exception(f"Could not find PID in instance name: {instance}")
        return int(pid.group())

    def _get_recent_n_records(self, pid: int, n: int) -> List[float]:
        if pid not in self.cpu_process_recent_history:
            self.cpu_process_recent_history[pid] = []
        return self.cpu_process_recent_history[pid][-n:]

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
        if status != PDH_MORE_DATA:
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
        filtered_instances = []
        for instance in instances:
            pid = self._pid_from_instance(instance)
            if pid in pids:
                filtered_instances.append(instance)
        return filtered_instances

    def get_pid_to_cpu_percent_map(
        self, processes: List[psutil.Process]
    ) -> Dict[int, float]:
        return { 0: read_cpu_percent(self.hwnd) }

        process_counter_handle_pairs: List[Tuple[psutil.Process, ctypes.c_void_p]] = []
        for i, process in enumerate(processes):
            name = process.name().strip(".exe")

            cached_process = self.cpu_process_counter_cache.get(process)
            if cached_process is not None:
                process_counter_handle_pairs.append(
                    (cached_process.process, cached_process.counter_handle)
                )
            else:
                process_name = name if i == 0 else f"{name}#{i}"
                counter_path = f"\\Process({process_name})\\% Processor Time".encode(
                    "ascii"
                )
                counter_handle = ctypes.c_void_p()
                self._assert_status(
                    self.pdh.PdhAddCounterA(
                        self.cpu_query_handle,
                        ctypes.c_char_p(counter_path),
                        None,
                        ctypes.byref(counter_handle),
                    )
                )
                process_counter_handle_pairs.append((process, counter_handle))
                self.cpu_process_counter_cache[process] = ProcessCounterHandle(
                    process=process, counter_handle=counter_handle
                )
                self.pdh.PdhCollectQueryData(self.cpu_query_handle)

        self.pdh.PdhCollectQueryData(self.cpu_query_handle)
        pid_to_cpu_percent_map = {}

        for process, counter_handle in process_counter_handle_pairs:
            counter_value = PDH_FMT_COUNTERVALUE()
            counter_type = ctypes.c_ulong()
            try:
                self._assert_status(
                    self.pdh.PdhGetFormattedCounterValue(
                        counter_handle,
                        self.PDH_FMT_DOUBLE,
                        ctypes.byref(counter_type),
                        ctypes.byref(counter_value),
                    )
                )
            except:
                pass
            pid = process.pid
            percent_value = counter_value.data.doubleValue / psutil.cpu_count(
                logical=False
            )
            if pid not in self.cpu_process_recent_history:
                self.cpu_process_recent_history[pid] = []
            self.cpu_process_recent_history[pid].append(percent_value)
            percent_value = sum(self._get_recent_n_records(pid, 1))
            pid_to_cpu_percent_map[pid] = percent_value

        return pid_to_cpu_percent_map

    def get_pid_to_gpu_percent_map(self, pids: List[int]) -> Dict[int, float]:
        counter_handles = []
        gpu_instances = self._get_gpu_instances(pids)
        for instance in gpu_instances:
            pid = self._pid_from_instance(instance)
            cached_instance = self.gpu_process_counter_cache.get(instance)

            if cached_instance is not None:
                counter_handles.append(
                    (cached_instance.instance, cached_instance.counter_handle)
                )
            else:
                counter_path = (
                    f"\\GPU Engine({instance})\\Utilization Percentage".encode("ascii")
                )
                counter_handle = ctypes.c_void_p()
                self._assert_status(
                    self.pdh.PdhAddCounterA(
                        self.gpu_query_handle,
                        ctypes.c_char_p(counter_path),
                        None,
                        ctypes.byref(counter_handle),
                    )
                )
                counter_handles.append((instance, counter_handle))
                self.gpu_process_counter_cache[instance] = InstanceCounterHandle(
                    instance=instance, counter_handle=counter_handle
                )
                self.pdh.PdhCollectQueryData(self.gpu_query_handle)

        self.pdh.PdhCollectQueryData(self.gpu_query_handle)

        pid_to_gpu_percent_map = {}

        for instance, counter_handle in counter_handles:
            counter_value = PDH_FMT_COUNTERVALUE()
            counter_type = ctypes.c_ulong()
            self._assert_status(
                self.pdh.PdhGetFormattedCounterValue(
                    counter_handle,
                    self.PDH_FMT_DOUBLE,
                    ctypes.byref(counter_type),
                    ctypes.byref(counter_value),
                )
            )
            value = counter_value.data.doubleValue
            pid = self._pid_from_instance(instance=instance)
            if pid not in pid_to_gpu_percent_map:
                pid_to_gpu_percent_map[pid] = value
            else:
                pid_to_gpu_percent_map[pid] += value

        return pid_to_gpu_percent_map
