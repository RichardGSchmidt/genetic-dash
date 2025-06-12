import datetime
import os
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import plotly.express as px
import plotly.graph_objects as go
from gen_utils import get_matrices, load_packages, load_distances
import networkx as nx
import pandas as pd
from model.genetic_algorithm import genetic_algorithm

#Import Data
addresses = pd.read_csv('./data/addresses.csv')
packages = load_packages()
d_matrix = load_distances()
port = int(os.environ.get('PORT', 8050))

#store best solutions in memory
global best_solutions_memory
best_solutions_memory = []


# Incorporate modified Dash CSS Styleguide found at https://codepen.io/chriddyp/pen/bWLwgP
stylesheets = ['./dashstyles.css']
app = Dash(external_stylesheets=stylesheets)


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

def plot_map(G, addresses_df, genome=None):
    pos = {
        i: (addresses_df.iloc[i]['longitude'], addresses_df.iloc[i]['latitude'])
        for i in range(len(addresses_df))
    }

    edge_traces = []
    if genome is not None:
        colors = px.colors.qualitative.Plotly
        for i, truck in enumerate(genome.trucks):
            if not truck.packages:
                continue
            color = colors[i % len(colors)]
            route = [0]
            for pkg_id in truck.packages:
                pkg = genome.packages.get(pkg_id)
                if pkg and pkg.address in pos:
                    route.append(pkg.address)
            route.append(0)

            edge_trace = go.Scattermapbox(
                lon=[pos[pt][0] for pt in route],
                lat=[pos[pt][1] for pt in route],
                mode='lines',
                line=dict(width=2, color=color),
                name=f'Truck {i+1}'
            )
            edge_traces.append(edge_trace)
    else:
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace = go.Scattermapbox(
                lon=[x0, x1],
                lat=[y0, y1],
                mode='lines',
                line=dict(width=0.5, color='gray'),
                name='Default Routes'
            )
            edge_traces.append(edge_trace)

    # Add node points
    node_trace = go.Scattermapbox(
        lon=[pos[i][0] for i in G.nodes()],
        lat=[pos[i][1] for i in G.nodes()],
        mode='markers+text',
        marker=dict(size=10, color='red'),
        text=[str(i) for i in G.nodes()],
        hovertext=[
            f"{addresses_df.iloc[i]['location']}<br>{addresses_df.iloc[i]['address']}"
            for i in G.nodes()
        ],
        textposition="top center",
        name='Locations'
    )

    fig = go.Figure(data=edge_traces + [node_trace])

    fig.update_layout(
        title='Salt Lake City Delivery Network Map',
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            style='open-street-map',  # free and doesn't require token
            center=dict(lat=40.6908, lon=-111.8910),
            zoom=10
        ),
        margin=dict(t=30, b=10, l=10, r=10)
    )

    return fig


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
    fig = go.Figure(data=edge_traces + [node_trace])

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
        dcc.Input(id='population-size',type='number',min=10,max=32000,step=10,value=100),

        html.Label('Generations'),
        dcc.Input(id='generations',type='number',min=1,max=50000,step=1,value=16),

        html.Label('Crossover Rate'),
        dcc.Input(id='crossover-rate',type='number',min=0.0,max=1,step=0.05,value=0.8),

        html.Label('Mutation Rate'),
        dcc.Input(id='mutation-rate',type='number',min=0.0,max=1,step=0.01,value=0.05),



        html.Br(),
        html.Button('Run Genetics', id='run-genetics', n_clicks=0),
        dcc.Store(id='run-complete-flag', data=0),
        html.Div(id='output-summary')
    ], style={'padding':'20px', 'border':'1px solid black', 'margin':'10px'}),

    html.Div(className='row', children=[
        html.Div([
            dcc.Graph(id='network-graph')
        ], style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.H4("Truck Loadouts"),
            html.Div(id='truck-loadouts', style={
                'overflowY': 'scroll', 'maxHeight': '500px',
                'border': '1px solid #ccc', 'padding': '10px'
            })
        ], style={'width': '28%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'})
    ]),
    html.Div(className='row', children='View Best Solutions', style={'textAlign': 'center', 'fontSize': 20}),
    dcc.Slider(
        id='solution-slider',
        min=0,
        max=0,  # We'll update this after GA run
        step=1,
        value=0,
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    html.Div(className='row', children='Cost Per Best Solution', style={'textAlign':'center'}),
    dcc.Graph(id='graph-content'),
    dcc.Graph(id='generation-track')
])

@callback(
    Output('network-graph', 'figure'),
    Input('solution-slider', 'value')
)
def update_network_graph(solution_idx):
    if 0 <= solution_idx < len(best_solutions_memory):
        genome = best_solutions_memory[solution_idx]['genome']
        return plot_map(G, addresses_df=addresses, genome=genome)
    else:
        return plot_map(G, addresses_df=addresses, genome=None)


