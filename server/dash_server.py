"""
Dash 是 KProfiler 可视化各种数据所依赖的模块。

这个模块真的非常非常难用，如果早知道，绝不会用的，哎，我现在看到dash这个单词就头大

这个文件是调用 Dash 的，里面包含了大量的：
    - callback
    - Input
    - Output
    - State
上面这些关键字以一种神奇的、难以维护的方式组合起来，支撑可视化运作。
"""

import time
import logging
import dash
import plotly.graph_objs as go  # ?
from dash import dcc, html, ClientsideFunction
from dash.dependencies import Input, Output

from typing import List, Tuple, NamedTuple, Dict, Optional
from core.history import History
from core.process_map import ProcessMap
from helpers.config import Config
from helpers.process_utils import ProcessUtils
from psutil import Process
from threading import Thread
from flask import request, Flask
from werkzeug.serving import make_server


class Trace(NamedTuple):
    key: str
    title: str
    color: str
    data: object


class TimeWindow(NamedTuple):
    """
    单位：时间戳（秒）
    """

    start: int
    end: int


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
        self.refresh_flag = False
        self.processes: List[Process] = []
        self.process_labels = set()
        self.time_window: Optional[TimeWindow] = None
        self.should_refresh = True
        self.next_tick = None
        self.status_text = "未在计时"
        self._update_internal_processes()

    def on_next_tick(self, proc):
        self.next_tick = proc

    def call_next_tick(self):
        if self.next_tick is not None:
            self.next_tick()
            self.next_tick = None

    def notify_processes_updated(self):
        if self.server is not None:
            self.server.stop()
            self.server = None

        # 顺序不能错啊啊啊啊！
        self._update_internal_processes()
        self.flask, self.dash = self._create_dash()
        self._register_callbacks()
        self.server = FlaskServer(self.flask, self.dash, self.config)
        self.server.start()
        self.request_refresh()

    def request_refresh(self):
        self.refresh_flag = True

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
            if not self.should_refresh:
                return dash.no_update

            if self.time_window is None:
                latest_records = self.history.get_latest(
                    self.config.latest_record_count, pid
                )
            else:
                latest_records = self.history.get_all(self.time_window, pid)
            if not latest_records:
                return go.Figure()

            time_format = lambda t: time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(t)
            )
            timestamps = [
                time_format(record.timestamp_seconds) for record in latest_records
            ]

            fig = go.Figure()

            first_record_time = latest_records[0].timestamp_seconds
            last_record_time = latest_records[-1].timestamp_seconds
            first_time = time_format(first_record_time)
            last_time = time_format(last_record_time)
            elapsed_minutes = (last_record_time - first_record_time) / 60

            if is_percent_data:
                data_map: Dict[str, NamedTuple] = {
                    "cpu": Trace(
                        key="cpu_percent",
                        title="CPU 使用率 (%)",
                        color="#fb7299",
                        data={},
                    ),
                    "gpu": Trace(
                        key="gpu_percent",
                        title="GPU 使用率 (%)",
                        color="#66ccff",
                        data={},
                    ),
                }

                for trace in data_map.values():
                    history_values = [
                        (
                            record.cpu_percent
                            if trace.key == "cpu_percent"
                            else record.gpu_percent
                        )
                        for record in latest_records
                    ]
                    average = sum(history_values) / len(history_values)
                    maximum = max(history_values)
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=history_values,
                            mode="lines+markers",
                            name=trace.title,
                            line=dict(color=trace.color, width=3),
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=[average] * len(latest_records),
                            mode="lines",
                            name=f"平均值 ({trace.title})",
                            line=dict(color=trace.color, dash="dash", width=1),
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=[maximum] * len(latest_records),
                            mode="lines",
                            name=f"最大值 ({trace.title})",
                            line=dict(color=trace.color, dash="longdash", width=1),
                        )
                    )

                prefix = (
                    f"{(self.time_window.end - self.time_window.start) // 60}分钟"
                    if self.time_window
                    else ""
                )
                fig.update_layout(
                    title=f"{prefix}使用率数据 (时间跨度: {first_time} ~ {last_time}, 约合 {elapsed_minutes:.2f} 分钟)",
                    xaxis_title="时间",
                    yaxis_title="使用率 %",
                )
            else:
                data_map: Dict[str, NamedTuple] = {
                    "uss": Trace(
                        key="uss_mb",
                        title="专用内存 (uss) 大小 (MB)",
                        color="rgb(135, 235, 0)",
                        data={},
                    ),
                    "rss": Trace(
                        key="rss_mb",
                        title="驻留集 (rss) 大小 (MB)",
                        color="#fb7299",
                        data={},
                    ),
                    "wset": Trace(
                        key="wset_mb",
                        title="工作集 (wset) 大小 (MB)",
                        color="rgb(251, 196, 33)",
                        data={},
                    ),
                    "pwset": Trace(
                        key="pwset_mb",
                        title="私有工作集 (private) 大小 (MB)",
                        color="#39c5bb",
                        data={},
                    ),
                    "vms": Trace(
                        key="vms_mb",
                        title="虚拟内存 (vms) 大小 (MB)",
                        color="#66ccff",
                        data={},
                    ),
                }

                for trace in data_map.values():
                    history_values = [
                        getattr(record.memory_utilization, trace.key)
                        for record in latest_records
                    ]
                    average = sum(history_values) / len(history_values)
                    minimum = min(history_values)
                    maximum = max(history_values)
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=history_values,
                            mode="lines+markers",
                            name=trace.title,
                            line=dict(color=trace.color, width=3),
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=[average] * len(latest_records),
                            mode="lines",
                            name=f"平均值 ({trace.title})",
                            line=dict(color=trace.color, dash="dash", width=1),
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=[minimum] * len(latest_records),
                            mode="lines",
                            name=f"最小值 ({trace.title})",
                            line=dict(color=trace.color, dash="dot", width=1),
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=timestamps,
                            y=[maximum] * len(latest_records),
                            mode="lines",
                            name=f"最大值 ({trace.title})",
                            line=dict(color=trace.color, dash="longdash", width=1),
                        )
                    )

                prefix = (
                    f"{(self.time_window.end - self.time_window.start) // 60}分钟"
                    if self.time_window
                    else ""
                )
                fig.update_layout(
                    title=f"{prefix}内存数据 (时间跨度: {first_time} ~ {last_time}, 约合 {elapsed_minutes:.2f} 分钟)",
                    xaxis_title="时间",
                    yaxis_title="已用 (MB)",
                )

            self.call_next_tick()
            return fig

        return callback

    def _create_dash(self) -> Tuple[Flask, dash.Dash]:
        flask_app = Flask(__name__)
        dash_app = dash.Dash(
            __name__,
            server=flask_app,
            assets_folder="assets",
            title="KProfiler",
            update_title="KProfiler - 正刷新数据...",
            suppress_callback_exceptions=True,
            prevent_initial_callbacks="initial_duplicate",
        )

        graphs = []
        graphs.append(
            html.Div(
                [
                    html.H2("控制面板"),
                    html.Div(
                        [
                            html.Button("结束程序", id="button-exit", n_clicks=0),
                            html.Button("刷新页面", id="button-refresh", n_clicks=0),
                            html.Button("清屏", id="button-clear", n_clicks=0),
                            html.Div(className="vertical-rule"),
                            html.Button("保存数据", id="button-save", n_clicks=0),
                            html.Button("读取数据", id="button-load", n_clicks=0),
                            html.Div(className="vertical-rule"),
                            html.Button(
                                children="暂停更新", id="button-pause", n_clicks=0
                            ),
                            html.Button("恢复更新", id="button-restore", n_clicks=0),
                            html.Div(className="vertical-rule"),
                            dcc.Input(
                                id="input-time",
                                type="number",
                                min=1,
                                max=7200,
                                step=1,
                            ),
                            html.Span("分钟"),
                            html.Button(
                                "开始计时", id="button-start-timer", n_clicks=0
                            ),
                            html.Button(
                                "清除计时", id="button-remove-timer", n_clicks=0
                            ),
                            html.Span("当前状态: "),
                            html.Span(id="timer-status", children="未在计时"),
                            html.Div(id="exit", style={"display": "none"}),
                            html.Div(id="save-filename", style={"display": "none"}),
                            html.Div(id="save-text", style={"display": "none"}),
                            html.Div(id="load-text", style={"display": "none"}),
                            html.Div(id="message", style={"display": "none"}),
                        ]
                    ),
                ]
            )
        )

        for process in self.processes:
            name = process.name()
            pid = process.pid
            label = self.process_map.get_label(pid)
            graphs.append(
                html.Div(
                    [
                        html.H2(
                            f"{name} {label} (PID={pid}) 数据"
                            if pid != 0
                            else f"{name} 总值"
                        ),
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
                        html.H3("请打开目标进程，然后这里会自动刷新。"),
                        html.H3("提示：进程名大小写一定要匹配~"),
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
        dash_app.clientside_callback(
            ClientsideFunction("main", function_name="exit_program"),
            Output("exit", "children"),
            [Input("button-exit", "n_clicks")],
        )
        dash_app.clientside_callback(
            ClientsideFunction("main", function_name="refresh_page"),
            [Input("button-refresh", "n_clicks")],
        )
        dash_app.clientside_callback(
            ClientsideFunction("main", function_name="handle_save"),
            [Input("save-text", "children"), Input("save-filename", "children")],
        )
        dash_app.clientside_callback(
            ClientsideFunction("main", function_name="handle_load"),
            Output("load-text", "children"),
            [Input("button-load", "n_clicks")],
        )
        dash_app.clientside_callback(
            ClientsideFunction("main", function_name="show_message"),
            [Input("message", "children")],
        )

        def clear_history():
            self.history.records = []

        @dash_app.callback(Input("button-load", "n_clicks"))
        def handle_load(n_clicks):
            if n_clicks > 0:
                pass

        @dash_app.callback(
            Output("save-text", "children"),
            Output("save-filename", "children"),
            Output('message', 'children', allow_duplicate=True),
            [Input("button-save", "n_clicks")],
        )
        def handle_save(n_clicks):
            if n_clicks <= 0:
                return [None, None, dash.no_update]
            text = self.history.serialize()
            filename = f"history-{self.config.target}.csv"
            return [text, filename, f"已下载为{filename}"]

        @dash_app.callback([Input("load-text", "children")])
        def handle_load(text):
            self.history.parse_and_load(text, self.config.history_upperbound)

            def pause_refresh():
                self.should_refresh = False

            self.on_next_tick(pause_refresh)

        @dash_app.callback([Input("button-pause", "n_clicks")])
        def handle_pause(n_clicks):
            if n_clicks > 0:
                self.should_refresh = False

        @dash_app.callback([Input("button-restore", "n_clicks")])
        def handle_restore(n_clicks):
            if n_clicks > 0:
                self.should_refresh = True

        @dash_app.callback(
            [
                Input("button-start-timer", "n_clicks"),
                Input("input-time", "value"),
            ],
        )
        def start_timer(n_clicks, value):
            if n_clicks <= 0:
                self.status_text = "未在计时"
            if value is None or value <= 0 or value > 7200:
                self.status_text = "错误：时间不能超过 7200 分钟"
            now = int(time.time())
            end = now + value * 60
            self.time_window = TimeWindow(start=now, end=end)
            self.status_text = f"正在计时，将在 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))} 结束"

        @dash_app.callback(
            [
                Input("button-remove-timer", "n_clicks"),
            ],
        )
        def remove_timer(n_clicks):
            if n_clicks <= 0:
                return
            self.status_text = "未在计时"
            self.time_window = None

        @dash_app.callback(
            Output("interval-refresh-layout", "n_intervals"),
            Output("message", "children", allow_duplicate=True),
            [Input("button-clear", "n_clicks")],
        )
        def handle_clear(n_clicks):
            if n_clicks > 0:
                clear_history()
                return [1234567, "将在下个刷新周期清屏！"]
            return dash.no_update

        @dash_app.callback(
            Output("timer-status", "children"),
            [Input("interval-refresh-layout", "n_intervals")],
        )
        def handle_update_status(n_intervals):
            prefix = "" if self.should_refresh else "更新已暂停，"
            return prefix + self.status_text

        @dash_app.callback(
            Output("button-refresh", "n_clicks"),
            [Input("interval-refresh-layout", "n_intervals")],
        )
        def poll_refresh(n_intervals):
            if self.refresh_flag:
                self.refresh_flag = False
                return [1]
            return [0]

        @dash_app.callback(
            [Input("exit", "children")],
        )
        def exit_button_callback(n_clicks):
            if n_clicks > 0:
                print("Exiting...")
                ProcessUtils.exit_immediately()

        return flask_app, dash_app
