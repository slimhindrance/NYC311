#!/usr/bin/env python
# coding: utf-8

# ## Web app
# In order to make this available as a free web app on pythonanywhere.com, I used a simple pandas.sample function to meet the 100MB file size threshold.  The randomness in the function should render the resultant data more than adequate to visualize the prevalence of complaints.
# There are still roughly 1MM data points.

# In[1]:


#%reset -f #clears memory (Ive needed this a lot)


# In[2]:


#Import modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#!pip install folium
import folium
#!pip install plotly
import plotly
#!pip install dash
import dash
from dash import dcc
from dash import html
import plotly.express as px
import plotly.graph_objs as go
#!pip install dash_bootstrap_components
import dash_bootstrap_components as dbc


# In[3]:


#Injest data  WILL BE REVISITING TO UPDATE FROM API
filename = "webapp_sample.csv" #change this for yourself
df=pd.read_csv(filename)
complaintTypeDF = pd.read_csv('complaintTypesCopy.csv',names=['id','desc','category']).dropna(axis=0)
complaintCategoryList = list(set(complaintTypeDF['category'].tolist()))
complaintCategoryList.sort()

dropdownOptions=[]
for item in complaintCategoryList:
    dropdownOptions.append({'label':item,'value':item})

agenciesDF = pd.read_csv('agencies.csv').dropna(axis=0).dropna(axis=0)
agenciesDF.AgencyCode = agenciesDF.AgencyCode.str.upper()
agenciesDF['desc'] = agenciesDF.AgencyCode.astype(str).str.cat(agenciesDF.AgencyName,sep=': ')
agenciesDF.sort_values(by=['desc'],inplace=True)
agencyDict = dict(zip(agenciesDF.desc,agenciesDF.AgencyID))

agencyOptions=[]
for item in agencyDict:
    agencyOptions.append({'label':item,'value':item})


# In[4]:


# My generic filtering mechanism
def filterFunc(df,complaintCat,agency,yearVal):

    compmap =pd.read_csv('_complaintmap.csv')
    refer = compmap[['MasterComplaintType']].to_dict(orient='dict')
    refer = refer['MasterComplaintType']
    listOfIDs = []
    if complaintCat!=None:
        for k,v in refer.items():
            if v==complaintCat:
                listOfIDs.append(k)
    if agency!=None:
        agencyID = agencyDict[agency]
    #adf = df[df.incident_zip == 11212]
    #adf = adf[adf.created_year == 1]
    #adf = df[df.created_month == 1]
    #adf = adf[adf.created_day == 12]
    if complaintCat==None:
        adf=df.copy()
    else:

        adf = df[df.complaint_type.isin(listOfIDs)].copy()

    if agency==None:
        pass
    else:
        adf = adf[adf.agency==agencyID].copy()
    adf=adf[(adf.created_year>=yearVal[0]-2000)&(adf.created_year<=yearVal[1]-2000)].copy()
    return adf



# In[35]:


#HEATMAPS and TIME SERIES
def build_ts_heatmap(adf, timeframe='month'):
    global map_hatter
    from folium import plugins
    df_acc = pd.DataFrame()
    from folium.plugins import HeatMap
    map_hatter = folium.Map(location=[40.6628, -73.95421],
                    zoom_start = 10.5)

    df_acc['Latitude'] = adf['latitude'].astype(float).fillna(np.mean(adf.latitude))
    df_acc['Longitude'] = adf['longitude'].astype(float).fillna(np.mean(adf.longitude))
    heat_df = df_acc[['Latitude', 'Longitude']]

    # Weight color by year
    heat_df['Weight'] = adf['created_'+timeframe]#.str[5:7] #[0:4] for years - must edit line 18 also
    heat_df['Weight'] = heat_df['Weight'].astype(float)
    heat_df = heat_df.dropna(axis=0, subset=['Latitude','Longitude'])#, 'Weight'])
    #heat_df.to_csv('test.csv')

    # Make list of lists
    heat_data = [[[row['Latitude'],row['Longitude']] for index, row in heat_df[heat_df['Weight'] == i].iterrows()] for i in range(1,13)]#range is range of datetime data moving

    # Plotting
    hm = plugins.HeatMapWithTime(heat_data,auto_play=True,max_opacity=0.8)
    hm.add_to(map_hatter)
    # Display the map
    map_hatter.save('currentmap.html')
    #display(map_hatter)
    return map_hatter


# In[37]:


# CHOOSE timeframe = 'year', 'month', or 'day'

build_ts_heatmap(df[df.incident_zip == 11], timeframe='month')


# In[ ]:

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

minVal = int("20"+str(df.created_year.min()))
maxVal = int("20"+str(df.created_year.max()))
markDict = {}
yearNum=minVal
while yearNum<=maxVal:
    markDict[yearNum]=yearNum
    yearNum+=1
