import time
import logging
import dash
import plotly.graph_objs as go
import sys
from dash import dcc, html
from dash.dependencies import Input, Output

from typing import List, Tuple
from core.history import History
from core.process_map import ProcessMap
from helpers.config import Config
from psutil import Process
from threading import Thread
from flask import request, Flask
from werkzeug.serving import make_server

# Disable werkzeug logging
logging.getLogger("werkzeug").setLevel(logging.ERROR + 1000)


class FlaskServer:
    def __init__(self, flask: Flask, app: dash.Dash, config: Config) -> None:
        self.flask = flask
        self.app = app
        self.config = config
        self.server_thread = None

        # https://docs.python.org/3/library/sys.html
        self.traceback_limit_backup = 1000

    def start(self) -> None:
        print("Process list changed. Server reloading...")
        self.server = make_server("0.0.0.0", self.config.port, self.flask)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.start()

        def _start_dash_app():
            self.app.run(
                debug=False,
                use_reloader=False,
            )

        self.dash_thread = Thread(target=_start_dash_app)
        self.dash_thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server_thread.join()


class DummyProcess:
    pid = 0

    def __init__(self, process_name: str) -> None:
        self.process_name = process_name

    def name(self):
        return self.process_name


class DashServer:
    def __init__(
        self,
        history: History,
        process_map: ProcessMap,
        config: Config,
    ):
        self.history = history
        self.config = config
        self.process_map = process_map
        self.dash: dash.Dash = None
        self.server: FlaskServer = None
        self.processes: List[Process] = []
        self.process_labels = set()
        self._update_internal_processes()

    def notify_processes_updated(self):
        if self.server is not None:
            self.server.stop()
            self.server = None

        # 顺序不能错啊！
        self._update_internal_processes()
        self.flask, self.dash = self._create_dash()
        self._register_callbacks()
        self.server = FlaskServer(self.flask, self.dash, self.config)
        self.server.start()

    def _update_internal_processes(self):
        self.process_labels = self.process_map.available_labels
        is_empty = len(self.process_map.processes) == 0
        if is_empty:
            self.processes = []
        else:
            self.processes = [
                DummyProcess(self.config.target)
            ] + self.process_map.processes

    def _register_callbacks(self):
        for process in self.processes:
            pid = process.pid

            self.dash.callback(
                Output(f"live-update-graph-{pid}-percents", "figure"),
                [Input("interval-refresh-layout", "n_intervals")],
            )(self._make_callback_for(pid=pid, is_percent_data=True))

            self.dash.callback(
                Output(f"live-update-graph-{pid}-data", "figure"),
                [Input("interval-refresh-layout", "n_intervals")],
            )(self._make_callback_for(pid=pid, is_percent_data=False))

    def _make_callback_for(self, pid: int, is_percent_data: bool):
        def callback(n: int) -> go.Figure:
            latest_records = self.history.get_latest(100, pid)
            if not latest_records:
                return go.Figure()

            time_format = lambda t: time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(t)
            )
            timestamps = [
                time_format(record.timestamp_seconds) for record in latest_records
            ]

            fig = go.Figure()

            if is_percent_data:
                cpu_percents = [record.cpu_percent for record in latest_records]
                gpu_percents = [record.gpu_percent for record in latest_records]
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=cpu_percents,
                        mode="lines+markers",
                        name="CPU %",
                        line=dict(color="#ff7f0e"),
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=gpu_percents,
                        mode="lines+markers",
                        name="GPU %",
                        line=dict(color="#39c5bb"),
                    )
                )
                fig.update_layout(
                    title=f"{pid} 使用率数据",
                    xaxis_title="时间",
                    yaxis_title="使用率 %",
                )
            else:
                memory_utilizations = [
                    record.memory_utilization.process_used_memory_mb
                    for record in latest_records
                ]
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=memory_utilizations,
                        mode="lines+markers",
                        name="Memory Utilization (MB)",
                        line=dict(color="#fb7299"),
                    )
                )
                fig.update_layout(
                    title=f"{pid} RAM使用情况",
                    xaxis_title="时间",
                    yaxis_title="已用RAM (MB)",
                )
            return fig

        return callback

    def _create_dash(self) -> Tuple[Flask, dash.Dash]:
        flask_app = Flask(__name__)
        dash_app = dash.Dash(
            __name__,
            server=flask_app,
            assets_folder="assets",
            title="KProfiler",
            update_title="\\^O^/",
            suppress_callback_exceptions=True,
        )
        graphs = []
        for process in self.processes:
            name = process.name()
            pid = process.pid
            label = self.process_map.get_label(pid)
            graphs.append(
                html.Div(
                    [
                        html.H2(f"{name} ({pid}, {label}) 数据"),
                        dcc.Graph(id=f"live-update-graph-{pid}-percents"),
                        dcc.Graph(id=f"live-update-graph-{pid}-data"),
                    ]
                ),
            )

        if len(self.processes) == 0:
            graphs.append(
                html.Div(
                    [
                        html.H2("暂无数据"),
                        html.H3("请打开目标进程，然后这里会自动刷新"),
                    ]
                )
            )
        dash_app.layout = html.Div(
            [
                html.H1(f"KProfiler ({self.config.target})"),
                *graphs,
                dcc.Interval(
                    id="interval-refresh-layout",
                    interval=self.config.page_update_interval,
                    n_intervals=0,
                ),
            ]
        )
        return flask_app, dash_app
