#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Service Request Data analysis
# Author: Lavina DCosta
# Created: February 2026.
# Notice: This document contains proprietary analysis of municipal data.

from datetime import datetime
# Dynamic Watermark for audit trail
print(f"311_Analysis_LD: Data analyzed and generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 79)

import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


# In[2]:


#Cleaning step 1. Started analysis by importing all libraries, to ensure efficient analysis

#Imported all libraries

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from vega_datasets import data
import json
import matplotlib.dates as mdates
import polars as pl
import os
import pandas as pd
import geopandas
import plotly.graph_objects as go
import plotly.express as px  
import json

# Exported CSV from city website, saved it before importing and used for analysis, used polars for speed and memory efficiency.

# Configured Polars to show all columns (default is 10 columns)
pl.Config.set_tbl_cols(15)  # show up to 15 columns
pl.Config.set_tbl_rows(10)  # number of rows to display

Service_Requests_311 = pl.read_csv("/Users/Lavina/Documents/311 data/311_Service_Requests_20260214.csv")


# In[3]:


# Use this for massive datasets
Service_Requests_311.describe()


# In[4]:


# Step 2:  Initialize in lazy frame for memory efficiency, lowercase, datatype assigned, unwanted columns removed,duplicates removed, null values removed,formatting standarized, converted to pandas
lf = Service_Requests_311.lazy().rename(lambda col: col.lower())

DATE_FORMAT = "%Y/%m/%d %I:%M:%S %p"
text_cols = ['service_request_id', 'status_description', 'source', 'service_name', 'agency_responsible', 'comm_name', 'comm_code']
coord_cols = ['longitude', 'latitude']

# Cleaning steps
Service_Requests_311_cleaned = (
    lf
    .select(pl.all().exclude(['address', 'location_type', 'point']))
    .with_columns([
        # Type-safe date parsing
        pl.col(['requested_date', 'updated_date', 'closed_date']).map_batches(
            lambda s: s.str.to_datetime(format=DATE_FORMAT, strict=False) if s.dtype == pl.String else s
        ),
        # String cleaning & Float casting
        pl.col(text_cols).cast(pl.String).str.strip_chars().str.replace_all(r'[^\w\s-]', ''),
        pl.col(coord_cols).cast(pl.Float64)
    ])
    .with_columns([
        pl.col('comm_code').str.to_uppercase(),
        # Calculate response time
        ((pl.col('closed_date').dt.date() - pl.col('requested_date').dt.date()).dt.total_days())
          .cast(pl.Int64).alias('response_time_days'),
        # Create service group
        pl.col('service_name').str.split(' ').list.get(0).cast(pl.String).alias('service_group')
    ])
    .unique(subset=['service_request_id'])
    .filter(
        (~pl.col('status_description').str.to_uppercase().str.contains('TO BE DELETED')) &
        (~pl.col('service_name').str.to_lowercase().str.contains(r'question|inquiry'))
    )
    #Dropnulls without arguments removed any row with at least one null value
    .drop_nulls() 
    .collect()
)
# Formatting & conversion to Pandas 
Service_Requests_311_cleaned.columns = [col.capitalize() for col in Service_Requests_311_cleaned.columns]
Service_Requests_311_ready = Service_Requests_311_cleaned.to_pandas()

# Set Pandas StringDtype
obj_cols = Service_Requests_311_ready.select_dtypes(include=['object']).columns
Service_Requests_311_ready[obj_cols] = Service_Requests_311_ready[obj_cols].astype("string")

# Summary and checks for all parameters
print("Data check summary")

# Step to check for duplicates
dup_count = Service_Requests_311_ready.duplicated(subset=['Service_request_id']).sum()
print(f"Duplicate IDs: {dup_count}")

# Null Check Summary
null_report = Service_Requests_311_ready.isnull().sum()
print("\nNull Counts per Column:")
print(null_report[null_report > 0] if null_report.sum() > 0 else "No nulls found.")

# All columns summary (Numerical and Categorical)
print("\n--- STATISTICAL SUMMARY (All Columns) ---")
display(Service_Requests_311_ready.describe(include='all').T)

# Saved new DataFrame as CSV in Documents folder
documents_path = os.path.join(os.path.expanduser('~'), 'Documents', 'Service_Requests_311_ready.csv')
Service_Requests_311_ready.to_csv(documents_path, index=False)

print(f"Saved CSV to: {documents_path}")

print(f"Final Mappable Rows: {len(Service_Requests_311_ready)}")
print(Service_Requests_311_ready.dtypes)


# In[5]:


# Created a map to illustrate the category in which maximum complaints are received from different neighbourhood illustrating the importance of different columns.

geojson_path = "/Users/Lavina/Documents/311 data/Comm_Bound.geojson"
with open(geojson_path) as f:
    geojson_data = json.load(f)


# Mapping the Top 10 Service Groups 
top_10_groups = (
    Service_Requests_311_ready['Service_group']
    .value_counts()
    .head(10)
    .index.tolist()
)

# Identify Top 10 Communities for the left-side index
top_10_communities_list = (
    Service_Requests_311_ready['Comm_name']
    .value_counts()
    .head(10)
    .index.tolist()
)

top_sg = (
    Service_Requests_311_ready[Service_Requests_311_ready['Service_group'].isin(top_10_groups)]
    .groupby(['Comm_code', 'Comm_name', 'Service_group'], observed=True)
    .agg(
        count=('Service_group', 'count'),
        lon=('Longitude', 'mean'),
        lat=('Latitude', 'mean')
    )
    .reset_index()
    .sort_values('count', ascending=False)
    .groupby('Comm_code')
    .head(1)
    .reset_index(drop=True)
)

sg_map = {name: (9 - i) for i, name in enumerate(top_10_groups)}
top_sg['sg_index'] = top_sg['Service_group'].map(sg_map)

# Figure customization
colors = (px.colors.qualitative.Pastel + px.colors.qualitative.Pastel2)[:10]
reversed_colors = colors[::-1]
custom_sg_scale = [[i/9, reversed_colors[i]] for i in range(10)]

# Created Map
fig = go.Figure()

# 1. Main Choropleth (Colors by Service Group)
fig.add_trace(go.Choropleth(
    geojson=geojson_data,
    locations=top_sg['Comm_code'],
    z=top_sg['sg_index'],
    featureidkey="properties.comm_code",
    colorscale=custom_sg_scale,
    marker_line_width=0.5,
    marker_line_color='white',
    showscale=True,
    colorbar=dict(
        title="<b>Top 10 Service Groups</b><br><i>High Volume at Top</i>",
        tickvals=list(range(10)),
        ticktext=top_10_groups[::-1], 
        x=0.88, 
        len=0.5,
        y=0.5
    )
))

# Community Names Index (Filtered for Top 10 and sorted by COUNT descending)
index_df = (
    top_sg[top_sg['Comm_name'].isin(top_10_communities_list)]
    .sort_values('count', ascending=False)
)

for _, row in index_df.iterrows():
    fig.add_trace(go.Scattergeo(
        lon=[None], lat=[None], 
        mode='markers',
        name=f"<b>{row['Comm_code']}</b>: {row['Comm_name']}",
        legendgroup="Communities",
        marker=dict(size=10, color='rgba(0,0,0,0)'), 
        showlegend=True
    ))

# Community Codes used as text labels as it is compact.
fig.add_trace(go.Scattergeo(
    lon=top_sg['lon'],
    lat=top_sg['lat'],
    text=top_sg['Comm_code'],
    mode='text',
    textfont=dict(size=8, color='#333333', family='Arial Narrow'),
    showlegend=False,
    hoverinfo='skip'
))

# Layout
fig.update_layout(
    title={'text': "<b>Distribution of Top 10 Complaint Groups by Community Code</b>", 'x': 0.5},
    geo=dict(fitbounds="locations", visible=False, bgcolor='white'),


    annotations=[dict(
        text="311 ANALYSIS_LD",
        xref="paper", yref="paper",
        x=0.01, y=0.01,
        showarrow=False,
        font=dict(size=16, color="rgba(150, 150, 150, 0.4)"),
        align="left"
    )],

    legend=dict(
        title="<b>Top 10 Communities<br>(High to Low Volume)</b>",
        x=0.02, 
        y=0.9,
        traceorder="normal",
        font=dict(size=10),
        itemsizing='constant',
        bgcolor="rgba(255,255,255,0.7)"
    ),

    width=2000, 
    height=1000,
    margin={"r":100, "t":100, "l":100, "b":50}
)

fig.show(config={'staticPlot': True})


# In[6]:


# Prepared data for response time distribution of different service request
df_viz = Service_Requests_311_ready[['Service_group', 'Response_time_days']].copy()
group_order = df_viz['Service_group'].value_counts().index.tolist()

# Created the plot
fig = px.box(
    df_viz, 
    x='Service_group', 
    y='Response_time_days',
    color='Service_group',
    category_orders={'Service_group': group_order},
    color_discrete_sequence=px.colors.qualitative.Set2,
    title="<b>Response Time Distribution by Service Group</b>",
    labels={
        "Service_group": "Service Group", 
        "Response_time_days": "Response Time (Days)"
    },
    points=False 
)

# Enhanced Layout with Legend
fig.update_layout(
    xaxis_tickangle=-45,
    plot_bgcolor="#F5F5F5",
    paper_bgcolor="white",
    width=1300, # Increased width to make room for legend
    height=700,

    # WATERMARK ADDED HERE (Bottom-Left Corner)
    annotations=[dict(
        text="311 ANALYSIS_LD",
        xref="paper", yref="paper",
        x=0.01, y=0.01,
        showarrow=False,
        font=dict(size=16, color="rgba(150, 150, 150, 0.4)"),
        align="left"
    )],

    # Configuration of legend
    showlegend=True,
    legend=dict(
        title="<b>Service Category</b>",
        orientation="v",      # Vertical legend
        yanchor="top",
        y=1,                  # Align to top
        xanchor="left",
        x=1.02,               # Position just outside the right of the plot
        bgcolor="rgba(255,255,255,0.5)",
        bordercolor="Gray",
        borderwidth=1
    )
)

fig.show()


# In[7]:


# Rows with questions/inquiry check 
questions_df = Service_Requests_311_ready[
    Service_Requests_311_ready['Service_name'].str.contains('question|inquiry', case=False, na=False)
]

# Display values
print(questions_df['Service_name'].unique())


# In[8]:


# As discussed in the meeting further analysis would be required, maps created are overview of the data collected and initial EDA performed in support of columns that need to be retained.
# This map is not interactive, removed interactive component made it static as opposed to that demonstrated in the meeting, purpose being to observe all data which it illustrates perfectly, hovering requires moving from one part of map to other which is better for presentation, which would be created later.
# All codes are collated after confirmation received in the meeting, as opposed to when a demonstration was provided as when analysis was performed initially before meeting check was performed after each step to ensure correct analysis was performed. 
# The parameters of cleaned DataFrame can be compared with raw data, all parameters output recorded in this script are as per the task.
# Initial cleaning using polars and then DataFrame created in pandas for visualization.
# If any additonal details are required please do not hesitate.


# In[9]:


#Data Source: City of Calgary Open Data Portal (Not Owned by Author)


# In[ ]:




