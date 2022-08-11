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
    max_value=20,
    value=3,
    step=1,
)

tab1, tab2, tab3 = st.tabs(['Map', 'Neighbour Data', 'Hyper parameters'])

with tab3:
    pass


selected_postcode = st.sidebar.selectbox('Choose a Postcode to find neighbours of', modelling_df.index)
radius = st.sidebar.slider('Radius', min_value=0, max_value=50_000, value=1000, step=50)

selected_geospace = postcode_geodata.loc[selected_postcode, 'geometry']
selected_geospace = selected_geospace.buffer(radius)


overlapping_geometries = postcode_geodata.index[postcode_geodata.within(selected_geospace)]
overlapping_geometries = overlapping_geometries.union(postcode_geodata.index[postcode_geodata.overlaps(selected_geospace)])

filtered_geodata = postcode_geodata.loc[overlapping_geometries, :]
filtered_attributes = modelling_df.loc[modelling_df.index.intersection(filtered_geodata.index), :]

if chosen_neighbours > len(filtered_attributes):
    st.warning(f'There is not enough nearby postcodes (only {len(filtered_attributes) - 1}) for your requested number of neighbours {chosen_neighbours}')
    chosen_neighbours = len(filtered_attributes) - 1

distances, nearest_neighbours = get_nearest_neighbours(filtered_attributes, selected_postcode, chosen_neighbours)
distances = np.round(distances, 2)


nearest_neighbour_attributes = modelling_df_nonprocessed.loc[nearest_neighbours, :]
nearest_neighbour_attributes.insert(0, 'Rank', np.arange(chosen_neighbours + 1))
nearest_neighbour_attributes.insert(1, 'Distance', distances)

chosen_start = st.sidebar.selectbox('Goto this neighbour: ', nearest_neighbour_attributes.index)

if nearest_neighbours[0] != selected_postcode:
    st.error("The nearest neighbour isn't itself???")

geo_data: gpd.GeoDataFrame = postcode_geodata.loc[nearest_neighbours, :]
geo_data = geo_data.join(nearest_neighbour_attributes)

chosen_centroid = geo_data.loc[[chosen_start], 'geometry'].to_crs('EPSG:4283').centroid
lat, long = chosen_centroid.x, chosen_centroid.y

m = folium.Map(location=[long, lat], zoom_start=12)

with tab1:
    geo_data.explore(
        column=distances,
        m=m,
        cmap='cividis',
        tooltip=['Rank', 'Distance', 'Postcode'],
    )

    gdf = postcode_geodata.loc[[selected_postcode], :]
    gdf['geometry'] = gdf.buffer(radius)
    x1, y1, x2, y2 = gdf['geometry'].total_bounds

    folium.GeoJson(gdf['geometry'].boundary).add_to(m)

    st_data = st_folium(m, height=700, width=700)

with tab2:
    st.write(nearest_neighbour_attributes)
