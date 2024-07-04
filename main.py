#!python3
# encoding:utf-8

from core.kprofiler import KProfiler
from core.history import History
from server.dash_server import DashServer
from helpers.config import Config
import webbrowser
import time


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
    profiler.start()

    if profiler.config.realtime_diagram:
        server = DashServer(history, profiler.process_map, profiler.config)
        profiler.subscribe_to_process_change(server.notify_processes_updated)
        profiler.trigger_subscribers()
        webbrowser.open(f"http://127.0.0.1:{profiler.config.port}", autoraise=True)

    while True:
        # Main loop
        time.sleep(1)


if __name__ == "__main__":
    main()
