from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
from gen_utils import get_matrices, load_packages
import networkx as nx
import pandas as pd
from model.genetic_algorithm import genetic_algorithm

#Import Data
best_solutions = pd.read_csv('./data/best_solutions.csv')
d_matrix, t_matrix = matrices = get_matrices()
addresses = pd.read_csv('./data/addresses.csv')
packages = load_packages()

#store best solutions in memory
global best_solutions_memory
best_solutions_memory = []


# Incorporate CSS
stylesheets = ['./dashstyles.css']
app = Dash(external_stylesheets=stylesheets)


# Compute cumulative costs for stacking
best_solutions['late_cost'] = best_solutions['late_packages'] * 20
best_solutions['mileage_cost'] = best_solutions['mileage']
best_solutions['trucks_cost'] = best_solutions['trucks_used'] * 200
best_solutions['total_cost'] = best_solutions['trucks_cost'] + best_solutions['late_cost'] + best_solutions['mileage_cost']


#creates a network graph from a distance matrix
def create_graph(distance_matrix):
    G = nx.Graph()
    n = len(distance_matrix)

    # Add Nodes
    for i in range(n):
        G.add_node(i, label=f"Location {i}")

    # Add Edges
    for i in range(n):
        for j in range(i+1, n):
            weight = distance_matrix[i][j]
            G.add_edge(i, j, weight=weight)
    return G

def plot_map(G, addresses_df):
    pos = {}
    for i in range(len(addresses_df)):
        lat = addresses_df.iloc[i]['latitude']
        lon = addresses_df.iloc[i]['longitude']
        pos[i] = (lon, lat)

    #edge tracing lists
    edge_x = []
    edge_y = []
    edge_weights = []

    for edge in G.edges():
        x0,y0 = pos[edge[0]]
        x1,y1 = pos[edge[1]]
        edge_x.extend([x0,x1,None])
        edge_y.extend([y0,y1,None])
        weight = G[edge[0]][edge[1]]['weight']
        edge_weights.append(weight)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines',
        name='Routes'
    )

    #Nodes tracing lists
    node_x = []
    node_y = []
    node_text = []
    node_info = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Get address info if available
        location_name = addresses_df.iloc[node]['location']
        address = addresses_df.iloc[node]['address']
        node_info.append(f"Location {node}<br>{location_name}<br>{address}")
        node_text.append(str(node))


    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_info,
        text=node_text,
        textposition="middle center",
        marker=dict(
            color ='red',
            size = 12,
            line=dict(width=2, color='white')
        ),
        name='Delivery Locations'
    )

    #Create the figure
    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title='Salt Lake City Delivery Network Map',
        font=dict(size=16),
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[dict(
            text="Geographic map showing delivery locations and routes in Salt Lake City area.",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002,
            xanchor='left', yanchor='bottom',
            font=dict(size=12)
        )],
        xaxis=dict(
            title="Longitude",
            showgrid=True,
            zeroline=False,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="Latitude",
            showgrid=True,
            zeroline=False,
            gridcolor='lightgray',
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor='white'
    )

    return fig


# Create the network graph from distance matrix
G = create_graph(d_matrix)

app.layout = html.Div([
    html.Div(className='row', children='Genetic-Dash',style={'textAlign':'center','fontSize':30}),

    html.Div([
        html.Label('No. of Trucks (1-50)'),
        dcc.Input(id='num-trucks',type='number',min=1,max=50,step=1,value=3),

        html.Label("Truck Capacity"),
        dcc.Input(id='truck-capacity',type='number',min=1,max=100,step=1,value=14),

        html.Label("Truck Speed"),
        dcc.Input(id='truck-speed',type='number',min=5.0,max=100.0,step=0.1,value=18.0),

        html.Br(),
        html.Label('Population Size'),
        dcc.Input(id='population-size',type='number',min=10,max=8000,step=10,value=5000),

        html.Label('Generations'),
        dcc.Input(id='generations',type='number',min=1,max=2000,step=1,value=32),

        html.Label('Crossover Rate'),
        dcc.Input(id='crossover-rate',type='number',min=0.0,max=1,step=0.05,value=0.9),

        html.Label('Mutation Rate'),
        dcc.Input(id='mutation-rate',type='number',min=0.0,max=1,step=0.01,value=0.02),



        html.Br(),
        html.Button('Run Genetics', id='run-genetics', n_clicks=0),
        html.Div(id='output-summary')
    ], style={'padding':'20px', 'border':'1px solid black', 'margin':'10px'}),

    html.Div(className='row', children='Map', style={'textAlign':'center','fontSize':30}),
    dcc.Graph(id='network-graph'),
    html.Div(className='row', children='Cost Per Best Solution', style={'textAlign':'center'}),
    dcc.Graph(id='graph-content'),
    dcc.Graph(id='generation-track')
])

@callback(
    Output('network-graph', 'figure'),
    Input('network-graph', 'id'),
)
def update_network_graph(value):
    return plot_map(G, addresses_df=addresses)

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
@callback(
    Output('output-summary', 'children'),
    Input('run-genetics', 'n_clicks'),
    Input('num-trucks', 'value'),
    Input('truck-capacity', 'value'),
    Input('truck-speed', 'value'),
    Input('population-size', 'value'),
    Input('generations', 'value'),
    Input('crossover-rate', 'value'),
    Input('mutation-rate', 'value')
)
def run_genetic_algorithm(n_clicks, num_trucks, truck_capacity, truck_speed,
                          population_size, generations, crossover_rate, mutation_rate):
    if n_clicks == 0:
        return ""

    # Run the algorithm
    global best_solutions_memory
    best_solutions_memory = []
    best_cost = None
    _, best_cost = genetic_algorithm(
        truck_count=num_trucks,
        truck_capacity=truck_capacity,
        truck_speed=truck_speed,
        packages=packages,
        matrices=(d_matrix, t_matrix),
        pop_size=population_size,
        generations=generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        best_solutions_out=best_solutions_memory
    )

    # Collect results
    late_count = len(best_solution.late_packages)
    mileage = sum(truck.mileage for truck in best_solution.trucks)
    active_trucks = sum(1 for truck in best_solution.trucks if truck.packages)

    return html.Div([
        html.P(f"Best Total Cost: {best_cost:.2f}"),
        html.P(f"Late Packages: {late_count}"),
        html.P(f"Total Mileage: {mileage:.2f}"),
        html.P(f"Trucks Used: {active_trucks}")
    ])

if __name__ == '__main__':
    app.run(debug=True)
