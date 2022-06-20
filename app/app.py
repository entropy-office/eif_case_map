##############################
##     IMPORT LIBRARIES     ##
##############################

import os
import pathlib
import re

import dash
from dash import Dash, dcc, html, Input, Output, State
# import dash_bootstrap_components as dbc
# import plotly.express as px
import plotly.graph_objects as go
# import dash_daq as daq

# ADDED LIBRARIES
from textwrap import dedent

import pandas as pd
import numpy as np
import json

# Disable copy warnings
pd.options.mode.chained_assignment = None

##############################
##     INITIALIAZE APP      ##
##############################

# app = Dash(__name__)

app = dash.Dash(
    __name__,
    # external_stylesheets=[dbc.themes.MINTY],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

server = app.server
# app.config.suppress_callback_exceptions = True
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True

##############################
##        LOAD DATA         ##
##############################

# LOAD GeoJSON of NUTS-3 Shapes
# with open('data/geojson/Super_Gen/NUTS_Level_3_(January_2018)_Boundaries.geojson') as json_file:
#     nuts3json = json.load(json_file)

# LOAD NUT3-3 Dataframe
df = pd.read_csv('data/nuts3.csv', encoding='utf-8-sig')

# converters={'employee_id': str.strip}

# CS = CASESTUDIES
# cs = pd.read_csv('data/eif-case-studies-new.csv', encoding='utf-8-sig')
cs = pd.read_csv('data/final/eif-casesmap-working_dev-test.csv', encoding='utf-8-sig')


cols = cs.select_dtypes(object).columns
cs[cols] = cs[cols].apply(lambda x: x.str.strip())

# MAPBOX ACCESS TOKEN
mapbox_access_token = "pk.eyJ1IjoicGF0aGFydmV5IiwiYSI6ImNreTRzb2ZmeTBleWgydW1sYjV1enZldWIifQ.emUuH8XVCjL-9aGkVEg6OA"
mapbox_style = "mapbox://styles/patharvey/cl0wndql8001r14o1bl7llqtp"

##############################
##       FIX LONG/LAT       ##
##############################

# Rename lat and lon
loc_df = cs.rename({'lat_approx': 'lat', 'long_approx': 'lon'}, axis='columns')

# assign unique key based on dup locations
loc_df['loc_id'] = loc_df.groupby(['lat', 'lon']).ngroup()
loc_df['loc_dup_num'] = loc_df.groupby('loc_id').cumcount()

# dup or not a dup
loc_df_dups = loc_df[loc_df['loc_dup_num'] > 0]
loc_df_no_dups = loc_df[loc_df['loc_dup_num'] == 0]

# Set Jitter Value
sigma = 0.025
# Assign to lon and lat
loc_df_dups = loc_df_dups.assign(lat=np.random.normal(loc_df_dups['lat'], sigma))
loc_df_dups = loc_df_dups.assign(lon=np.random.normal(loc_df_dups['lon'], sigma))

# reset to cs
cs = pd.concat([loc_df_dups, loc_df_no_dups]).reset_index(drop=True)

cs = cs.rename({'lat': 'lat_approx', 'lon': 'long_approx'}, axis='columns')

##############################
##        CLEAN DATA        ##
##############################

dict_color_point = {
    "E": "#007D8A",  # GREEN
    "F": "#E0004D",  # PINK
    "S": "#DBC600",  # GOLD/GREEN
    "X": "#009EE3"  # BLUE
}

# Add point_color
cs['point_color'] = cs['issue']
cs['point_color'] = cs['point_color'].replace(dict_color_point, regex=True)

# assign random number based on number of rows
df['color'] = np.random.randint(1, 500, df.shape[0])

# CLEAN TEXT FOR HOVER LABEL
issue_dict = {"E": "Early Childhood Services", "F": "Family Relations & Parental Conflict", "S": "Speech & Language Support"}
action_dict = {"1": "Strategy",  # possible to add <br> directly into string
               "2": "Workforce",
               "3": "Partnership",
               "4": "Community",
               "5": "Services & Interventions",
               "6": "Coordinated Working",
               "7": "Outcomes & Experience",
               "8": "Evaluation",
               "9": "None"}

# copy columns in cs
cs['hover_issue'] = cs['issue']
cs['hover_action'] = cs['action'].astype(str)
# string replace, use dicts
cs['hover_issue'] = cs['hover_issue'].replace(issue_dict, regex=True)
cs['hover_action'] = cs['hover_action'].replace(action_dict, regex=True)

# Add breaks to summary
cs['hover_summary'] = cs['summary'].str.wrap(50)
cs['hover_summary'] = cs['hover_summary'].apply(lambda x: x.replace('\n', '<br>'))


# SPLIT DF: AREA STUDIED VS. AREA NOT STUDIED
# UNIQUE areas in CASESTUDY as LIST
area_studied = set(cs['nuts318cd'].unique())
# AREA STUDIED
dss = df[df['nuts318cd'].isin(area_studied)]
# AREA NOT STUDIED
dnn = df[~df['nuts318cd'].isin(area_studied)]

# Left Merge dss on cs...two instances of same code UKC11, dataframe "ds" should be 1 row longer than prev "dss"
ds = cs.merge(dss, on='nuts318cd', how='left')
# convert action column into list
# ds['action'] = ds['action'].str.split(',')
# Left Merge cs on dnn...maintain length of dnn
dn = dnn.merge(cs, on='nuts318cd', how='left')

# drop duplicates in ds and concat on dn
dsx = ds.drop_duplicates(subset=['nuts318cd'], keep='first')
# assign darker values to areas studied
dsx['color'] = np.random.randint(750, 1000, dsx.shape[0])
# stack dataframes ontop of one another
df = pd.concat([dsx, dn]).reset_index(drop=True)
# test
# print(df, ds)

##############################
##          STYLE           ##
##############################

DEFAULT_OPACITY = 0.8

DEFAULT_COLORSCALE = [  # PURPLE SCALE / Different in Doc
    "#E3DDE5",
    "#CBC0D2",
    "#B7A6C2",
    "#A58FB3",
    "#957AA6",
    "#85679A",  # Current Unselected
    "#78568E",
    "#6C4684",
    "#5F3478",
    "#52256F",
]

EIF_PURPLE = "#653279"
EIF_GREEN = "#007D8A"
EIF_PINK = "#E0004D"
EIF_GOLD = "#DBC600"
EIF_BLUE = "#009EE3"
EIF_WHITE = "#FFFFFF"
EIF_GREY = "#373A36"

# CSS STYLE PROPERTIES
# font                all font properties in one line
# @font-face          declare non-web-safe fonts
# font-family         font of the element
# font-size           font size
# font-size-adjust    control font size if the first declared option is not available
# font-stretch        widen or narrow text
# font-style          font style: normal, italic, oblique
# font-variant        set small-caps
# font-weight         use bold or thin characters #  thin (100), normal (400), bold (700), and heavy (900)

# h1 { font-size: 4.5rem; line-height: 1.2;  letter-spacing: -.1rem; margin-bottom: 2rem; }
# h2 { font-size: 3.6rem; line-height: 1.25; letter-spacing: -.1rem; margin-bottom: 1.8rem; margin-top: 1.8rem;}
# h3 { font-size: 3.0rem; line-height: 1.3;  letter-spacing: -.1rem; margin-bottom: 1.5rem; margin-top: 1.5rem;}
# h4 { font-size: 2.6rem; line-height: 1.35; letter-spacing: -.08rem; margin-bottom: 1.2rem; margin-top: 1.2rem;}
# h5 { font-size: 2.2rem; line-height: 1.5;  letter-spacing: -.05rem; margin-bottom: 0.6rem; margin-top: 0.6rem;}
# h6 { font-size: 2.0rem; line-height: 1.6;  letter-spacing: 0; margin-bottom: 0.75rem; margin-top: 0.75rem;}

# TITLE
titlestyle = {'color': EIF_PURPLE, 'font-weight': 'bold', 'font-style': 'normal', 'margin-top': '0.6rem', 'margin-bottom': '0px'}
# SUB-TITLE
substyle = {'color': "#85679A", 'font-weight': 'bold', 'font-style': 'italic', 'font-size': '120%', 'margin-bottom': '0.6rem'}
# DESCRIPTION
descripstyle = {'color': EIF_GREY, 'font-weight': 'normal', 'font-style': 'normal', 'font-size': '100%'}
# {'color': EIF_GREY, 'font-weight': 'normal', 'font-style': 'normal', 'font-size': '100%',
# LEGEND TEXT
legendstyle = {'font-weight': 'normal', 'font-size': '100%', 'color': EIF_GREY,
               'list-style': 'none', 'text-indent': '20px', 'white-space': 'nowrap',
               'margin-left': '2%'}
# SUB-HEADING
blackbold = {'color': EIF_PURPLE, 'font-weight': 'bold', 'verticalAlign': 'top', 'font-size': '120%'}

# LISTS
liststyle = {'color': EIF_GREY, 'font-weight': 'normal', 'font-size': '100%'}
# DEfAULT TEXT
defaultstyle = {'color': EIF_GREY, 'font-weight': 'normal'}
# LINK STYLE
# linkstyle = {'color': EIF_GREEN, 'white-space': 'pre-wrap', 'word-break': 'break-all'}

##############################
##       MODAL BUTTON       ##
##############################


def build_modal_info_overlay(id, side, content):
    """
    Build div representing the info overlay for a plot panel
    """
    div = html.Div(
        [  # modal div
            html.Div(
                [  # content div
                    html.Div(
                        [
                            html.H4(
                                [
                                    "Info",
                                    html.Img(
                                        id=f"close-{id}-modal",
                                        src="assets/times-circle-solid.svg",
                                        n_clicks=0,
                                        className="info-icon",
                                        style={"margin": 0},
                                    ),
                                ],
                                className="container_title",
                                style={"color": "white"},
                            ),
                            dcc.Markdown(content),
                        ]
                    )
                ],
                className=f"modal-content {side}",
            ),
            html.Div(className="modal"),
        ],
        id=f"{id}-modal",
        style={"display": "none"},
    )

    return div


##############################
##        APP LAYOUT        ##
##############################

# App Mirrored Layout
app.layout = html.Div(
    [  # APP / not closed
        html.Div([  # ROOT / not closed
            html.Div(
                [  # LEFT COLUMN / closed
                    html.Div(
                        [  # TITLE
                            html.Div(
                                [
                                    html.H3("Transforming Early Intervention for Families", style=titlestyle),
                                    html.H5("Case Studies from Local Areas", style=substyle),
                                ], style={'text-align': 'left'},
                            ),
                        ],
                        className="title_pretty_container",
                        id='title',
                    ),  # Title: CLOSED
                    html.Div(
                        [  # INFO CONTAINER
                            html.Div(
                                [  # A-COLUMN
                                    html.Label(children=['About This Map: '], style={'color': EIF_PURPLE, 'font-weight': 'bold', 'margin-bottom': '2%', 'font-size': '120%'}),
                                    html.P("This map provides quick and easy access to examples of innovation and good practice by local authorities and partners across England and Wales. The case studies include the practical application of tools and research \
                                        developed by EIF and are intended to support local areas to use these in their own work.", style=descripstyle),
                                    html.Br(),
                                    html.P("To focus on a specific theme or local activity simply select your area of interest to filter the results displayed. You can then click the \
                                        points on the map for a summary and a link to the full case study.", style=descripstyle),
                                    html.Br(),
                                    # html.Label(children=['Legend '], style={'color': EIF_PURPLE, 'font-weight': 'bold', 'margin-bottom': '2%'}),
                                    # html.Div([
                                    #     html.Ul(
                                    #         children=[
                                    #             html.Li("Early Childhood Services", className='circle', style={'background': EIF_GREEN}),
                                    #             html.Li("Family Relations & Parental Conflict", className='circle', style={'background': EIF_PINK, }),
                                    #             html.Li("Speech & Language Support", className='circle', style={'background': EIF_GOLD}),
                                    #         ], style=legendstyle),
                                    # ]),
                                    html.Label(children=['Themes '], style=blackbold),
                                    html.Button(className='button btn btn-primary btn-xs', id='all-or-none', n_clicks=1, children="Select / Unselect All", style={'margin-left': '1%', 'margin-top': '1%', 'margin-bottom': '2%'}),
                                    dcc.Checklist(id='issue_list',
                                                  options=[{"label": "Early Childhood Services", "value": "E"}, {"label": "Family Relations & Parental Conflict", "value": "F"}, {"label": "Speech & Language Support", "value": "S"}],
                                                  value=["E", "F", "S"],  # labelStyle={'color': "#B7A6C2"},  # change color of text https://community.plotly.com/t/change-color-of-checklists-checkboxes/60601/4
                                                  style={'margin-bottom': '6%', 'color': EIF_GREY, 'font-weight': 'normal', 'font-size': '100%'}),
                                    html.Label("Local Activity ", style=blackbold),

                                    html.Button(className='button btn btn-primary btn-sm', id='all-or-none1', n_clicks=1, children="Select / Unselect All", style={'margin-left': '1%', 'margin-top': '1%', 'margin-bottom': '2%'}),
                                    dcc.Checklist(
                                        id='action_list',  # formerly recycling_type
                                        options=[
                                            {"label": "Strategy Development", "value": "1"}, {"label": "Workforce Development", "value": "2"}, {"label": "Partnership Working", "value": "3"}, {"label": "Co-Production", "value": "4"},
                                            {"label": "Services & Interventions", "value": "5"}, {"label": "Coordinated Working", "value": "6"}, {"label": "Experience & Outcome", "value": "7"}, {"label": "Evaluation", "value": "8"}
                                        ],
                                        value=["1", "2", "3", "4", "5", "6", "7", "8", "9"], style=liststyle, className="checkbox-round",
                                    ),
                                    # html.Div([
                                    #     html.Button(id='modal', className='button btn btn-primary btn-xs', n_clicks=0, children="?"),
                                    # ], style={'margin-left': '1%', 'margin-top': '10%', 'verticalAlign': 'bottom'}),
                                ],  # style={'width': '39%', 'display': 'inline-block', 'verticalAlign': 'top'},  # style={'align-items': 'top'}
                                className="pretty_container",
                                id="a-column",
                            ),  # A-COLUMN: Closed

                            html.Div(
                                [  # B-COLUMN
                                    html.Label(['Project Information: '], style={'color': EIF_PURPLE, 'font-weight': 'bold', 'verticalAlign': 'top', 'font-size': '120%'}),
                                    html.P(id='web_link', children=[],
                                           style={'border': '1.5px solid black', 'text-align': 'left',
                                                  'border-radius': '5px',
                                                  'padding': '12px 12px 12px 12px', 'border-color': EIF_PURPLE,
                                                  'margin-top': '6px'}),
                                    html.Br(),
                                    html.Label(children=['Map Legend: '], style={'color': EIF_PURPLE, 'font-weight': 'bold', 'margin-bottom': '2%', 'font-size': '120%'}),
                                    html.Div([
                                        html.Ul(
                                            children=[
                                                html.Li("Early Childhood Services", className='circle', style={'background': EIF_GREEN, 'font-size': '100%', 'margin-bottom': '3%'}),
                                                html.Li("Family Relations & Parental Conflict", className='circle', style={'background': EIF_PINK, 'font-size': '100%', 'margin-bottom': '3%'}),
                                                html.Li("Speech & Language Support", className='circle', style={'background': EIF_GOLD, 'font-size': '100%', 'margin-bottom': '1%'}),
                                            ], style=legendstyle),
                                    ]),
                                ],  # style={'margin-left': '5%', 'verticalAlign': 'top', 'width': '100%'},
                                className="pretty_container",
                                id="b-column",
                            ),  # B-COLUMN: Closed
                        ],
                        className="row container-display",
                        id="info-containter",
                    ),  # Info Container is closed
                ],
                className="six columns",
                id="left-column",
            ),  # Left Column is closed
            ######################################################
            html.Div(
                children=[
                    html.Div(
                        [
                            # html.Div([
                                dcc.Graph(
                                    id='graph',
                                    config={'displayModeBar': True, 'scrollZoom': True},
                                    style={'height': '100vh', 'width': '85vh', 'padding-top': '1vh', 'display': 'inline-block'}  # 'padding-bottom': '6px',
                                    # style={'display': 'inline-block'}
                                ),
                            # ], className='map-container', id='map'),
                        ],
                        className='graph-container',
                        id='graph-figure'
                    ),
                ],
                className="four columns",
                id='right-column'
            ),
            # Close root
        ], className='row'),
        # Close App

    ], className='twelve columns'  # className='ten columns offset-by-one'
)


##############################
##        CALLBACKS         ##
##############################

# LINK: HOW TO ADD CHOROPLETH LAYER
# https://community.plotly.com/t/how-can-i-combine-choropleth-and-scatter-layer-in-a-plotly-map/29842
# https://stackoverflow.com/questions/67680264/combining-mapbox-choropleth-with-additional-layers-and-markers-in-python-try-to
# https://chart-studio.plotly.com/~RPlotBot/1735.py


# BELOW CREATE MODALS (TOOLTIPS THAT CAN BE OPEN AND CLOSED) - NEEDS TO BE DEVELOPED

# for id in ["theme", "activity"]:

#     @ app.callback(
#         [Output(f"{id}-modal", "style")],
#         [Input(f"show-{id}-modal", "n_clicks"), Input(f"close-{id}-modal", "n_clicks")],
#     )
#     def toggle_modal(n_show, n_close):
#         ctx = dash.callback_context
#         if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("show-"):
#             return {"display": "block"}, {"zIndex": 1003}
#         else:
#             return {"display": "none"}, {"zIndex": 0}


@ app.callback(Output('graph', 'figure'),
               [Input('issue_list', 'value'),
                Input('action_list', 'value')])
def update_figure(issue_list, action_list):
    df_sub = ds[(ds['issue'].isin(issue_list)) &
                (ds['action'].str.contains('|'.join(map(re.escape, action_list)), na=False))
                ]

    # Create Figure
    locations = [go.Scattermapbox(
        lon=df_sub['long_approx'],
        lat=df_sub['lat_approx'],
        mode='markers',
        marker={'color': df_sub['point_color'], 'opacity':0.75, 'size': 10},
        unselected={'marker': {'opacity': 0.75, 'size': 10}},
        selected={'marker': {'opacity': 0.4, 'size': 25}},
        hoverinfo='text',
        hovertext=df_sub['case_title'],
        hovertemplate="<br>".join([  # Case Title
            "<b>%{customdata[1]}</b>",
            "<i>Click to View Description</i><br><br>"
            "<b>Area:</b> %{customdata[2]}",
            "<b>Themes:</b> %{customdata[3]}",
            "<b>Local Activity:</b> %{customdata[4]}",
            # "<br>%{customdata[5]}", # Remove Description
            "<extra></extra>"]),
        hoverlabel_align='left',
        hoverlabel_bordercolor='white',
        # customdata=df_sub['link']
        customdata=df_sub[['link', 'case_title', 'area', 'hover_issue', 'hover_action', 'hover_summary', 'summary', \
                           'year', 'rel_tool_name', 'rel_tool_link', 'contact_name', 'contact_title', 'contactors', 'contact_email']]
    )]

# Return Figure
    return {
        'data': locations,
        'layout': go.Layout(
            uirevision='foo',  # preserves state of figure/map after callback activated
            clickmode='event+select',
            hovermode='closest',
            hoverdistance=2,
            margin=dict(t=0, b=0, l=0, r=0),  # adjusts border of graph
            # title=dict(text="<b>Early Intervention Foundation:</b> Selection of Case Studies", font=dict(size=16, color='#653279')),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,  # rotation z-axis
                # style='light',
                style=mapbox_style,
                center=dict(
                    lat=52.9,
                    lon=-2,
                ),
                pitch=0,  # rotation x-axis
                zoom=6.2
            ),
        )
    }


