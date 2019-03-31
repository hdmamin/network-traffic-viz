import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from sklearn.preprocessing import RobustScaler


CSS = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(external_stylesheets=CSS)
server = app.server

# Load and process data.
df = pd.read_csv('computer_security.csv', parse_dates=['date'])
gbs = df.groupby(['l_ipn', 'date']).f.sum()

app.layout = html.Div([

        # Dropdown
        dcc.Dropdown(id='dropdown',
                     options=[dict(label=f'IP {i:<10}', value=i)
                              for i in range(10)],
                     # value=list(range(1, 11)),
                     value=[0, 1],
                     multi=True
        ),

        # Interval Component
        dcc.Interval(id='interval',
                     n_intervals=0,
                     interval=1_000,
                     max_intervals=df.date.nunique() // 3),

        # Div containing graphs.
        html.Div(id='g1')
])


@app.callback(Output('g1', 'children'),
              [Input('interval', 'n_intervals'),
               Input('dropdown', 'value')])
def update_g1(n_intervals, selections):
    interval_scalar = 3
    max_idx = n_intervals * interval_scalar
    graphs = []

    # Generate plot for each ip selected from dropdown.
    for i in selections:
        gb = gbs[i]
        x = gb.head(max_idx).index
        y = gb.head(max_idx).values

        color = 'green'
        traces = [go.Scatter(
                            x=x,
                            y=y,
                            fill='tozeroy',
                            mode='lines',
                            line={'width': 3,
                                  'color': color}
                            )]

        # Detect outliers and change color.
        if y[-interval_scalar:].max() > (10 + y.min()) * 100:
            line_color = 'rgba(193, 66, 66, 1)'
            fill_color = 'rgba(193, 66, 66, .8)'
            trace2 = go.Scatter(
                            x=x[-interval_scalar:],
                            y=y[-interval_scalar:],
                            fill='tozeroy',
                            mode='lines',
                            line={'width': 3,
                                  'color': line_color},
                            fillcolor=fill_color
                            )
            traces.append(trace2)

        # Create layout dictionary to pass to Graph object.
        layout = dict(title=f'IP {i}',
                      height=400,
                      xaxis={'title': 'Date'},
                      yaxis={'title': 'Total Flows'},
                      showlegend=False
                      )

        graph = dcc.Graph(
            figure=go.Figure(data=traces,
                             layout=layout)
        )

        graphs.append(graph)
    return graphs


if __name__ == '__main__':
    app.run_server(port=5000, debug=True)
