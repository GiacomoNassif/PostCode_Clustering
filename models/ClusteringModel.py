import functools

from DashBoardData import modelling_df
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import haversine_distances
import numpy as np


def get_neighbour_algorithm(df):
    nearest_neighbours = NearestNeighbors(
        algorithm='kd_tree'
    )

    nearest_neighbours.fit(df)

    return nearest_neighbours


def get_nearest_neighbours(df, postcode: int, neighbours: int):
    nearest_neighbours = get_neighbour_algorithm(df)

    attribute_data = df.loc[[postcode], :]
    distances, neighbour_indexes = nearest_neighbours.kneighbors(attribute_data, n_neighbors=neighbours + 1)

    return distances.reshape(-1), df.index[neighbour_indexes.reshape(-1)]
