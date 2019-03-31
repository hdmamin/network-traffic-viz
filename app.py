import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from sklearn.preprocessing import RobustScaler


CSS = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
STEP = 3
app = dash.Dash(external_stylesheets=CSS)
server = app.server

# Load data and group by IP, then create features to identify outliers.
scaler = RobustScaler()
df = pd.read_csv('computer_security.csv', parse_dates=['date'])
gb = df.groupby(['l_ipn', 'date']).f.sum()
gbs = [pd.DataFrame(gb[i]) for i in range(10)]

# Create slice indices for plotting many traces. Use step+1 so there are no
# gaps between traces.
slices = []
for g in gbs:
    g['scaled'] = scaler.fit_transform(g[['f']])
    g['prev_ratio'] = g.f / g.f.shift(1, fill_value=np.inf)
    slice_ = [slice(i, i + STEP + 1) for i in range(0, g.shape[0], STEP)]
    slices.append(slice_)

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
                     max_intervals=np.ceil(df.date.nunique() / STEP)
                     ),

        # Div containing graphs.
        html.Div(id='g1')
])


@app.callback(Output('g1', 'children'),
              [Input('interval', 'n_intervals'),
               Input('dropdown', 'value')])
def update_g1(n_intervals, selections):
    max_idx = n_intervals * STEP
    graphs = []

    # Generate plot for each ip selected from dropdown.
    for i in selections:
        g = gbs[i].head(max_idx)
        line_colors = ['rgba(85, 191, 63, 1)', 'rgba(193, 66, 66, 1)']
        colors = ['rgba(85, 191, 63, 0.75)', 'rgba(193, 66, 66, .8)']
        traces = []
        for s in slices[i]:
            current_slice = g.iloc[s]
            x = current_slice.index
            y = current_slice.f
            c_idx = any((current_slice.scaled > 1.5) &
                        (current_slice.prev_ratio > 10))
            trace = go.Scatter(
                       x=x,
                       y=y,
                       fill='tozeroy',
                       mode='lines',
                       fillcolor=colors[c_idx],
                       line={'width': 3,
                             'color': line_colors[c_idx]}
                       )
            traces.append(trace)

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
