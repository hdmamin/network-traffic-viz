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
outlier_idx = []
for g in gbs:
    g['scaled'] = scaler.fit_transform(g[['f']])
    g['prev_scaled'] = g.scaled.shift(1, 0)
    g['prev'] = g.f.shift(1, fill_value=np.inf)
    g['prev_ratio'] = g.f / g.prev

app.layout = html.Div([

        # Dropdown
        dcc.Dropdown(id='dropdown',
                     options=[dict(label=f'IP {i:<10}', value=i)
                              for i in range(10)],
                     value=list(range(4)),
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
        colors = ['rgba(85, 191, 63, 1)', 'rgba(193, 66, 66, 1)']

        # Generate plot traces.
        traces = []
        df_neg = g.where(((g.scaled <= 2.25) | (g.prev_ratio <= 10)) &
                         (g.prev_scaled <= 2.25), None)
        trace_all = go.Scatter(
                        x=g.index,
                        y=g.f,
                        fill='tonexty',
                        fillcolor=colors[1],
                        mode='lines',
                        connectgaps=False,
                        hoverinfo='y',
                        line={'width': 3,
                              'color': line_colors[1]}
                        )

        trace_neg = go.Scatter(
                       x=df_neg.index,
                       y=df_neg.f,
                       fill='tozeroy',
                       fillcolor=colors[0],
                       mode='lines',
                       connectgaps=False,
                       hoverinfo='y',
                       line={'width': 3,
                             'color': line_colors[0]}
                       )

        traces.extend([trace_all, trace_neg])

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

    # Format html output.
    output = []
    for k, graph in enumerate(graphs):
        if k % 2 == 0:
            row = html.Div([], className='row')
        row.children.append(html.Div(graph, className='six columns'))
        if k % 2 == 1:
            output.append(row)
    return output

if __name__ == '__main__':
    app.run_server(port=5000, debug=True)
