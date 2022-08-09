import streamlit as st
from DashBoardData import modelling_df, postcode_geodata, modelling_df_nonprocessed
import numpy as np
from models.ClusteringModel import get_nearest_neighbours
import geopandas as gpd
from streamlit_folium import st_folium
import folium

st.title('Nearest Neighbour Analysis')

chosen_neighbours = st.sidebar.slider(
    label='Choose the number of neighbours to find: ',
    min_value=1,
    max_value=10,
    value=3,
    step=1,
)

tab1, tab2, tab3 = st.tabs(['Map', 'Neighbour Data', 'Hyper parameters'])

with tab3:
    distance_contribution = st.slider(
        label='Distance Contribution to loss',
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.01
    )

selected_postcode = st.sidebar.selectbox('Choose a Postcode to find neighbours of', modelling_df.index)

distances, nearest_neighbours = get_nearest_neighbours(selected_postcode, chosen_neighbours, distance_contribution)
distances = np.round(distances, 2)

nearest_neighbour_attributes = modelling_df_nonprocessed.loc[nearest_neighbours, :]
nearest_neighbour_attributes.insert(0, 'Rank', np.arange(chosen_neighbours + 1))
nearest_neighbour_attributes.insert(1, 'Distance', distances)


chosen_start = st.sidebar.selectbox('Goto this neighbour: ', nearest_neighbour_attributes.index)

if nearest_neighbours[0] != selected_postcode:
    st.error("The nearest neighbour isn't itself???")

geo_data: gpd.GeoDataFrame = postcode_geodata.loc[nearest_neighbours, :]
geo_data = geo_data.join(nearest_neighbour_attributes)

chosen_centroid = geo_data.centroid.loc[chosen_start]
lat, long = chosen_centroid.x, chosen_centroid.y

m = folium.Map(location=[long, lat], zoom_start=12)

geo_data.explore(
    column=distances,
    m=m,
    cmap='cividis',
    tooltip=['Rank', 'Distance', 'Postcode'],
)
with tab1:
    st_data = st_folium(m, height=700, width=700)


with tab2:
    st.write(nearest_neighbour_attributes)