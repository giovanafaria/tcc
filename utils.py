import numpy as np
from queue import PriorityQueue

def load_elevation(width, height):
    """
    creates random elevation grid #TODO: replace with real one
    """
    np.random.seed(42)
    return np.random.rand(height, width)

def a_star_path(grid, start, goal):
    """
    Finding shortest paths with A* algorithm
    """
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while not frontier.empty():
        _, current = frontier.get()
        if current == goal:
            break

        for neighbor in grid.get_neighborhood(current, moore=True, include_center=False):
            new_cost = cost_so_far[current] + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost
                frontier.put((priority, neighbor))
                came_from[neighbor] = current

    path = []
    curr = goal
    while curr and curr in came_from:
        path.insert(0, curr)
        curr = came_from[curr]
    return path