timeframe='month'
app.layout= html.Div(children=[                      dcc.Dropdown(id='complaint',options=dropdownOptions,placeholder='Select complaint category'),                      dcc.Dropdown(id='agency',options=agencyOptions,placeholder='Select agency'),                      dcc.RangeSlider(id='year--slider',
                                 min=int("20"+str(df.created_year.min())),
                                 max=int("20"+str(df.created_year.max())),
                                      marks=markDict,
                                      step=None,
                                 value=[int("20"+str(df.created_year.min())),int("20"+str(df.created_year.max()))]),
                      html.Button('Submit', id='button'),\
                        html.H1('NYC 311 Complaint Data'),\
                               dcc.Loading(
                                        children=[html.Div([html.Iframe(id= 'map', srcDoc = open('currentmap.html','r').read(), width='100%', height='600'),])],
                                        type="circle",),\
                               html.H6('team 187 (SlackOverflow): CSE_6242_DVA, Georgia Tech, Fall 2021', style={'float':'right'}),
                               html.H2('How to'),\
                               html.P('The complaint type dropdown allows us to see all complaints of a particular type.'),\
                               html.P('The agency dropdown allows us to further filter the complaints through a particular agency.'),\
                               html.P('The range-slider permits selection of a single year or an aggregate of years to map.'),\
                               html.P('The timecontroller at the bottom cycles through months, allowing us to visualize the movement of complaint data.'),\
                            html.H1('Photo Gallery'),\
                        #html.H4('1'),\
                        html.Img(src=app.get_asset_url('01-AvgDaysToCloseByBorough.PNG'),style={'width':'40%','height':'40%', 'float':'left'}),\
                        #html.H4('2'),\
                        html.Img(src=app.get_asset_url('02-Top10ComplaintsByAgency.PNG'),style={'width':'40%','height':'40%', 'float':'right'}),\
                        #html.H4('3'),\
                        html.Img(src=app.get_asset_url('03-Top10ComplaintsByType.PNG'),style={'width':'40%','height':'40%', 'float':'left'}),\
                        #html.H4('4'),\
                        #html.Img(src=app.get_asset_url('04-Top10ComplaintsByLocationType.PNG'),style={'width':'40%','height':'40%', 'float':'right'}),\
                        html.Img(src=app.get_asset_url('12-311CallsResponseTimeFromNYCAndLA.PNG'),style={'width':'40%','height':'40%', 'float':'right'}),\
                        #html.H4('5'),\
                        html.Img(src=app.get_asset_url('05-AvgResponseTimeNyBorough.PNG'),style={'width':'40%','height':'40%', 'float':'left'}),\
                        #html.H4('6'),\
                        html.Img(src=app.get_asset_url('06-ComplaintsCountVsDaysToCloseByBorough.PNG'),style={'width':'40%','height':'40%', 'float':'right'}),\
                        #html.H4('7'),\
                        html.Img(src=app.get_asset_url('07-ComplaintResponseTimeHeatmapByYear.PNG'),style={'width':'40%','height':'40%', 'float':'left'}),\

                        html.Img(src=app.get_asset_url('08-ComplaintTypesByBorough.PNG'),style={'width':'40%','height':'40%', 'float':'right'}),\
                        #html.H4('7'),\
                        html.Img(src=app.get_asset_url('09-SubComplainTypeByYears.PNG'),style={'width':'40%','height':'40%', 'float':'left'}),\
                        html.Img(src=app.get_asset_url('10-SubComplainTypeByNeighborhood.PNG'),style={'width':'40%','height':'40%', 'float':'right'}),\
                        #html.H4('7'),\
                        html.Img(src=app.get_asset_url('11-HighestResidentialNoiseVsResponseTime.PNG'),style={'width':'40%','height':'40%', 'float':'left'}),\
                        #
                        #html.H4('7'),\
                        #html.Img(src=app.get_asset_url('13-RegressionAnalysisNYCAndLA.PNG'),style={'width':'40%','height':'40%'}),\
                     ])

@app.callback(
    dash.dependencies.Output('map', 'srcDoc'),
    dash.dependencies.Input('button', 'n_clicks'),
    dash.dependencies.Input('complaint', 'value'),
    dash.dependencies.Input('agency', 'value'),
    dash.dependencies.Input('year--slider', 'value'))

def update_map(n_clicks,complaintType,agencyType,yearSelection):

    if n_clicks==None:

        return dash.no_update
    else:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

        if 'button' in changed_id:
            newDF = filterFunc(df,complaintType,agencyType,yearSelection)
            newDF.to_csv('test.csv')
            build_ts_heatmap(newDF, timeframe=timeframe)
            n_clicks=None
            return open('currentmap.html', 'r').read()
        else:
            return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=False)


# In[ ]:





# In[ ]:




