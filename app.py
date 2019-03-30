import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from sklearn.preprocessing import StandardScaler


def sum_by_date(df):
    """Get total flows by date."""
    return df.groupby('date').f.sum()


CSS = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(external_stylesheets=CSS)
server = app.server

# Load data
df = pd.read_csv('computer_security.csv', parse_dates=['date'])
df = df.loc[df.f < 250_000] # temporarily filter out massive outlier
gbs = [sum_by_date(df.loc[df.l_ipn == i]) for i in df.l_ipn.unique()]


app.layout = html.Div([

        # Dropdown
        dcc.Dropdown(id='dropdown',
                     options=[dict(label=f'IP {i:<10}', value=i)
                              for i in range(1, 11)],
                     value=list(range(1, 11)),
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
    # for i, ip in enumerate(ips, 1):
    #     gb = sum_by_date(ip).head(n_intervals*interval_scalar)

    # for i, gb in enumerate(gbs, 1):
    for i in selections:
        gb = gbs[i-1]
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
        recent = 2*interval_scalar
        if y[-recent:].max() > (10 + y.min()) * 100:
            line_color = 'rgba(193, 66, 66, 1)'
            fill_color = 'rgba(193, 66, 66, .8)'
            trace2 = go.Scatter(
                            x=x[-recent:],
                            y=y[-recent:],
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
