import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # 更新间隔为1秒
        n_intervals=0
    )
])

@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    # 这里使用你的实时数据更新逻辑
    data = [go.Scatter(x=[1, 2, 3], y=[4, 1, 2], mode='lines+markers')]
    layout = go.Layout(title='实时数据更新图表')
    return {'data': data, 'layout': layout}

if __name__ == '__main__':
    app.run_server(debug=True)
