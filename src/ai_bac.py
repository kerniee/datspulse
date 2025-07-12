from dataclasses import dataclass
from time import time
from game_types import PlayerMoveCommands, PlayerResponse, AntMoveCommand, Hex, HexType
from game_types import Tile
from hex import neighbors
import random
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

    def get_move_commands(
        self, player_response: PlayerResponse
    ) -> PlayerMoveCommands | None:
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

        # simple move
        tiles = {(tile.q, tile.r): tile for tile in player_response.map}
        ant_positions = {(ant.q, ant.r) for ant in ants}
        moves = []
        for ant in ants:
            possible_moves = []
            for n in neighbors(Hex(ant.q, ant.r)):
                tile = tiles.get((n.q, n.r))
                if not tile:
                    continue
                if tile.type == HexType.STONE:
                    continue
                if (n.q, n.r) in ant_positions:
                    continue
                possible_moves.append(n)
            if possible_moves:
                # Move to a random valid neighbor
                target = random.choice(possible_moves)
                moves.append(AntMoveCommand(ant=ant.id, path=[target]))
            else:
                # No valid move, stay in place
                moves.append(AntMoveCommand(ant=ant.id, path=[Hex(ant.q, ant.r)]))
        return PlayerMoveCommands(moves=moves)
