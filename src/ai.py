from collections import deque
from random import choice, shuffle
from time import time
from typing import Optional

from data_structs import SeenTiles
from game_types import (
    UNIT_TYPE_STATS,
    Ant,
    AntMoveCommand,
    FoodOnMap,
    Hex,
    HexType,
    PlayerEnemy,
    PlayerMoveCommands,
    PlayerResponse,
    Tile,
    UnitType,
)
from hex import distance, neighbors
from pathfinding import (
    PathTruncator,
    bfs_to_nearest_unexplored,
    find_min_cost_path_to_any,
)


class AIMemory:
    def __init__(self):
        self.food: dict[Hex, FoodOnMap] = {}
        self.enemies: dict[Hex, PlayerEnemy] = {}

    def update_food(self, player_response: PlayerResponse):
        current_food_hexes = {
            Hex(food.q, food.r): food for food in player_response.food
        }
        map_hexes = set(Hex(tile.q, tile.r) for tile in player_response.map)
        # forget food that is known to be non-existent
        for old_hex, _ in list(self.food.items()):
            # check if we see the food hex
            if old_hex in map_hexes:
                # we see the food hex, check if it's still there
                if old_hex in current_food_hexes:
                    # it's still there, keep it in memory
                    self.food[old_hex] = current_food_hexes[old_hex]
                else:
                    # it's not there, forget it
                    self.forget_food(old_hex)
            else:
                # if we don't see the food hex, keep it in memory
                pass

        for hex_, food in current_food_hexes.items():
            self.food[hex_] = food

    def forget_food(self, hex_: Hex):
        if hex_ in self.food:
            del self.food[hex_]

    def get_food_hexes(self):
        return set(self.food.keys())

    def update_enemies(self, player_response: PlayerResponse):
        current_enemies = {Hex(e.q, e.r): e for e in player_response.enemies}
        map_hexes = set(Hex(tile.q, tile.r) for tile in player_response.map)
        # forget enemies that are known to be non-existent
        for old_hex, _ in list(self.enemies.items()):
            # check if we see the enemy hex
            if old_hex in map_hexes:
                # we see the enemy hex, check if it's still there
                if old_hex in current_enemies:
                    # it's still there, keep it in memory
                    self.enemies[old_hex] = current_enemies[old_hex]
                else:
                    # it's not there, forget it
                    self.forget_enemy(old_hex)
            else:
                # if we don't see the enemy hex, keep it in memory
                pass

        for hex_, enemy in current_enemies.items():
            self.enemies[hex_] = enemy

    def forget_enemy(self, hex_: Hex):
        if hex_ in self.enemies:
            del self.enemies[hex_]

    def get_enemy_hexes(self):
        return set(self.enemies.keys())


