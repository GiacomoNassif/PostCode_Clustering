import functools

from DashBoardData import modelling_df
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import haversine_distances
import numpy as np


def custom_distance(x, y, distance_contribution=0.2):
    coords_x = x[:2].reshape(-1, 2)
    coords_y = y[:2].reshape(-1, 2)

    actual_distance = haversine_distances(coords_x, coords_y)
    # print(coords_x, coords_y)
    # print(actual_distance)

    rest_distance = np.sum((x[2:] - y[2:]) ** 2)

    return actual_distance * distance_contribution + rest_distance * (1 - distance_contribution)


@functools.lru_cache(maxsize=1)
def get_neighbour_algorithm(distance_contribution: float = 0.2):
    nearest_neighbours = NearestNeighbors(
        algorithm='ball_tree',
        metric=custom_distance,
        metric_params={'distance_contribution': distance_contribution}
    )

    nearest_neighbours.fit(modelling_df)

    return nearest_neighbours

@functools.cache
def get_nearest_neighbours(postcode: int, neighbours: int, distance_contribution: float):
    nearest_neighbours = get_neighbour_algorithm(distance_contribution)

    attribute_data = modelling_df.loc[[postcode], :]
    distances, neighbour_indexes = nearest_neighbours.kneighbors(attribute_data, n_neighbors=neighbours + 1)

    return distances.reshape(-1), modelling_df.index[neighbour_indexes.reshape(-1)]
