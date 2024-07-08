#!python3
# encoding:utf-8

from core.kprofiler import KProfiler
from core.history import History
from helpers.config import Config
from server.backend import KProfilerBackend
from threading import Thread
import time
import webbrowser


def load_config() -> Config:
    try:
        return Config("config.yaml")
    except:
        print("配置文件加载失败，请确保 config.yaml 存在于 main.py 旁边")
        exit(1)


def main():
    config = load_config()
    history = History(history_upperbound=config.history_upperbound)
    profiler = KProfiler(history=history, config=config)
    backend = KProfilerBackend(profiler, profiler.process_map, history)
    profiler.start()

    if profiler.config.realtime_diagram:
        Thread(
            target=lambda: time.sleep(0.25)
            or webbrowser.open(
                f"http://127.0.0.1:{profiler.config.port}", autoraise=True
            ),
            daemon=True,
        ).start()
        backend.run()

    profiler.wait_all()


if __name__ == "__main__":
    print(
        """
██╗  ██╗██████╗ ██████╗  ██████╗ ███████╗██╗██╗     ███████╗██████╗ 
██║ ██╔╝██╔══██╗██╔══██╗██╔═══██╗██╔════╝██║██║     ██╔════╝██╔══██╗
█████╔╝ ██████╔╝██████╔╝██║   ██║█████╗  ██║██║     █████╗  ██████╔╝
██╔═██╗ ██╔═══╝ ██╔══██╗██║   ██║██╔══╝  ██║██║     ██╔══╝  ██╔══██╗
██║  ██╗██║     ██║  ██║╚██████╔╝██║     ██║███████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
"""
    )
    main()
