#!python3
# encoding:utf-8

from core.kprofiler import KProfiler
from core.history import History
from server.dash_server import DashServer
from helpers.process_utils import ProcessUtils
import signal
import webbrowser


def make_signal_interrupt_handler(profiler: KProfiler):
    def h(sig, frame):
        print("Interrupted by user, stopping...")
        ProcessUtils.exit_immediately()
        profiler.notify_stop()
        profiler.wait_all()
        exit(0)

    return h


def main():
    history = History()
    profiler = KProfiler(history)
    profiler.start()

    if profiler.config.realtime_diagram:
        signal.signal(signal.SIGINT, make_signal_interrupt_handler(profiler))
        server = DashServer(history, profiler.process_map, profiler.config)
        profiler.subscribe_to_process_change(server.notify_processes_updated)
        profiler.trigger_subscribers()
        webbrowser.open(f"http://127.0.0.1:{profiler.config.port}", autoraise=True)
    else:
        signal.signal(signal.SIGINT, make_signal_interrupt_handler(profiler))


if __name__ == "__main__":
    main()
