import functools

import pandas as pd
import streamlit as st
from DashBoardData import modelling_df, modelling_df_nonprocessed
import numpy as np
from models.ClusteringModel import get_dynamic_neighbours
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from DataEDA import load_geodata
from StreamlitGraphics import plot_title
import time

plot_title()


@st.experimental_singleton
def get_geo_data():
    return load_geodata()


geodata = get_geo_data()

if 'map_cache' not in st.session_state:
    st.session_state['map_cache'] = dict()


@st.experimental_singleton
def get_sidebar_selector():
    modelling_df_nonprocessed.insert(0, 'Suburb Name', '')
    modelling_df_nonprocessed['Suburb Name'] = geodata['Suburb Name']

    sidebar_names = modelling_df_nonprocessed.reset_index().agg(lambda x: f'{x["Suburb Name"]} ({x["SUBURB_CODE"]})',
                                                                axis=1)
    modelling_df_nonprocessed.drop(columns='Suburb Name', axis=1, inplace=True)
    return sidebar_names, dict(zip(sidebar_names, list(modelling_df_nonprocessed.index)))


@st.experimental_singleton
def get_perth_index():
    sidebar_names, _ = get_sidebar_selector()
    return next(i for i, val in enumerate(sidebar_names) if val == 'Perth (WA) (51230)')


sidebar_names, mapping = get_sidebar_selector()

selected_postcode_original = st.sidebar.selectbox('Choose a Postcode to find neighbours of', sidebar_names,
                                                  index=get_perth_index())
selected_postcode = mapping[selected_postcode_original]

tab1, tab2, tab3 = st.tabs(['Map', 'Neighbour Data', 'Hyper parameters'])

with tab3:
    radius = st.slider('Starting Radius', min_value=1, max_value=50_000, value=1000, step=50)
    multiplicative_factor = st.slider('Radius Multiplier', min_value=1., max_value=10., value=2., step=0.1)

    required_exposure = st.slider('Minimum Exposure', min_value=0., max_value=50_000., step=10.)


@st.experimental_memo(max_entries=1)
def get_neighbours(starting_radius: float, multiplying_factor: float, current_index, required_exposure):
    return get_dynamic_neighbours(
        starting_radius=starting_radius,
        multiplying_factor=multiplying_factor,
        geo_data=geodata,
        exposure_data=modelling_df_nonprocessed['Exposure'],
        attribute_data=modelling_df,
        current_index=current_index,
        required_exposure=required_exposure
    )


nearest_neighbours, distances, geometries_used = get_neighbours(radius, multiplicative_factor, selected_postcode,
                                                                required_exposure)

distances = np.round(distances, 2)


@st.experimental_memo(max_entries=1)
def get_nearest_neighbour_attributes(radius, multiplicative_factor, selected_postcode, required_exposure):
    nearest_neighbours, *_ = get_neighbours(radius, multiplicative_factor, selected_postcode, required_exposure)

    nearest_neighbour_attributes = modelling_df_nonprocessed.loc[nearest_neighbours, :]
    nearest_neighbour_attributes.insert(0, 'Rank', np.arange(len(nearest_neighbour_attributes)))
    nearest_neighbour_attributes.insert(1, 'Distance', distances)

    return nearest_neighbour_attributes, nearest_neighbour_attributes["Exposure"].sum()


nearest_neighbour_attributes, current_exposure = get_nearest_neighbour_attributes(radius, multiplicative_factor, selected_postcode, required_exposure)

# chosen_start = st.sidebar.selectbox('Goto this neighbour: ', nearest_neighbour_attributes.index)
chosen_start = selected_postcode
st.sidebar.write(f'Total Exposure = {current_exposure:.2f}')

if nearest_neighbours[0] != selected_postcode:
    st.error("The nearest neighbour isn't itself???")

with tab1:
    def generate_map(radius, multiplicative_factor, selected_postcode, required_exposure):

        if (radius, multiplicative_factor, selected_postcode, required_exposure) in st.session_state.map_cache:
            return st.session_state.map_cache[(radius, multiplicative_factor, selected_postcode, required_exposure)]

        nearest_neighbours, distances, geometries_used = get_neighbours(radius, multiplicative_factor,
                                                                        selected_postcode,
                                                                        required_exposure)

        geo_data: gpd.GeoDataFrame = geodata.loc[nearest_neighbours, :]
        geo_data = geo_data.join(nearest_neighbour_attributes)

        chosen_centroid = geo_data.loc[[chosen_start], 'geometry'].to_crs('EPSG:4283').centroid
        lat, long = chosen_centroid.x, chosen_centroid.y

        map_element = folium.Map(location=[long, lat], zoom_start=12)

        geo_data['Exposure'] = modelling_df_nonprocessed['Exposure']
        geo_data.explore(
            column=distances,
            m=map_element,
            cmap='cividis',
            tooltip=['Rank', 'Distance', 'Suburb Name', 'Exposure'],
        )

        for geometry in geometries_used:
            current_geometry = gpd.GeoDataFrame(index=[0], crs='EPSG:3112', geometry=[geometry])
            folium.GeoJson(current_geometry.boundary).add_to(map_element)

        st.session_state.map_cache = dict()
        st.session_state.map_cache[(radius, multiplicative_factor, selected_postcode, required_exposure)] = map_element

        return map_element


    m = generate_map(radius, multiplicative_factor, selected_postcode, required_exposure)

    st_data = st_folium(m, height=700, width=700)

with tab2:
    st.write(nearest_neighbour_attributes)


    @st.cache
    def convert_to_csv(df):
        return df.to_csv().encode('utf-8')


    st.download_button(
        'Download Data',
        convert_to_csv(nearest_neighbour_attributes),
        file_name=f'{selected_postcode_original} DynamicClustering.csv'
    )

if 'bulkquery' not in st.session_state:
    st.session_state['bulkquery'] = False


def set_bulk_query(value): st.session_state['bulkquery'] = value


st.sidebar.button('Bulk Query', on_click=lambda: set_bulk_query(True))

if st.session_state['bulkquery']:

    result_dict = dict()

    my_bar = st.sidebar.progress(0.)
    for index, current_postcode in enumerate(modelling_df.index):
        current_nearest_neighbours, current_distances, current_geometries = get_neighbours(radius,
                                                                                           multiplicative_factor,
                                                                                           current_postcode,
                                                                                           required_exposure)

        total_exposure = modelling_df_nonprocessed['Exposure'].loc[current_nearest_neighbours].sum()
        result_dict[current_postcode] = [
            list(current_nearest_neighbours[1:]),
            len(current_distances[1:]),
            current_distances[1:],
            len(current_geometries),
            total_exposure
        ]

        my_bar.progress((index + 1) / len(modelling_df))

    my_bar.empty()

    result_data = pd.DataFrame.from_dict(
        result_dict,
        orient='index',
        columns=['Dynamic Neighbours', 'Neighbours Used', 'Distances', 'Radii Used', 'Accumulated Exposure'],
    )
    result_data.index.names = ['Suburb Code']

    st.sidebar.download_button(
        'Download!',
        data=result_data.to_csv().encode('utf-8'),
        file_name=f'Dynamic Neighbours: Radius={radius} Radius Scaling={multiplicative_factor} Minimum Exposure={required_exposure}.csv'
    )

    set_bulk_query(False)
