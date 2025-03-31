import signal
import win32api
import os


def kill_on_ctrl_c():
    def handler(sig, frame):
        print("Ctrl+C pressed. Killing the process.")
        self_pid = os.getpid()
        hProcess = win32api.OpenProcess(2035711, False, self_pid)
        if hProcess:
            win32api.TerminateProcess(hProcess, 0)

    signal.signal(signal.SIGINT, handler)
