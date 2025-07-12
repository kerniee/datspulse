from dataclasses import dataclass
from time import time
from game_types import (
    PlayerMoveCommands,
    PlayerResponse,
    AntMoveCommand,
    Hex,
    HexType,
    UNIT_TYPE_STATS,
    UnitType,
)
from game_types import Tile
from hex import neighbors
import itertools


@dataclass
class CostDictValue:
    cost: int
    path: list[Hex]


VERY_LARGE_INT = 999999999


class AI:
    def __init__(self):
        self.seen_tiles: dict[Hex, Tile] = {}
        self.cost_dict: dict[tuple[Hex, Hex], CostDictValue] = {}

    def update_cost_dict(self, new_tiles: list[Tile]):
        # Build a lookup for tile type by Hex
        tile_lookup = {Hex(tile.q, tile.r): tile for tile in self.seen_tiles.values()}

        def tile_cost(tile: Tile) -> int:
            t = HexType(tile.type)
            if t in (HexType.EMPTY, HexType.ANTHILL):
                return 1
            elif t == HexType.DIRT:
                return 2
            else:  # STONE or ACID
                return VERY_LARGE_INT  # Use a large int for impassible

        # For each tile, run Dijkstra to all others
        for start_hex, start_tile in tile_lookup.items():
            # Dijkstra's algorithm
            import heapq

            counter = itertools.count()
            heap: list[tuple[int, int, list[Hex]]] = [
                (0, next(counter), [start_hex])
            ]  # (cost, count, path)
            visited: dict[Hex, int] = {}
            while heap:
                cost_so_far, _, path = heapq.heappop(heap)
                current = path[-1]
                if current in visited and visited[current] <= cost_so_far:
                    continue
                visited[current] = cost_so_far
                # Store cost and path from start_hex to current
                self.cost_dict[(start_hex, current)] = CostDictValue(
                    cost=cost_so_far, path=path.copy()
                )
                for neighbor in neighbors(current):
                    neighbor_tile = tile_lookup.get(neighbor)
                    if not neighbor_tile:
                        continue
                    n_cost = tile_cost(neighbor_tile)
                    if n_cost >= VERY_LARGE_INT:
                        continue  # impassible
                    heapq.heappush(
                        heap, (cost_so_far + n_cost, next(counter), path + [neighbor])
                    )

    def get_move_commands(self, player_response: PlayerResponse) -> PlayerMoveCommands:
        # Update seen_tiles with the latest map info
        new_tiles: list[Tile] = []
        for tile in player_response.map:
            tile_hex = Hex(tile.q, tile.r)
            if tile_hex in self.seen_tiles:
                new_tiles.append(tile)
            else:
                self.seen_tiles[tile_hex] = tile

        start_time = time()
        self.update_cost_dict(new_tiles)
        end_time = time()
        print(f"Time taken to update cost dict: {end_time - start_time} seconds")

        if player_response is None:
            return None
        ants = player_response.ants
        food_on_map = player_response.food
        home_hexes = set((h.q, h.r) for h in player_response.home)
        tiles = {(tile.q, tile.r): tile for tile in player_response.map}
        ant_positions = {(ant.q, ant.r) for ant in ants}

        # Build a lookup for food positions
        food_positions = [(food.q, food.r) for food in food_on_map if food.amount > 0]
        food_hexes = [Hex(q, r) for q, r in food_positions]
        home_hex_objs = [Hex(q, r) for q, r in home_hexes]

        # --- Exploration logic: find frontier hexes (unknown neighbors) ---
        seen_hexes = set(self.seen_tiles.keys())
        frontier_hexes = set()
        for hex in seen_hexes:
            for n in neighbors(hex):
                if n not in seen_hexes:
                    frontier_hexes.add(n)
        # Remove any frontier hexes that are already occupied by ants
        frontier_hexes = [h for h in frontier_hexes if (h.q, h.r) not in ant_positions]

        moves = []
        planned_positions = set(
            ant_positions
        )  # Track where ants will be after this turn
        for ant in ants:
            ant_hex = Hex(ant.q, ant.r)
            ant_type = UnitType(ant.type)
            speed = int(UNIT_TYPE_STATS[ant_type]["speed"])
            print(f"\nAnt {ant.id} ({ant_type}) at {ant_hex}")
            # If ant is carrying food, go home
            if ant.food.amount > 0:
                print("  Carrying food, target: home")
                min_cost = VERY_LARGE_INT
                best_path = [ant_hex]
                for home_hex in home_hex_objs:
                    key = (ant_hex, home_hex)
                    if key in self.cost_dict:
                        cost = self.cost_dict[key].cost
                        path = self.cost_dict[key].path
                        if cost < min_cost:
                            min_cost = cost
                            best_path = path
                print(f"  Best path to home: {best_path}")
                # Path should NOT include current position; only the hexes to move to, up to 'speed' steps
                move_path = best_path[1 : speed + 1] if len(best_path) > 1 else []
                # Only allow moves to hexes not already planned to be occupied
                filtered_path = []
                for h in move_path:
                    if (h.q, h.r) not in planned_positions or (h.q, h.r) == (
                        ant.q,
                        ant.r,
                    ):
                        filtered_path.append(h)
                if not filtered_path:
                    print("  No valid move_path (blocked), fallback to current hex")
                    filtered_path = [ant_hex]
                print(f"  Final move_path: {filtered_path}")
                # Mark the last hex in the path as planned to be occupied
                planned_positions.add((filtered_path[-1].q, filtered_path[-1].r))
                moves.append(AntMoveCommand(ant=ant.id, path=filtered_path))
            else:
                # --- Exploration logic for scouts ---
                if ant_type == UnitType.SCOUT and not food_hexes and frontier_hexes:
                    print("  Scout exploring, target: frontier")
                    min_cost = VERY_LARGE_INT
                    best_path = [ant_hex]
                    for frontier_hex in frontier_hexes:
                        key = (ant_hex, frontier_hex)
                        if key in self.cost_dict:
                            cost = self.cost_dict[key].cost
                            path = self.cost_dict[key].path
                            if cost < min_cost:
                                min_cost = cost
                                best_path = path
                    print(f"  Best path to frontier: {best_path}")
                    # Path should NOT include current position; only the hexes to move to, up to 'speed' steps
                    move_path = best_path[1 : speed + 1] if len(best_path) > 1 else []
                    filtered_path = []
                    for h in move_path:
                        if (h.q, h.r) not in planned_positions or (h.q, h.r) == (
                            ant.q,
                            ant.r,
                        ):
                            filtered_path.append(h)
                    if not filtered_path:
                        print("  No valid move_path (blocked), fallback to current hex")
                        filtered_path = [ant_hex]
                    print(f"  Final move_path: {filtered_path}")
                    planned_positions.add((filtered_path[-1].q, filtered_path[-1].r))
                    moves.append(AntMoveCommand(ant=ant.id, path=filtered_path))
                else:
                    print("  Not carrying food, target: food")
                    min_cost = VERY_LARGE_INT
                    best_path = [ant_hex]
                    for food_hex in food_hexes:
                        key = (ant_hex, food_hex)
                        if key in self.cost_dict:
                            cost = self.cost_dict[key].cost
                            path = self.cost_dict[key].path
                            if cost < min_cost:
                                min_cost = cost
                                best_path = path
                    print(f"  Best path to food: {best_path}")
                    # Path should NOT include current position; only the hexes to move to, up to 'speed' steps
                    move_path = best_path[1 : speed + 1] if len(best_path) > 1 else []
                    filtered_path = []
                    for h in move_path:
                        if (h.q, h.r) not in planned_positions or (h.q, h.r) == (
                            ant.q,
                            ant.r,
                        ):
                            filtered_path.append(h)
                    if not filtered_path:
                        print("  No valid move_path (blocked), fallback to current hex")
                        filtered_path = [ant_hex]
                    print(f"  Final move_path: {filtered_path}")
                    planned_positions.add((filtered_path[-1].q, filtered_path[-1].r))
                    moves.append(AntMoveCommand(ant=ant.id, path=filtered_path))
        return PlayerMoveCommands(moves=moves)
