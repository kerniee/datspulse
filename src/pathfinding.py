"""
Pathfinding utilities for ant AI.
"""

from typing import List, Set

from data_structs import VERY_LARGE_INT, SeenTiles
from game_types import UNIT_TYPE_STATS, Ant, Hex, HexType, Tile, UnitType
from hex import neighbors


def tile_cost(tile: Tile) -> int:
    t = HexType(tile.type)
    if t in (HexType.EMPTY, HexType.ANTHILL):
        return 1
    elif t == HexType.DIRT:
        return 2
    else:  # STONE or ACID
        return VERY_LARGE_INT  # Use a large int for impassible


class PathTruncator:
    def __init__(self, seen_tiles: SeenTiles, taken_destinations: Set[Hex]):
        self.seen_tiles = seen_tiles
        self.taken_destinations = taken_destinations

    def truncate(self, ant: Ant, path: List[Hex]) -> List[Hex]:
        speed = UNIT_TYPE_STATS[UnitType(ant.type)].speed
        if not path or len(path) < 2:
            return []
        truncated = []
        total_cost = 0
        for i in range(1, len(path)):
            curr = path[i]
            tile = self.seen_tiles.get(curr)
            if not tile:
                break
            step_cost = tile_cost(tile)
            if total_cost + step_cost > speed:
                break
            truncated.append(curr)
            total_cost += step_cost
        for i in range(1, len(truncated)):
            if truncated[i] in self.taken_destinations:
                truncated = truncated[:i]
                break
        return truncated


def bfs_to_nearest_unexplored(
    start_hex: Hex, unexplored: Set[Hex], food_hexes: Set[Hex], seen_tiles: SeenTiles
) -> List[Hex]:
    import heapq
    import itertools

    queue = []
    counter = itertools.count()
    heapq.heappush(queue, (0, next(counter), [start_hex]))
    visited = set()
    while queue:
        cost_so_far, _, path = heapq.heappop(queue)
        current = path[-1]
        if current in visited:
            continue
        visited.add(current)
        if current in unexplored and current not in food_hexes:
            return path
        for neighbor in neighbors(current):
            if neighbor in visited:
                continue
            tile = seen_tiles.get(neighbor)
            if not tile:
                continue
            n_cost = tile_cost(tile)
            if n_cost >= VERY_LARGE_INT:
                continue
            heapq.heappush(
                queue, (cost_so_far + n_cost, next(counter), path + [neighbor])
            )
    return []


def find_min_cost_path_to_any(
    start: Hex, targets: Set[Hex], seen_tiles: SeenTiles, taken_destinations: Set[Hex]
) -> List[Hex]:
    import heapq
    import itertools

    queue = []
    counter = itertools.count()
    heapq.heappush(queue, (0, next(counter), [start]))
    visited = set()
    found_paths = {}
    valid_targets = targets - taken_destinations
    checked_paths = 0
    MAX_PATHS_TO_CHECK = 10
    while queue and checked_paths < MAX_PATHS_TO_CHECK:
        cost_so_far, _, path = heapq.heappop(queue)
        current = path[-1]
        if current in visited:
            continue
        visited.add(current)
        if current in valid_targets:
            # Validate path: must be more than just the start
            if len(path) > 1:
                found_paths[current] = (cost_so_far, path)
                checked_paths += 1
        for neighbor in neighbors(current):
            if neighbor in visited:
                continue
            if neighbor in taken_destinations and neighbor != start:
                continue
            tile = seen_tiles.get(neighbor)
            if not tile:
                continue
            n_cost = tile_cost(tile)
            if n_cost >= VERY_LARGE_INT:
                continue
            heapq.heappush(
                queue, (cost_so_far + n_cost, next(counter), path + [neighbor])
            )
    if not found_paths:
        return []
    min_food, (min_cost, min_path) = min(found_paths.items(), key=lambda x: x[1][0])
    return min_path
