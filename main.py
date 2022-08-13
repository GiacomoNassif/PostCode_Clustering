import streamlit as st
from DashBoardData import modelling_df, modelling_df_nonprocessed
import numpy as np
from models.ClusteringModel import get_dynamic_neighbours
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from DataEDA import load_geodata
from StreamlitGraphics import plot_title

plot_title()


@st.cache(allow_output_mutation=True)
def get_geo_data():
    return load_geodata()


geodata = get_geo_data()


@st.cache
def get_sidebar_selector():
    modelling_df_nonprocessed.insert(0, 'Suburb Name', '')
    modelling_df_nonprocessed['Suburb Name'] = geodata['Suburb Name']

    sidebar_names = modelling_df_nonprocessed.reset_index().agg(lambda x: f'{x["Suburb Name"]} ({x["SUBURB_CODE"]})',
                                                                axis=1)
    modelling_df_nonprocessed.drop(columns='Suburb Name', axis=1, inplace=True)
    return sidebar_names, dict(zip(sidebar_names, list(modelling_df_nonprocessed.index)))


@st.cache
def get_perth_index():
    sidebar_names, _ = get_sidebar_selector()
    return next(i for i, val in enumerate(sidebar_names) if val == 'Perth (WA) (51230)')


sidebar_names, mapping = get_sidebar_selector()

selected_postcode_original = st.sidebar.selectbox('Choose a Postcode to find neighbours of', sidebar_names,
                                                  index=get_perth_index())
selected_postcode = mapping[selected_postcode_original]

tab1, tab2, tab3 = st.tabs(['Map', 'Neighbour Data', 'Hyper parameters'])

with tab3:
    radius = st.sidebar.slider('Starting Radius', min_value=1, max_value=50_000, value=1000, step=50)
    multiplicative_factor = st.sidebar.slider('Radius Multiplier', min_value=1., max_value=10., value=2., step=0.1)

    required_exposure = st.sidebar.slider('Minimum Exposure', min_value=0., max_value=50_000., step=10.)

nearest_neighbours, distances, geometries_used = get_dynamic_neighbours(
    starting_radius=radius,
    multiplying_factor=multiplicative_factor,
    geo_data=geodata,
    exposure_data=modelling_df_nonprocessed['Exposure'],
    attribute_data=modelling_df,
    current_index=selected_postcode,
    required_exposure=required_exposure
)

distances = np.round(distances, 2)

nearest_neighbour_attributes = modelling_df_nonprocessed.loc[nearest_neighbours, :]
nearest_neighbour_attributes.insert(0, 'Rank', np.arange(len(nearest_neighbour_attributes)))
nearest_neighbour_attributes.insert(1, 'Distance', distances)

chosen_start = st.sidebar.selectbox('Goto this neighbour: ', nearest_neighbour_attributes.index)
st.sidebar.write(f'Total Exposure = {nearest_neighbour_attributes["Exposure"].sum():.2f}')

if nearest_neighbours[0] != selected_postcode:
    st.error("The nearest neighbour isn't itself???")

geo_data: gpd.GeoDataFrame = geodata.loc[nearest_neighbours, :]
geo_data = geo_data.join(nearest_neighbour_attributes)

chosen_centroid = geo_data.loc[[chosen_start], 'geometry'].to_crs('EPSG:4283').centroid
lat, long = chosen_centroid.x, chosen_centroid.y

m = folium.Map(location=[long, lat], zoom_start=12)

with tab1:
    geo_data['Exposure'] = modelling_df_nonprocessed['Exposure']
    geo_data.explore(
        column=distances,
        m=m,
        cmap='cividis',
        tooltip=['Rank', 'Distance', 'Suburb Name', 'Exposure'],
    )

    for geometry in geometries_used:
        current_geometry = gpd.GeoDataFrame(index=[0], crs='EPSG:3112', geometry=[geometry])
        folium.GeoJson(current_geometry.boundary).add_to(m)
    #m(geometries_used[-1].bounds)

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
