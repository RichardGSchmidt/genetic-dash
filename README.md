# Genetic Algorithm Dashboard

A Dash-based visualization dashboard for genetic algorithm results, showing cost breakdown and generation tracking.

## Installation

1. Clone this repository:
```bash
git https://github.com/RichardGSchmidt/genetic-dash.git
cd genetic-dash
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the dashboard:
```bash
python genetic-dash.py
```

The dashboard will be available at `http://127.0.0.1:8050/`

## Data Requirements

The application expects:
- `./data/best_solutions.csv` - Contains genetic algorithm results
- `./data/distances.csv` - Distance matrix for routing calculations
- `./dashstyles.css` - CSS styling file

## Features

- Stacked line chart showing cost breakdown (late packages, mileage, trucks)
- Generation timeline bar chart
- Interactive Plotly visualizations