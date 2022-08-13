import functools
import geopandas as gpd
import pandas as pd
from sklearn.neighbors import NearestNeighbors


def get_enough_exposure(
        starting_radius: float,
        multiplying_factor: float,
        geo_data: gpd.GeoDataFrame,
        exposure_data: pd.Series,
        current_index,
        required_exposure: float
):
    current_geospace = geo_data.loc[current_index, 'geometry']
    current_indexes = [current_index]
    filtered_exposure = exposure_data.loc[current_indexes]
    used_geospaces = []

    while filtered_exposure.sum() < required_exposure:
        current_geospace = current_geospace.buffer(starting_radius)
        used_geospaces.append(current_geospace)

        overlapping_geometries = geo_data.index[geo_data.within(current_geospace)]
        current_indexes = overlapping_geometries.union(geo_data.index[geo_data.overlaps(current_geospace)])

        filtered_exposure = exposure_data.loc[current_indexes]

        if filtered_exposure.sum() > required_exposure:
            break

        starting_radius *= multiplying_factor

    return current_indexes, used_geospaces


def get_dynamic_neighbours(
        starting_radius: float,
        multiplying_factor: float,
        geo_data: gpd.GeoDataFrame,
        exposure_data: pd.Series,
        attribute_data: pd.DataFrame,
        current_index,
        required_exposure: float
):
    indexes, used_geoshapes = get_enough_exposure(
        starting_radius,
        multiplying_factor,
        geo_data,
        exposure_data,
        current_index,
        required_exposure
    )

    exposure_data = exposure_data.loc[indexes]
    attribute_data = attribute_data.loc[indexes, :]


    # TODO: This is me being lazy. Remove the KNN and just store a distance matrix from the start.
    nearest_neighbours = NearestNeighbors(
        algorithm='kd_tree'
    )
    nearest_neighbours.fit(attribute_data)
    distances, neighbour_indexes = nearest_neighbours.kneighbors(attribute_data.loc[[current_index], :], n_neighbors=len(attribute_data))
    distances = distances.reshape(-1)
    attribute_indexes = attribute_data.index[neighbour_indexes.reshape(-1)]

    current_exposure = 0
    count = 0
    for index in attribute_indexes:
        if current_exposure > required_exposure:
            break

        current_exposure += exposure_data[index]
        count += 1

    return attribute_indexes[:count], distances[:count], used_geoshapes