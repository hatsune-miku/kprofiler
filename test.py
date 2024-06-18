from dash import Dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

app = Dash(__name__)

app.layout = html.Div(
    [
        dcc.Interval(id="interval-refresh-layout", interval=1000),  # 每秒触发一次
        html.Button("Refresh", id="should-refresh", n_clicks=0),
        html.Div(id="should-refresh-v"),
    ]
)


class MyApp:
    def __init__(self):
        self.refresh_flag = True

    def setup_callbacks(self, dash_app):
        @dash_app.callback(
            Output("should-refresh-v", "children"),
            [Input("interval-refresh-layout", "n_intervals")],
        )
        def poll_refresh(n_intervals):
            if self.refresh_flag:
                self.refresh_flag = False
                return "1"
            else:
                return "0"


my_app = MyApp()
my_app.setup_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
