import pynvml
from typing import Optional, Tuple

global did_initialized
did_initialized = False

class GPUHelper:
    def __init__(self) -> None:
        global did_initialized
        if did_initialized:
            return
        pynvml.nvmlInit()
        did_initialized = True

    def query_process(self, pid: int) -> Optional[Tuple[object, pynvml.c_nvmlUtilization_t]]:
        # Build process gpu usage map
        pid_to_usage = {}

        count = pynvml.nvmlDeviceGetCount()
        for i in range(0, count):
            device_handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            process_info_list = pynvml.nvmlDeviceGetGraphicsRunningProcesses(device_handle)
            for process_info in process_info_list:
                if process_info.pid == pid:
                    usage = pynvml.nvmlDeviceGetUtilizationRates(device_handle)
                    return (process_info, usage)
        return None