# ISSUE LIST: SELECT ALL - DELETE REDUNDANT
@ app.callback(Output('issue_list', 'value'),
               [Input('all-or-none', 'n_clicks')],
               [State('issue_list', 'options')])
def select_all_none(all_selected, options):
    if all_selected % 2 == 0:
        all_or_none1 = []
        return all_or_none1
    else:
        all_or_none1 = [option['value'] for option in options if all_selected]
        return all_or_none1

# ACTION LIST: SELECT ALL


@ app.callback(Output('action_list', 'value'),
               [Input('all-or-none1', 'n_clicks')],
               [State('action_list', 'options')])
def select_all_none(all_selected, options):
    if all_selected % 2 == 0:
        all_or_none1 = ["9"]
        return all_or_none1
    else:
        all_or_none1 = [option['value'] for option in options if all_selected]
        return all_or_none1

# LINK STYLE
# https://stackoverflow.com/questions/10629928/why-does-line-height-property-not-work-with-hyperlinks


# PINFO STYLE MAIN
ptitlestyle = {'color': EIF_GREY, 'margin-bottom': '1%', 'font-weight': 'bold', 'verticalAlign': 'bottom', 'font-size': '100%', 'line-height': '20px', 'verticalAlign': 'top'}
# SUBTITLE STYLE
psubtitlestyle = {'color': EIF_GREY, 'font-weight': 'normal', 'font-style': 'italic', 'white-space': 'break-spaces', 'line-height': '20px', 'verticalAlign': 'top', 'font-size': '100%', 'float': 'left'}
# SUBTITLE STYLE
psubtitlestyle_end = {'color': EIF_GREY, 'font-weight': 'normal', 'font-style': 'italic', 'white-space': 'break-spaces', 'line-height': '20px', 'verticalAlign': 'top', 'font-size': '100%'}
# DESCRIPTION
pdescripcatstyle = {'color': EIF_GREY, 'margin-bottom': '1%', 'font-weight': 'bold', 'font-style': 'bold', 'font-size': '100%', 'line-height': '20px', 'float': 'left', 'white-space': 'break-spaces', 'verticalAlign': 'bottom'}
# DESCRIPTION
pdescripstyle = {'color': EIF_GREY, 'font-weight': 'normal', 'font-style': 'normal', 'font-size': '100%', 'white-space': 'break-spaces', 'line-height': '20px', 'float': 'left', 'verticalAlign': 'bottom'}
# BREAK
breakstyle = {'color': EIF_GREY, 'font-weight': 'bold', 'font-style': 'bold', 'font-size': '100%', 'white-space': 'break-spaces', 'line-height': '20px', 'float': 'none', 'verticalAlign': 'bottom'}
# LINK
linkstyle = {'color': EIF_GREEN, 'margin-top': '2%', 'white-space': 'pre-wrap', 'word-break': 'break-all', 'font-size': '100%', 'line-height': '20px', 'verticalAlign': 'bottom', 'text-decoration': 'none'}

