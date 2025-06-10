from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
from gen_utils import get_matrices
import networkx as nx
import pandas as pd

#Import Data
best_solutions = pd.read_csv('./data/best_solutions.csv')

# Incorporate CSS
stylesheets = ['./dashstyles.css']
app = Dash(external_stylesheets=stylesheets)


# Compute cumulative costs for stacking
best_solutions['late_cost'] = best_solutions['late_packages'] * 20
best_solutions['mileage_cost'] = best_solutions['mileage']
best_solutions['trucks_cost'] = best_solutions['trucks_used'] * 200
best_solutions['total_cost'] = best_solutions['trucks_cost'] + best_solutions['late_cost'] + best_solutions['mileage_cost']

app.layout = [
    html.Div(className='row', children='Genetic-Dash',style={'textAlign':'center','fontSize':30}),
    html.Div(className='row', children='Map', style={'textAlign':'center','fontSize':30}),
    html.Div(className='row', children='Cost Per Best Solution', style={'textAlign':'center'}),
    dcc.Graph(id='graph-content'),
    dcc.Graph(id='generation-track')
]

@callback(
    Output('graph-content', 'figure'),
    Input('graph-content', 'id')
)
def update_graph(value):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=best_solutions['index'],
        y=best_solutions['late_cost'],
        mode='lines',
        name='Late Packages Fee Refunds',
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=best_solutions['index'],
        y=best_solutions['mileage_cost'],
        mode='lines',
        name='Mileage Cost',
        stackgroup='one'
    ))


    fig.add_trace(go.Scatter(
        x=best_solutions['index'],
        y=best_solutions['trucks_cost'],
        mode='lines',
        name='Trucks Cost',
        stackgroup='one'
    ))

    fig.update_layout(title='Stacked Line Chart of Total Costs of each Best Solution',
                      xaxis_title='Solution Count',
                      yaxis_title='Costs')

    return fig

@callback(
    Output('generation-track', 'figure'),
    Input('generation-track', 'id')
)
def update_generation_graph(value):
    fig = px.bar(
        best_solutions,
        x='index',
        y='generation',
        color='generation',
        title='Generation Timeline',
        labels={'index': 'Solution Count', 'generation': 'Generation'},
        color_continuous_scale='Cividis'
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)
