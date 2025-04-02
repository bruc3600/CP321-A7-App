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

# group dataset by 'Winner' to collect years, and average attendance
grouped = (
    df.groupby('Winner')
    .agg({
        'Year': lambda x: ', '.join(x.astype(str)),  # all years in a single string
          'Attendance': lambda x: x.str.replace(',', '').astype(float).mean()  # numeric avg
      })
      .reset_index()
)
grouped.columns = ['Country', 'WinYears', 'AvgAttendance']

# merge winners and grouped data into full_data variable to be used for choropleths
full_data = winners.merge(grouped, how='left', on='Country')


def generate_choropleth_wins():
    # setup choropleth for Wins by Country
    fig = px.choropleth(
        full_data,
        locations="Country",
        locationmode="country names",
        color="Wins",
        color_continuous_scale=px.colors.sequential.Teal, # use Teal sequential color for better visibility; other color mapping makes it hard to differentiate countries with no wins to countries with 1 win.
        category_orders={"Wins": ["1", "2", "3", "4", "5"]},
        title="FIFA World Cup Wins by Country",
        hover_name="Country",
        hover_data={
            "Wins": True
        },
        height=800,
        width=1200
    )
    # update layout to ensure the legend shows a discrete vs a continuous legend (i.e. 1.5 wins doesn't make sense)
    fig.update_layout(
        coloraxis_colorbar=dict(
            tickmode='array',
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['1', '2', '3', '4', '5'],
            title='Wins'
        )
    )
    # clean map design to show countries, hide the frame and define the background color
    fig.update_geos(
        showcountries=True, 
        showframe=False, 
        projection_type="natural earth", 
        bgcolor='white')
    return fig


def generate_choropleth_yearly(selected_year):
    # get the single row for the chosen year and define the winner and runner-up for that row
    row = df[df['Year'] == selected_year].iloc[0]
    winner = row['Winner']
    runner_up = row['Runner-up']
    
    # build a dataframe of all countries that have won
    year_df = pd.DataFrame({'Country': winners['Country']})
    
    # assign each country as 'Winner', or 'Runner-up'
    def label_country(country):
        if country == winner:
            return 'Winner'
        elif country == runner_up:
            return 'Runner-up'
    
    year_df['Status'] = year_df['Country'].apply(label_country)
    
    # add empty placeholders for hover tooltips
    year_df['Score'] = ''
    year_df['Venue'] = ''
    year_df['Attendance'] = ''
    
    # fill in details for the winner and runnerup
    year_df.loc[year_df['Country'] == winner, ['Score', 'Venue', 'Attendance']] = (
        row['Score'], row['Venue'], row['Attendance']
    )
    year_df.loc[year_df['Country'] == runner_up, ['Score', 'Venue', 'Attendance']] = (
        row['Score'], row['Venue'], row['Attendance']
    )

    # define color map to be used to highlight the status of each winner, runner up
    color_map = {
        'Winner': 'green', # green used for win
        'Runner-up': 'red' # red used for loss (or runner-up)
    }
    
    # create choropleth map for the specified year to showcase winner and runnerup
    fig = px.choropleth(
        year_df,
        locations='Country',
        locationmode='country names',
        color='Status',
        color_discrete_map=color_map, # use predefined color map
        hover_name='Country',
        hover_data={ # show more details on the game, such as score, where the venue was, and the attendance
            'Status': False,        
            'Score': True,
            'Venue': True,
            'Attendance': True,
        },
        title=f"Yearly Final: {selected_year}",
        height=800,
        width=1200
    )
    
    # format the map design (same as other function)
    fig.update_geos(
        showcountries=True,
        showframe=False,
        projection_type="natural earth",
        bgcolor='white'
    )
    return fig

# dash app setup
app = dash.Dash(__name__)
server = app.server # for deployment on render.com

# define the html layout for the dashboard
app.layout = html.Div([
    html.H1("FIFA World Cup Dashboard"), # title
    html.H2("Note: Selecting 'Yearly Final' mode will use the Year selector box at the bottom."), # note for how to use the selection mode
    html.Label("Select Mode:"), # select mode label and following radio buttons
    dcc.RadioItems(
        id='mode-selector',
        options=[{'label': 'Wins by Country', 'value': 'wins'},
            {'label': 'Yearly Final',   'value': 'yearly'}
        ],
        value='wins',  # default
        inline=True
    ),
    html.Div([
        html.Label("Select a Country to see its Number of Wins:"), # dropdown for country selection (to show # of wins for that country)
        dcc.Dropdown(
            id='country-dropdown',
            options=[{"label": c, "value": c} for c in sorted(winners['Country'].unique())],
            value='Brazil'
        ),
        html.Div(id='country-output') # space for the output (i.e. said country has x wins)
    ], style={"margin-top": "5px"}),
    html.Div([
        html.Label("Select a Year:"), # dropdown for year selection to show who won, runner-up for that year, and also to be used as year selection for yearly mode (which generates separate choropleth)
        dcc.Dropdown(
            id='year-dropdown',
            options=[{"label": y, "value": y} for y in sorted(df['Year'].unique())],
            value = 2022
        ),
        html.Div(id='year-output') # space for the output (i.e. winner for said year is...)
    ], style={"margin-top": "20px"}),
    dcc.Graph(id='choropleth'), # placeholder for the choropleth (whichever one is selected)
], style={"backgroundColor": "white", "padding": "20px"})

# callback to update map based on mode and selected year
@app.callback(
    Output('choropleth', 'figure'),
    [Input('mode-selector', 'value'),
     Input('year-dropdown', 'value')]
)

# function for mode selector; default is 'wins' mode, other mode is 'yearly' mode.
def update_choropleth(mode, selected_year):
    if mode == 'wins':
        return generate_choropleth_wins()  # generate default choropleth (shows all countries which won, with color scheme to show higher / lower wins per country)
    else:
        return generate_choropleth_yearly(selected_year) # generate secondary choropleth which shows for the year selected, the winner, runner-up on the map, with details such as attendance, score, etc.
    
# callback to show total number of wins for selected country
@app.callback(
    Output('country-output', 'children'),
    Input('country-dropdown', 'value')
)

# function to display the number of wins for selected country
def update_country_output(selected_country):
    wins = winners[winners['Country'] == selected_country]['Wins'].values
    num_wins = int(wins[0]) if len(wins) > 0 else 0
    return f"{selected_country} has won the World Cup {num_wins} times."

# callback to show winner and runnerup for selected year
@app.callback(
    Output('year-output', 'children'),
    Input('year-dropdown', 'value')
)

# function to display winner and runnerup for selected year
def update_year_output(selected_year):
    row = df[df['Year'] == selected_year].iloc[0]
    return f"In {selected_year}, the winner has {row['Winner']} and the runner-up was {row['Runner-up']}."

# run app
if __name__ == '__main__':
    app.run(debug=True)