# OMIT
# linkstylefloat = {'color': EIF_GREEN, 'white-space': 'pre-wrap', 'word-break': 'break-all', 'font-size': '100%', 'line-height': '0px', 'float': 'left', 'verticalAlign': 'top'}
# endlinestyle = {'color': EIF_GREY, 'white-space': 'pre-wrap', 'word-break': 'break-all', 'font-size': '100%', 'line-height': '0px', 'float': 'none', 'verticalAlign': 'bottom'}
# endlinkstyle = {'color': EIF_GREEN, 'white-space': 'pre-wrap', 'word-break': 'break-all', 'font-size': '100%', 'line-height': '0px', 'float': 'left', 'verticalAlign': 'bottom'}
# breakstyle = {'color': EIF_GREY, 'font-weight': 'bold', 'font-style': 'bold', 'font-size': '100%', 'line-height': '0px', 'float': 'none', 'white-space': 'pre-wrap', 'verticalAlign': 'top'}


@ app.callback(
    Output('web_link', 'children'),
    [Input('graph', 'clickData')])
def display_click_data(clickData):
    if clickData is None:
        # return 'Click on any point'
        return html.Label(children=["Select a location on the map to display more information about the case study here."],
                          style={'color': EIF_PURPLE, 'font-weight': 'normal', 'text-align': 'left'})
    else:
        # print (clickData)
        # the_link = clickData['points'][0]['customdata[0]']
        the_link = clickData['points'][0]['customdata']
        if the_link is None:
            # return 'No project information available'
            return html.Label(children=['No project information available'], style={'color': EIF_PURPLE, 'font-weight': 'normal', 'text-align': 'center'})
        else:  # html.A Denotes hyperlink
            return html.Div(
                children=[
                    html.Label(the_link[1], style=ptitlestyle),  # CASE TITLE
                    html.P(the_link[2], style=psubtitlestyle),  # AREA
                    html.P(", ", style=psubtitlestyle),  # AREA + ", " + YEAR #psubtitlestyle
                    html.P(the_link[7], style=psubtitlestyle_end),  # YEAR
                    # html.P(" ", style=breakstyle),  # AREA
                    html.Br(),
                    html.P("Description: ", style=pdescripcatstyle),
                    html.P(the_link[6], style=pdescripstyle),
                    # html.P(" ", style=pdescripcatstyle),
                    # html.P(" ", style=pdescripstyle),
                    # html.Br(style=pdescripcatstyle),
                    # html.Br(),
                    # html.Br(),
                    html.A("[Click For More Information]", href=the_link[0], target='_blank', style=linkstyle),
                    # html.P("Related Tool: ", style=pdescripcatstyle),  # AREA
                    # html.A(the_link[8], href=the_link[9], target='_self', style=linkstyle),
                    # html.P(" ", style=breakstyle),
                    # html.P(" ", style=breakstyle),
                    # html.P("Contact Name: ", style=pdescripcatstyle),  # AREA
                    # html.A(the_link[10], href=the_link[13], target='_blank', style=linkstyle),
                    # html.P(" ", style=breakstyle),
                    # html.P(" ", style=breakstyle),
                    # html.P("Contactor: ", style=pdescripcatstyle),  # AREA
                    # html.P(the_link[12], style=endlinestyle),
                    # html.P(" ", style=breakstyle),
                    # html.P(" ", style=breakstyle),
                ])
            # )  # adding '[0]' to the_link specifies which custom data to pass

# 0=link, 1=case_title, 2=area, 3=hover_issue, 4=hover_action, 5=hover_summary, 6=summary
# 7=year, 8=rel_tool_name, 9=rel_tool_link, 10=contact_name, 11=contact_title, 12=contactors, 13=contact_email

# Does not work as expected - should clear clickdata
# https://community.plotly.com/t/reset-click-data-when-clicking-on-map/22709
# @app.callback(Output("map", "clickData"),
#               [Input("map-container", "n_clicks")],
#               )
# def reset_clickData(n_clicks):
#     return None


if __name__ == '__main__':
    app.run_server()
