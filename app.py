#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  7 19:18:43 2018

@author: beaubritain, Richard Decal
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np

import logging

LOGGING_FORMAT = '%(asctime)-15s  %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT)

# Import your dataframe from a csv with pandas
df = pd.read_csv('kiva_loans.csv')

##### Beau graphs
# subset for important columns
"""df = df[['term_in_months', 'loan_amount', 'lender_count', 'funded_amount',
         'borrower_genders', 'repayment_interval', 'country', 'date',
         'activity']]"""
# subset for top 2 (number of loans) country values and USA to compare to
country_values = ['Philippines', 'Kenya', 'United States']
Beau_df = df[df['country'].isin(country_values)]
# sample to improve speed
a = Beau_df.sample(5000)

# len(kiva.activity.unique()) #shows there are 163 unique activities

top5 = df.groupby('activity').size().sort_values(ascending=False)[
       0:5]  # lets look at top 5
######## /Beau graphs


###### Richard maps
# converting dates from string to DateTime objects gives nice tools
df['date'] = pd.to_datetime(df['date'])
# for example, we can turn the full date into just a year
df['year'] = df.date.dt.year
# then convert it to integers so you can do list comprehensions later
# astype(int) expects a strings, so we need to go Period -> str -> int
# we want ints so we can find the min, max, etc later
df['year'] = df.year.astype(str).astype(int)

# This is our features of interest for mapping
# I grouped by year first so that I can then filter by year simply with just
# df.loc[2014]
countries_funded_amount = df.groupby(['year', 'country']).size()
######


logging.debug("creating gender columns...")
df["num_male"] = df["borrower_genders"].map(lambda row: sum(gender == "male" for gender in str(row).split(", ")))
df["num_female"] = df["borrower_genders"].map(lambda row: sum(gender == "female" for gender in str(row).split(", ")))
df["num_gendered_borrowers"] = df["borrower_genders"].map(lambda row: len([person for person in str(row).split(", ")]))
df["pct_male"] = df["num_male"] / df["num_gendered_borrowers"]
df["pct_female"] = df["num_female"] / df["num_gendered_borrowers"]

logging.debug("creating gender statistics...")

num_borrowers_by_country = df.groupby("country")[["num_male", "num_female", "num_gendered_borrowers"]].sum().sort_values("num_gendered_borrowers", ascending=False).head(5)

top_5_categories_male = df[df["pct_male"] == 1].groupby("activity").count()["id"].sort_values(ascending=False).head()

top_5_categories_female = df[df["pct_female"] == 1].groupby("activity").count()["id"].sort_values(ascending=False).head()


pct_female_year = df.groupby(['year', 'country'])['pct_female'].mean()
# df.groupby(['Name', 'Fruit'])['Number'].agg('sum')
# Create a Dash object instance
app = dash.Dash()

app.css.append_css({
    'external_url': 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
})

# The layout attribute of the Dash object, app
# is where you include the elements you want to appear in the
# dashboard. Here, dcc.Graph and dcc.Slider are separate
# graph objects. Most of Graph's features are defined
# inside the function update_figure, but we set the id
# here so we can reference it inside update_figure
app.layout = html.Div(className='container', children=[
    html.Div([  # this starts the row
        html.Div(  # this is the left graph of the row
            [html.H3(children='Top 5 activities for loans to Females',
                    style={
                        'textAlign': 'center',  # center the header
                        'color': '#7F7F7F'
            }),
            dcc.Graph(  # add a bar graph to dashboard
                id='basic-interactions',
                figure={
                    'data': [
                        {
                            'x': top_5_categories_female.index,
                            'y': top_5_categories_female,
                            'type': 'bar',
                            'opacity': .6,  # changes the bar chart's opacity
                            'name': 'Females'
                        }
                    ],
                    'layout': go.Layout(
                        xaxis={'title': 'Activity'},
                        yaxis={'title': 'Count', 'range': [0,61000]},
                    )
                }
            )], className="col-md-6"
        ),
        html.H3(
            children='Top 5 activities for loans to Males',
            style={
                'textAlign': 'center',  # center the header
                'color': '#7F7F7F'
                # https://www.biotechnologyforums.com/thread-7742.html more color code options
            }
        ),
        html.Div(dcc.Graph(  # add a bar graph to dashboard
            id='male_categories',
            figure={
                'data': [
                    {
                        'x': top_5_categories_male.index,
                        'y': top_5_categories_male,
                        'type': 'bar',
                        'opacity': .6,  # changes the bar chart's opacity
                        'name': 'Males'
                    }
                ],
                'layout': go.Layout(
                    xaxis={'title': 'Activity'},
                    yaxis={'title': 'Count', 'range': [0, 61000]},

                )
            }

        ), className="col-md-6")
    ], className="row"),
    # Richard's cloropleth map
    html.Div([
        html.Hr(),
        html.H1(
        children='Cloropleth maps including slider and log-scale colormap',
        style={
            'textAlign': 'center',  # center the header
            'color': '#7F7F7F'
            # https://www.biotechnologyforums.com/thread-7742.html more color code options
        }
    ),
        dcc.Graph(id='graph-with-slider'),
        html.Div([  # div inside div for style
            dcc.Slider(
                id='year-slider',
                min=df['year'].min(),
                max=df['year'].max(),
                value=df['year'].min(),  # The default value of the slider
                step=None,
                # the values have to be the same dtype for filtering to work later
                marks={str(year): year for year in df['year'].unique()},
            )
        ],
            style={'marginLeft': 40, 'marginRight': 40})
    ]),
    html.Div(
        style={'marginLeft': 40, 'marginRight': 40, 'paddingTop': 50, 'paddingBottom': 50}
    ),
    html.Div([
    dcc.Graph(id='scatter-with-slider', animate='true',  style={'marginTop': 30}),
     dcc.Slider(
        id='scatter-slider',
        min=2014,
        max=2017,
        value=2014,
        step=1,
        marks={str(year): str(year) for year in [2014, 2015, 2016, 2017]}
    )
])
])



