#!/usr/bin/env python3
"""
Earthquake Data Visualization Dashboard
Real-time map visualization of earthquake data from PostgreSQL
"""

import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pytz
import os

# Page configuration
st.set_page_config(
    page_title="Earthquake Data Dashboard",
    page_icon="🌎",
    layout="wide",
)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "earthquakedb")
DB_USER = os.environ.get("DB_USER", "earthquake")
DB_PASS = os.environ.get("DB_PASSWORD", "quakedata")

# Function to connect to PostgreSQL
@st.cache_resource
def get_db_connection():
    """Create a connection to PostgreSQL"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

# Function to fetch recent earthquakes
def get_recent_earthquakes(conn, hours=24, min_magnitude=0):
    """Fetch recent earthquakes from the database"""
    query = """
    SELECT 
        unid, time, region, latitude, longitude, depth, magnitude, action
    FROM 
        earthquakes
    WHERE 
        time >= NOW() AT TIME ZONE 'UTC' - INTERVAL '%s hours'
        AND magnitude >= %s
        AND action != 'delete'
    ORDER BY 
        time DESC
    """
    
    df = pd.read_sql_query(
        query, 
        conn, 
        params=(str(hours), min_magnitude)
    )
        
    return df

# Function to create an earthquake map
def create_earthquake_map(df):
    """Create a map visualization of earthquakes"""
    if df.empty:
        return go.Figure()
    
    # Create color scale based on magnitude
    df['marker_size'] = df['magnitude'] ** 2 * 5  # Scale for visibility
    
    # Convert time to Pacific timezone for display
    pacific = pytz.timezone('US/Pacific')
    if 'time' in df.columns:
        # Make a copy of time for the Pacific timezone display
        df['time_pacific'] = pd.to_datetime(df['time'], utc=True)
        df['time_pacific'] = df['time_pacific'].dt.tz_convert(pacific)
        df['time_pacific'] = df['time_pacific'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    # Create map
    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="region",
        hover_data={
            "magnitude": True,
            "depth": True,
            "time": True,
            "time_pacific": True,
            "latitude": False,
            "longitude": False,
            "marker_size": False,
        },
        color="magnitude",
        size="marker_size",
        color_continuous_scale="Viridis",
        zoom=1,
        height=600,
        labels={
            "magnitude": "Magnitude",
            "depth": "Depth (km)",
            "time": "Time (UTC)",
            "time_pacific": "Time (Pacific)"
        },
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title="Magnitude",
            thicknessmode="pixels", 
            thickness=20,
            lenmode="pixels", 
            len=300,
            yanchor="top", 
            y=1,
            xanchor="left",
            x=0.01,
        ),
    )
    
    return fig

# Header and Description
st.title("🌎 Real-time Earthquake Monitoring Dashboard")
st.markdown("""
This dashboard provides real-time visualization of earthquake data from around the world.
Data is updated automatically to show the most recent earthquakes.
""")

# Filter Sidebar
st.sidebar.header("Dashboard Controls")

# Time range selector
time_options = {
    "Last 6 hours": 6,
    "Last 12 hours": 12,
    "Last 24 hours": 24,
    "Last 3 days": 72,
    "Last week": 168,
}
selected_time = st.sidebar.selectbox(
    "Time range:",
    options=list(time_options.keys()),
    index=2  # Default to 24 hours
)

# Magnitude filter
min_magnitude = st.sidebar.slider(
    "Minimum magnitude:",
    min_value=0.0,
    max_value=9.0,
    value=0.0,
    step=0.5
)

if 'last_updated' not in st.session_state:
    st.session_state.last_updated = datetime.now()

# Get data and create visualizations
conn = get_db_connection()
hours = time_options[selected_time]

# Display last update time
st.sidebar.markdown(f"**Last updated:** {st.session_state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

# Fetch data
earthquake_data = get_recent_earthquakes(conn, hours, min_magnitude)

# Display data count
data_count = len(earthquake_data)
st.write(f"### Displaying {data_count} earthquakes with magnitude ≥ {min_magnitude} in the {selected_time.lower()}")

# Create tabs for different views
tab1, tab2 = st.tabs(["Map View", "Data Table"])

with tab1:
    with st.container():
        if data_count > 0:
            map_fig = create_earthquake_map(earthquake_data)
            st.plotly_chart(map_fig, use_container_width=True)
        else:
            st.info("No earthquake data to display for the selected criteria.")
    
  
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### Key Statistics")
    st.markdown("<br>", unsafe_allow_html=True)

    if data_count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Strongest Earthquake", f"{earthquake_data['magnitude'].max():.1f}")
        with col2:
            st.metric("Average Magnitude", f"{earthquake_data['magnitude'].mean():.1f}")
        with col3:
            st.metric("Deepest Earthquake", f"{earthquake_data['depth'].min():.1f} km")

with tab2:

    if not earthquake_data.empty:

        display_df = earthquake_data.copy()
        if 'time' in display_df.columns:

            display_df['time_utc'] = pd.to_datetime(display_df['time']).dt.strftime('%Y-%m-%d %H:%M:%S')

            pacific = pytz.timezone('US/Pacific')
            display_df['time_pacific'] = pd.to_datetime(display_df['time'], utc=True)
            display_df['time_pacific'] = display_df['time_pacific'].dt.tz_convert(pacific)
            display_df['time_pacific'] = display_df['time_pacific'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Rename columns for better display
        display_df = display_df.rename(columns={
            'unid': 'ID',
            'time_utc': 'Time (UTC)', 
            'time_pacific': 'Time (Pacific)',
            'region': 'Region', 
            'latitude': 'Latitude', 
            'longitude': 'Longitude',
            'depth': 'Depth (km)', 
            'magnitude': 'Magnitude',
            'action': 'Status'
        })
        
        # Reorder columns
        columns = ['ID', 'Time (UTC)', 'Time (Pacific)', 'Magnitude', 'Region', 'Latitude', 'Longitude', 'Depth (km)', 'Status']
        display_df = display_df[[col for col in columns if col in display_df.columns]]
        
        st.dataframe(
            display_df, 
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No earthquake data to display for the selected criteria.")

# Footer with refresh button
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Refresh Data Now"):
        st.session_state.last_updated = datetime.now()
        st.rerun()

# Footer with information
st.markdown("---")
st.markdown("""
**Data Source:** Real-time earthquake data from seismic monitoring stations around the world.
""") 