@callback(
    Output('graph-content', 'figure'),
    Input('run-complete-flag', 'data'),
)
def update_graph(n_clicks):
    if not best_solutions_memory or n_clicks == 0:
        return go.Figure()

    # Build DataFrame from memory
    df = pd.DataFrame([
        {
            'generation': sol['generation'],
            'late_cost': len(sol['genome'].late_packages) * 20,
            'mileage_cost': sum(t.mileage for t in sol['genome'].trucks),
            'trucks_cost': sum(1 for t in sol['genome'].trucks if t.packages) * 20
        }
        for sol in best_solutions_memory
    ])

    df = df.sort_values(by='generation').reset_index(drop=True)
    df['total_cost'] = df['late_cost'] + df['mileage_cost'] + df['trucks_cost']
    df['index'] = df.index

    # Build stacked line chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['late_cost'],
        mode='lines',
        name='Late Packages Cost',
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['mileage_cost'],
        mode='lines',
        name='Mileage Cost',
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['trucks_cost'],
        mode='lines',
        name='Trucks Cost',
        stackgroup='one'
    ))

    fig.update_layout(
        title='Stacked Line Chart of Total Cost per Best Solution',
        xaxis_title='Solution Index',
        yaxis_title='Cost',
        hovermode='x unified'
    )

    return fig


@callback(
    Output('truck-loadouts', 'children'),
    Input('solution-slider', 'value')
)
def update_truck_loadout(solution_idx):
    if 0 <= solution_idx < len(best_solutions_memory):
        genome = best_solutions_memory[solution_idx]['genome']
        generation = best_solutions_memory[solution_idx]['generation']
        truck_displays = []
        total_mileage = 0.0
        for i, truck in enumerate(genome.trucks):
            if not truck.packages:
                continue
            else:
                total_mileage += truck.mileage

            pkg_lines = []
            for pkg_id, delivered_time in truck.delivery_log:
                pkg = genome.packages.get(pkg_id)
                addr = addresses.iloc[pkg.address]['location']
                due = "EOD" if pkg.time_due == datetime.timedelta(hours=23, minutes=59, seconds=59) else format_time(
                    pkg.time_due)
                delivered = format_time(delivered_time)
                late = delivered_time > pkg.time_due
                line = html.Span([
                    f"Package {pkg_id} → {addr} (Due: {due}, Delivered: ",
                    html.Span(delivered, style={'color': 'red' if late else 'black'}),
                    ")"
                ])
                pkg_lines.append(line)
            truck_displays.append(html.Div([
                html.H5(f"Truck {i+1} (Mileage: {truck.mileage:.1f})",),
                html.Ul([html.Li(line) for line in pkg_lines])
            ], style={'marginBottom': '20px'}))
        #this arranges everything together for display
        truck_displays = html.Div([
            html.H2(f'{total_mileage:.1f} miles'),
            html.H3(f'Solution: {solution_idx + 1} Generation: {generation}'),
            html.Pre(str(genome)),
            html.Div(truck_displays)
        ])

        return truck_displays

    return "No solution selected."


@callback(
    Output('generation-track', 'figure'),
    Input('run-complete-flag', 'data')
)
def update_generation_graph(_):
    if not best_solutions_memory:
        return go.Figure()

    df = pd.DataFrame([
        {
            'generation': sol['generation'],
            'total_cost': sol['total_cost']
        }
        for sol in best_solutions_memory
    ])

    df = df.sort_values(by='generation').reset_index(drop=True)
    df['cost_improvement'] = df['total_cost'].shift(1) - df['total_cost']
    df['cost_improvement'] = df['cost_improvement'].fillna(0)

    fig = px.bar(
        df,
        x='generation',
        y='cost_improvement',
        title='Improvement per Generation',
        labels={'generation': 'Generation', 'cost_improvement': 'Cost Improvement'},
        color='cost_improvement',
        color_continuous_scale='Bluered'
    )

    fig.update_layout(
        yaxis_title='Improvement (ΔCost)',
        xaxis_title='Generation',
        hovermode='x unified'
    )

    return fig


@callback(
    Output('output-summary', 'children'),
    Output('solution-slider', 'max'),
    Output('solution-slider', 'value'),
    Output('run-complete-flag', 'data'),
    Input('run-genetics', 'n_clicks'),
    State('num-trucks', 'value'),
    State('truck-capacity', 'value'),
    State('truck-speed', 'value'),
    State('population-size', 'value'),
    State('generations', 'value'),
    State('crossover-rate', 'value'),
    State('mutation-rate', 'value'),
    prevent_initial_call=True
)
def run_genetic_algorithm(n_clicks, num_trucks, truck_capacity, truck_speed,
                          population_size, generations, crossover_rate, mutation_rate):
    if n_clicks == 0:
        return "", 0

    # Run the algorithm
    global best_solutions_memory
    best_solutions_memory = []
    best_cost = None
    matrices = get_matrices(truck_speed)
    _, best_cost = genetic_algorithm(
        truck_count=num_trucks,
        truck_capacity=truck_capacity,
        truck_speed=truck_speed,
        packages=packages,
        matrices=matrices,
        pop_size=population_size,
        generations=generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        best_solutions_out=best_solutions_memory
    )

    # Collect results
    final_solution = best_solutions_memory[-1]['genome']

    late_count = len(final_solution.late_packages)
    mileage = sum(truck.mileage for truck in final_solution.trucks)
    active_trucks = sum(1 for truck in final_solution.trucks if truck.packages)

    return(
        html.Div([
            html.P(f"Best Total Cost: {best_cost:.2f}"),
            html.P(f"Late Packages: {late_count}"),
            html.P(f"Total Mileage: {mileage:.2f}"),
            html.P(f"Trucks Used: {active_trucks}")
        ]),
        max(0,len(best_solutions_memory)-1), # slider max
        len(best_solutions_memory) - 1,
        n_clicks #makes the charts update

    )
def format_time(t):
    if isinstance(t, datetime.timedelta):
        total_minutes = int(t.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02}:{minutes:02}"
    return str(t)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=port,debug=True)
