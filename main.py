#!python3
# encoding:utf-8

from core.kprofiler import KProfiler
from core.history import History
from server.dash_server import DashServer
import webbrowser


def main():
    history = History(history_upperbound=5000)
    profiler = KProfiler(history)
    profiler.start()

    if profiler.config.realtime_diagram:
        server = DashServer(history, profiler.process_map, profiler.config)
        profiler.subscribe_to_process_change(server.notify_processes_updated)
        profiler.trigger_subscribers()
        webbrowser.open(f"http://127.0.0.1:{profiler.config.port}", autoraise=True)


if __name__ == "__main__":
    main()