# Notice the Input and Outputs in this wrapper correspond to
# the ids of the components in app.layout above.
@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('year-slider', 'value')])
def update_figure(selected_year):
    """Define how the graph is to be updated based on the slider."""

    # Depending on the year selected on the slider, filter the db
    # by that year.

    # snag: using .groupby() with more than one feature caused the datatype
    # to be Pandas.Series instead of Pandas.DataFrame. So, we couldn't just do
    # countries_funded_amount[countries_funded_amount['year'] == selected_year]
    one_year_data = pct_female_year.loc[selected_year]

    logzMin = np.log(one_year_data.values.min())
    logzMax = np.log(one_year_data.values.max())
    log_ticks = np.linspace(logzMin, logzMax, 8)
    exp_labels = np.exp(log_ticks).astype(np.int, copy=False)
    data = [dict(
        type='choropleth',
        locations=one_year_data.index.get_level_values('country'),
        # list of country names
        # other option is USA-states
        locationmode='country names',
        # sets the color values. using log scale so that extreme values don't
        # drown out the rest of the data
        z=np.log(one_year_data.values),  # ...and their associated values
        # sets the text element associated w each position
        text=one_year_data.values,
        hoverinfo='location+text',  # hide the log-transformed data values
        # other colorscales are available here:
        # https://plot.ly/ipython-notebooks/color-scales/
        colorscale='Greens',
        # by default, low numbers are dark and high numbers are white
        reversescale=True,
        # set upper bound of color domain (see also zmin)
        # zmin=200,
        # zmax=30000,
        # if you want to use zmin or zmax don't forget to disable zauto
        # zauto=False,
        marker={'line': {'width': 0.5}},  # width of country boundaries
        colorbar={'autotick': True,
                  'tickprefix': '',  # could be useful if plotting $ values
                  'title': 'Percent Loans to Females',  # colorbar title
                  'tickvals': log_ticks,
                  'ticktext': exp_labels
                  # transform log tick labels back to standard scale
                  },
    )]
    layout = dict(
        title='Percent of Loans to Females Per Country. Year: {}<br>Source:\
                <a href="https://www.kaggle.com/kiva/data-science-for-good-kiva-crowdfunding"">\
                Kaggle</a>'.format(selected_year),
        font=dict(family='Courier New, monospace', size=18, color='#7f7f7f'),
        geo={'showframe': False}  # hide frame around map
    )
    cloropleth_map_fig = {'data': data, 'layout': layout}
    return cloropleth_map_fig

# Joe scatter-plot
@app.callback(
    dash.dependencies.Output('scatter-with-slider', 'figure'),
    [dash.dependencies.Input('scatter-slider', 'value')])
def update_scatter(selected_year):
    filtered_df = df[(df['year'] == selected_year) & (df['num_female'] > 0) & (df['num_male'] == 0)]
    traces = []
    for i in filtered_df.sector.unique():
        df_by_sector = filtered_df[filtered_df['sector'] == i]
        traces.append(go.Scatter(
            x=[np.mean(df_by_sector[df_by_sector['country'] == j].loan_amount) for j in df_by_sector.country.unique()],
            y=[np.mean(df_by_sector[df_by_sector['country'] == j].lender_count) for j in df_by_sector.country.unique()],
            text=df_by_sector['country'],
            mode='markers',
            opacity=0.7,
            marker={
                'size': 8,
                'line': {'width': 0.5, 'color': 'blue'}
            },
            name=i
        ))

    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'type': 'linear', 'title': 'Loan Amount', 'autorange': 'True'},
            yaxis={'type': 'linear', 'title': 'Lender Count', 'autorange': 'True'},
            margin={'l': 40, 'b': 40, 't': 25, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            title='Sector Breakdowns for Solely Female Loans by Year'
        )
    }



if __name__ == '__main__':
    app.run_server(debug=True)
