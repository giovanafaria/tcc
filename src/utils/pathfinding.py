import os
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from queue import PriorityQueue

def load_elevation(width, height):
    """
    creates random elevation grid #TODO: replace with real one
    """
    np.random.seed(42)
    return np.random.rand(height, width)

def load_paths(width, height, shapefile):
    """
    reads shapefile and creates boolean mask of grid cells that lie on a path
    """
    os.environ["SHAPE_RESTORE_SHX"] = "YES"
    
    file = gpd.read_file(shapefile)
    # false = no path, true = path present
    mask = np.zeros((height, width), dtype=bool)

    #TODO: change it for large grids (my case later?)
    for y in range(height): # check if its center point is contained in any of the geometries
        for x in range(width):
            cell_point = Point(x + 0.5, y + 0.5)
            if file.contains(cell_point).any():
                mask[y, x] = True
    return mask

def a_star_path(grid, start, goal, path_mask=None):
    """
    Finding shortest paths with A* algorithm
    If a cell is on a path (per path_mask), it has lower movement cost
    """
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    # Manhattan distance heuristic
    def heuristic(a, b):
        (x1, y1) = a
        (x2, y2) = b
        return abs(x1 - x2) + abs(y1 - y2)

    while not frontier.empty():
        _, current = frontier.get()
        if current == goal:
            break

        neighbors = grid.get_neighborhood(current, moore=True, include_center=False)
        for neighbor in neighbors:
            # if its provided, prefer cells on a path
            if path_mask is not None:
                cost_factor = 1 if path_mask[neighbor[1], neighbor[0]] else 2
            else:
                cost_factor = 1
            new_cost = cost_so_far[current] + 1

            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(goal, neighbor)
                frontier.put((priority, neighbor))
                came_from[neighbor] = current

    # reconstruct the path from the start to goal if reachable
    path = []
    curr = goal
    while curr and curr in came_from:
        path.insert(0, curr)
        curr = came_from[curr]
    return path