class AI:
    def __init__(self):
        self.seen_tiles = SeenTiles()
        self.taken_destinations: set[Hex] = set()
        self.path_truncator = PathTruncator(self.seen_tiles, self.taken_destinations)
        self._scout_bfs_cache = {}  # (ant_pos, unexplored_key) -> path
        self._scout_bfs_cache_tiles_count = 0
        self.memory = AIMemory()
        self.same_place_counter: dict[Hex, tuple[str, int]] = {}

    # Pathfinding logic moved to pathfinding.py
    # def _bfs_to_nearest_unexplored ...
    # def _find_min_cost_path ...
    # def _find_min_cost_path_to_any ...

    def _update_same_place_counter(self, ants: list[Ant]):
        for ant in ants:
            ant_pos = Hex(ant.q, ant.r)
            if (
                ant_pos in self.same_place_counter
                and self.same_place_counter[ant_pos][0] == ant.id
            ):
                self.same_place_counter[ant_pos] = (
                    ant.id,
                    self.same_place_counter[ant_pos][1] + 1,
                )
            else:
                self.same_place_counter[ant_pos] = (ant.id, 1)

    def unstuck_same_place(
        self, ant: Ant, player_response: PlayerResponse
    ) -> Optional[AntMoveCommand]:
        ant_pos = Hex(ant.q, ant.r)
        if (
            ant_pos in self.same_place_counter
            and self.same_place_counter[ant_pos][0] == ant.id
            and self.same_place_counter[ant_pos][1] > 5
        ):
            return self.unstuck(ant, player_response)
        return None

    def _pick_valid_neighbor(
        self,
        ant_pos: Hex,
        exclude: Optional[set[Hex]] = None,
        not_on_food: Optional[set[Hex]] = None,
        not_stone: bool = False,
        not_on_hive: Optional[set[Hex]] = None,
    ) -> Optional[Hex]:
        """Pick a valid neighbor for fallback movement, with optional filters."""
        neighbors_list = list(neighbors(ant_pos))
        shuffle(neighbors_list)
        for neighbor in neighbors_list:
            if exclude and neighbor in exclude:
                continue
            if not_on_food and neighbor in not_on_food:
                continue
            if not_on_hive and neighbor in not_on_hive:
                continue
            if not_stone:
                tile = self.seen_tiles.get(neighbor)
                if not tile or tile.type == HexType.STONE:
                    continue
            return neighbor
        return None

    def _mark_taken_destinations(self, path: list[Hex]):
        for hex in path:
            self.taken_destinations.add(hex)

    def _get_cached_scout_path(
        self, ant_pos: Hex, unexplored: set[Hex], food_hexes: set[Hex]
    ) -> list[Hex]:
        unexplored_key = (ant_pos, frozenset(unexplored))
        # Invalidate cache if new tiles were added
        if len(self.seen_tiles) != self._scout_bfs_cache_tiles_count:
            self._scout_bfs_cache.clear()
            self._scout_bfs_cache_tiles_count = len(self.seen_tiles)
        if unexplored_key in self._scout_bfs_cache:
            return self._scout_bfs_cache[unexplored_key]
        min_path = bfs_to_nearest_unexplored(
            ant_pos, unexplored, food_hexes, self.seen_tiles
        )
        self._scout_bfs_cache[unexplored_key] = min_path
        return min_path

    def move_to_hive(self, ant: Ant, player_response: PlayerResponse) -> AntMoveCommand:
        ant_pos = Hex(ant.q, ant.r)
        min_path = find_min_cost_path_to_any(
            ant_pos, set(player_response.home), self.seen_tiles, self.taken_destinations
        )
        move_path = self.path_truncator.truncate(ant, min_path)
        self._mark_taken_destinations(move_path)
        return AntMoveCommand(ant=ant.id, path=move_path)

    def go_to_food(self, ant: Ant, player_response: PlayerResponse) -> AntMoveCommand:
        ant_pos = Hex(ant.q, ant.r)
        # Use both current and remembered food
        food_hexes = set(Hex(food.q, food.r) for food in player_response.food)
        memory_food_hexes = self.memory.get_food_hexes()
        all_food_hexes = food_hexes | memory_food_hexes

        # --- Filter NECTAR on enemy hives for WORKER ants ---
        if ant.type == UnitType.WORKER:
            # Identify all anthill tiles
            home_hexes = set(player_response.home)
            anthill_hexes = set(
                Hex(tile.q, tile.r)
                for tile in player_response.map
                if tile.type == HexType.ANTHILL
            )
            enemy_hive_hexes = anthill_hexes - home_hexes
            # Build a set of food hexes that are NECTAR on enemy hives
            nectar_on_enemy_hive = set(
                Hex(food.q, food.r)
                for food in player_response.food
                if food.type == 3
                and Hex(food.q, food.r) in enemy_hive_hexes  # 3 == FoodType.NECTAR
            )
            # Also filter from memory
            nectar_on_enemy_hive |= set(
                hex_
                for hex_ in memory_food_hexes
                if ((self.memory.food[hex_].type == 3) and (hex_ in enemy_hive_hexes))
            )
            all_food_hexes = all_food_hexes - nectar_on_enemy_hive
        # --- End filter ---

        # Exclude food hexes already taken by other ants
        available_food_hexes = all_food_hexes - self.taken_destinations
        if not available_food_hexes:
            return AntMoveCommand(ant=ant.id, path=[])
        min_path = find_min_cost_path_to_any(
            ant_pos, available_food_hexes, self.seen_tiles, self.taken_destinations
        )
        move_path = self.path_truncator.truncate(ant, min_path)
        self._mark_taken_destinations(move_path)
        return AntMoveCommand(ant=ant.id, path=move_path)

    def move_scout_explore(
        self, ant: Ant, player_response: PlayerResponse
    ) -> AntMoveCommand:
        seen_hexes = set(self.seen_tiles.keys())
        known_hexes = set(Hex(tile.q, tile.r) for tile in player_response.map)
        unexplored = seen_hexes - known_hexes
        food_hexes = set(Hex(food.q, food.r) for food in self.memory.get_food_hexes())
        unexplored = unexplored - food_hexes
        DANGER_RADIUS = 4
        ant_pos = Hex(ant.q, ant.r)
        enemy_hexes = set(Hex(e.q, e.r) for e in player_response.enemies)
        close_enemies = [
            e for e in enemy_hexes if distance(ant_pos, e) <= DANGER_RADIUS
        ]
        if close_enemies:
            # Flee: find the most distant reachable hex from all enemies within speed

            speed = UNIT_TYPE_STATS[UnitType(ant.type)].speed
            visited = set()
            queue = deque()
            queue.append((ant_pos, [ant_pos], 0))  # (current, path, cost)
            best_path = None
            best_min_dist = -1
            while queue:
                curr, path, cost = queue.popleft()
                if curr in visited:
                    continue
                visited.add(curr)
                if cost > speed:
                    continue
                # Only consider non-initial positions for fleeing
                if curr != ant_pos:
                    tile = self.seen_tiles.get(curr)
                    if not tile or tile.type == HexType.STONE:
                        continue
                    if curr in self.taken_destinations or curr in food_hexes:
                        continue
                    min_dist = (
                        min(distance(curr, e) for e in enemy_hexes)
                        if enemy_hexes
                        else 999
                    )
                    if min_dist > best_min_dist or (
                        min_dist == best_min_dist and best_path is None
                    ):
                        best_min_dist = min_dist
                        best_path = path[1:]  # exclude start
                for neighbor in neighbors(curr):
                    if neighbor in visited:
                        continue
                    tile = self.seen_tiles.get(neighbor)
                    if not tile or tile.type == HexType.STONE:
                        continue
                    step_cost = 1
                    if tile.type == HexType.DIRT:
                        step_cost = 2
                    if cost + step_cost > speed:
                        continue
                    queue.append((neighbor, path + [neighbor], cost + step_cost))
            if best_path:
                self._mark_taken_destinations(best_path)
                return AntMoveCommand(ant=ant.id, path=best_path)
            # fallback: if all are blocked, just pick any non-taken neighbor
            fallback = self._pick_valid_neighbor(
                ant_pos, exclude=self.taken_destinations
            )
            if fallback:
                self.taken_destinations.add(fallback)
                return AntMoveCommand(ant=ant.id, path=[fallback])
            return AntMoveCommand(ant=ant.id, path=[])
        if not unexplored:
            # fallback: move to random neighbor not on food
            fallback = self._pick_valid_neighbor(
                ant_pos, exclude=self.taken_destinations, not_on_food=food_hexes
            )
            if fallback:
                self.taken_destinations.add(fallback)
                return AntMoveCommand(ant=ant.id, path=[fallback])
            # if all neighbors are food or taken, just pick any
            fallback = self._pick_valid_neighbor(
                ant_pos, exclude=self.taken_destinations
            )
            if fallback:
                self.taken_destinations.add(fallback)
                return AntMoveCommand(ant=ant.id, path=[fallback])
            return AntMoveCommand(ant=ant.id, path=[])
        min_path = self._get_cached_scout_path(ant_pos, unexplored, food_hexes)
        move_path = self.path_truncator.truncate(ant, min_path)
        while move_path and move_path[-1] in food_hexes:
            move_path = move_path[:-1]
        self._mark_taken_destinations(move_path)
        return AntMoveCommand(ant=ant.id, path=move_path)

    def move_to_enemy(
        self, ant: Ant, player_response: PlayerResponse
    ) -> AntMoveCommand:
        ant_pos = Hex(ant.q, ant.r)
        current_enemies = set(Hex(e.q, e.r) for e in player_response.enemies)
        remembered_enemies = self.memory.get_enemy_hexes() - current_enemies
        min_path = find_min_cost_path_to_any(
            ant_pos, current_enemies, self.seen_tiles, self.taken_destinations
        )
        if not min_path and remembered_enemies:
            min_path = find_min_cost_path_to_any(
                ant_pos, remembered_enemies, self.seen_tiles, self.taken_destinations
            )
        move_path = self.path_truncator.truncate(ant, min_path)
        self._mark_taken_destinations(move_path)
        return AntMoveCommand(ant=ant.id, path=move_path)

    def timeit(self, label: str, func, *args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        end_time = time()
        diff = end_time - start_time
        if diff > 0.1:
            print(f"{label} in {diff} seconds")
        return result

    def unstuck(self, ant: Ant, player_response: PlayerResponse) -> AntMoveCommand:
        ant_pos = Hex(ant.q, ant.r)
        # Build set of hive (anthill) tiles
        hive_hexes = set(
            Hex(tile.q, tile.r)
            for tile in self.seen_tiles.values()
            if tile.type == HexType.ANTHILL
        )
        fallback = self._pick_valid_neighbor(
            ant_pos, exclude=self.taken_destinations, not_on_hive=hive_hexes
        )
        if fallback:
            self.taken_destinations.add(fallback)
            return AntMoveCommand(ant=ant.id, path=[fallback])
        print(f"Ant {ant} is stuck")
        # As a last resort, pick any neighbor not on hive
        neighbors_list = [n for n in neighbors(ant_pos) if n not in hive_hexes]
        # remove stone and acid from neighbors list
        neighbors_list = [
            n
            for n in neighbors_list
            if n not in self.taken_destinations
            and self.seen_tiles.get(n, Tile(cost=0, q=0, r=0, type=HexType.EMPTY)).type
            != HexType.STONE
            and self.seen_tiles.get(n, Tile(cost=0, q=0, r=0, type=HexType.EMPTY)).type
            != HexType.ACID
        ]
        if neighbors_list:
            return AntMoveCommand(ant=ant.id, path=[choice(neighbors_list)])
        # If all neighbors are hives (very rare), just pick any
        neighbors_list = list(neighbors(ant_pos))
        return AntMoveCommand(ant=ant.id, path=[choice(neighbors_list)])

    def get_move_commands(self, player_response: PlayerResponse) -> PlayerMoveCommands:
        new_tiles = self.seen_tiles.update(player_response.map)
        print(
            f"Seen tiles: {len(self.seen_tiles)}, new tiles: {len(new_tiles)}, map: {len(player_response.map)}, ants: {len(player_response.ants)}"
        )

        self.taken_destinations = set()

        # add main hive to taken destinations if we have less than 100 ants
        if len(player_response.ants) < 100:
            self.taken_destinations.add(
                Hex(player_response.spot.q, player_response.spot.r)
            )

        # add stones and acid to taken destinations
        for tile in self.seen_tiles.values():
            if player_response.turnNo > 200:
                if tile.type == HexType.STONE:
                    self.taken_destinations.add(Hex(tile.q, tile.r))
            else:
                if tile.type == HexType.STONE or tile.type == HexType.ACID:
                    self.taken_destinations.add(Hex(tile.q, tile.r))

        # add enemies to taken destinations
        enemy_hexes = set(Hex(e.q, e.r) for e in player_response.enemies)
        self.taken_destinations |= enemy_hexes

        if len(player_response.ants) < 70:
            print("Adding fighter enemies neighbor tiles to taken destinations")
            # add fighter enemies neighbor tiles to taken destinations
            warrior_enemies = [
                e for e in player_response.enemies if e.type == UnitType.FIGHTER
            ]
            for enemy in warrior_enemies:
                for neighbor in neighbors(Hex(enemy.q, enemy.r)):
                    self.taken_destinations.add(neighbor)

        # add food near enemies to taken destinations
        FOOD_NEAR_ENEMY_RADIUS = 3
        food_hexes = self.memory.get_food_hexes()
        for food_hex in food_hexes:
            counter = 0
            for enemy_hex in enemy_hexes:
                if distance(food_hex, enemy_hex) <= FOOD_NEAR_ENEMY_RADIUS:
                    counter += 1
            if counter > 2:
                print(f"Food near enemy: {food_hex}, counter: {counter}")
                self.taken_destinations.add(food_hex)

        self.memory.update_enemies(player_response)
        self.memory.update_food(player_response)

        self._update_same_place_counter(player_response.ants)
        moves: list[AntMoveCommand] = []
        already_moved_ants = set()

        for ant in player_response.ants:
            if ant.food.amount > 0:
                move = self.timeit(
                    f"Ant {ant} moved to hive",
                    self.move_to_hive,
                    ant,
                    player_response,
                )
                already_moved_ants.add(ant.id)
                if move.path:
                    moves.append(move)
                else:
                    moves.append(self.unstuck(ant, player_response))

        for ant in player_response.ants:
            move = self.unstuck_same_place(ant, player_response)
            if move:
                moves.append(move)
                already_moved_ants.add(ant.id)

        for ant in player_response.ants:
            move = None
            if ant.id in already_moved_ants:
                continue
            elif ant.type == UnitType.SCOUT:
                move = self.timeit(
                    f"Ant {ant} explore map",
                    self.move_scout_explore,
                    ant,
                    player_response,
                )
            elif ant.type == UnitType.FIGHTER:
                move = self.timeit(
                    f"Ant {ant} attack enemy",
                    self.move_to_enemy,
                    ant,
                    player_response,
                )
                if not move.path:
                    move = self.timeit(
                        f"Ant {ant} moved to food",
                        self.go_to_food,
                        ant,
                        player_response,
                    )
            else:
                move = self.timeit(
                    f"Ant {ant} moved to food",
                    self.go_to_food,
                    ant,
                    player_response,
                )
            if move.path:
                moves.append(move)
            else:
                moves.append(self.unstuck(ant, player_response))
        return PlayerMoveCommands(moves=moves)
