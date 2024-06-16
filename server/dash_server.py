import time
import logging
import dash
import plotly.graph_objs as go  # 好好好
from dash import dcc, html
from dash.dependencies import Input, Output

from core.history import History
from core.process_map import ProcessMap
from helpers.config import Config
from psutil import Process


class DummyProcess:
    # 0代表总值
    pid = 0

    def __init__(self, process_name: str) -> None:
        self.process_name = process_name

    def name(self):
        return self.process_name


class DashServer:
    def __init__(
        self, history: History, process_map: ProcessMap, config: Config
    ) -> None:
        self.history = history
        self.config = config
        self.app = dash.Dash(
            __name__, assets_folder="assets", title="KProfiler", update_title="\\^O^/"
        )
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        self.set_process_map(process_map)

    def set_process_map(self, process_map: ProcessMap) -> None:
        print(process_map)
        self.process_map = process_map
        self.process_labels = process_map.available_labels
        self.processes = [DummyProcess(self.config.target)] + process_map.processes
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self) -> None:
        graphs = []
        for process in self.processes:
            name = process.name()
            pid = process.pid
            label = self.process_map.get_label(pid)
            graphs.append(
                html.Div(
                    [
                        html.H2(f"{name} ({pid}, {label}) 使用率"),
                        dcc.Graph(id=f"live-update-graph-{pid}-percents"),
                    ]
                )
            )
            graphs.append(
                html.Div(
                    [
                        html.H2(f"{name} ({pid}, {label}) RAM使用"),
                        dcc.Graph(id=f"live-update-graph-{pid}-data"),
                    ]
                )
            )
        self.app.layout = html.Div(
            [
                html.H1(f"KProfiler ({self.config.target})"),
                *graphs,
                dcc.Interval(
                    id="interval-component",
                    interval=self.config.page_update_interval,
                    n_intervals=0,
                ),
            ]
        )

    def setup_callbacks(self) -> None:
        for process in self.processes:
            pid = process.pid
            self.app.callback(
                Output(f"live-update-graph-{pid}-percents", "figure"),
                [Input("interval-component", "n_intervals")],
            )(self.update_graph_live_percents(pid))
            self.app.callback(
                Output(f"live-update-graph-{pid}-data", "figure"),
                [Input("interval-component", "n_intervals")],
            )(self.update_graph_live_data(pid))

    def update_graph_live_percents(self, pid: int):
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
            cpu_percents = [record.cpu_percent for record in latest_records]
            gpu_percents = [record.gpu_percent for record in latest_records]

            fig = go.Figure()
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

            return fig

        return callback

    def update_graph_live_data(self, pid: int):
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
            memory_utilizations = [
                record.memory_utilization.process_used_memory_mb
                for record in latest_records
            ]

            fig = go.Figure()
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

    def start(self) -> None:
        self.app.run(
            debug=False, host="0.0.0.0", port=self.config.port, use_reloader=False
        )
