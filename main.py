import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# load dataset
df = pd.read_csv("Assignment7Dataset.csv")
# create list of countries that have won
winners = df['Winner'].value_counts().reset_index()
winners.columns = ['Country', 'Wins']

# get all countries from plotlys built in list
all_countries = px.data.gapminder().query("year == 2007")["country"].unique()

# build full dataset including countries with 0 wins (to color countries with 0 wins differently for better visibility)
full_data = pd.DataFrame({'Country': all_countries})
full_data = full_data.merge(winners, how='left', on='Country')
full_data['Wins'] = full_data['Wins'].fillna(0).astype(int).astype(str) # convert to string to be plotted as discrete vs continuous

# predefined discrete color map (white for countries with 0, then gradient from light to dark blue for >0)
color_map = {
    "0": "white",
    "1": "#fee5d9",
    "2": "#fcae91",
    "3": "#fb6a4a",
    "4": "#de2d26",
    "5": "#a50f15"
}

def generate_choropleth():
    
    
    fig = px.choropleth(
        full_data,
        locations="Country",
        locationmode="country names",
        color="Wins",
        color_discrete_map=color_map,
        category_orders={"Wins": ["0", "1", "2", "3", "4", "5", "6"]},
        title="FIFA World Cup Wins by Country",
        height=800,
        width=1200
    )
    fig.update_geos(showcountries=True, showframe=False, projection_type="natural earth", bgcolor='white',countrycolor="Black")
    return fig

# dash app setup
app = dash.Dash(__name__)
server = app.server
app.layout = html.Div([
    html.H1("FIFA World Cup Dashboard"),
    dcc.Graph(id='choropleth', figure=generate_choropleth()),
    html.Div([
        html.Label("Select a Country:"),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{"label": c, "value": c} for c in sorted(winners['Country'].unique())],
            value='Brazil'
        ),
        html.Div(id='country-output')
    ], style={"margin-top": "5px"}),
    html.Div([
        html.Label("Select a Year:"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{"label": y, "value": y} for y in sorted(df['Year'].unique())],
            value = 2022
        ),
        html.Div(id='year-output')
    ], style={"margin-top": "20px"})
], style={"backgroundColor": "white", "padding": "20px"})

# callbacks
@app.callback(
    Output('country-output', 'children'),
    Input('country-dropdown', 'value')
)

def update_country_output(selected_country):
    wins = winners[winners['Country'] == selected_country]['Wins'].values
    num_wins = int(wins[0]) if len(wins) > 0 else 0
    return f"{selected_country} has won the World Cup {num_wins} times."

@app.callback(
    Output('year-output', 'children'),
    Input('year-dropdown', 'value')
)

def update_year_output(selected_year):
    row = df[df['Year'] == selected_year].iloc[0]
    return f"In {selected_year}, the winner has {row['Winner']} and the runner-up was {row['Runner-up']}."

# run app
if __name__ == '__main__':
    app.run(debug=True)