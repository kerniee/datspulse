from ai import PathTruncator
from data_structs import (
    SeenTiles,
)
from game_types import Ant, Food, Hex, HexType, Tile, UnitType

# def test_cost_dict_value():
#     h1 = Hex(0, 0)
#     h2 = Hex(1, 0)
#     value = CostDictValue(cost=5, path=[h1, h2])
#     assert value.cost == 5
#     assert value.path == [h1, h2]


# def test_tile_cost():
#     # EMPTY and ANTHILL should be 1
#     tile_empty = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile_anthill = Tile(cost=1, q=0, r=1, type=HexType.ANTHILL)
#     # DIRT should be 2
#     tile_dirt = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
#     # STONE and ACID should be VERY_LARGE_INT
#     tile_stone = Tile(cost=999, q=2, r=0, type=HexType.STONE)
#     tile_acid = Tile(cost=1, q=2, r=1, type=HexType.ACID)
#     assert OnDemandCostDict.tile_cost(tile_empty) == 1
#     assert OnDemandCostDict.tile_cost(tile_anthill) == 1
#     assert OnDemandCostDict.tile_cost(tile_dirt) == 2
#     assert OnDemandCostDict.tile_cost(tile_stone) == VERY_LARGE_INT
#     assert OnDemandCostDict.tile_cost(tile_acid) == VERY_LARGE_INT


# def test_cost_dict_update_simple():
#     # Two adjacent tiles: EMPTY (0,0), DIRT (1,0)
#     tile1 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile2 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
#     seen_tiles = {Hex(0, 0): tile1, Hex(1, 0): tile2}
#     cost_dict = OnDemandCostDict(seen_tiles)
#     # Cost from (0,0) to (1,0) should be 2
#     key = (Hex(0, 0), Hex(1, 0))
#     assert key in cost_dict
#     assert cost_dict[key].cost == 2
#     assert cost_dict[key].path == [Hex(0, 0), Hex(1, 0)]
#     # Cost from (1,0) to (0,0) should be 1
#     key_rev = (Hex(1, 0), Hex(0, 0))
#     assert key_rev in cost_dict
#     assert cost_dict[key_rev].cost == 1
#     assert cost_dict[key_rev].path == [Hex(1, 0), Hex(0, 0)]


# def test_cost_dict_update_impassible():
#     # EMPTY (0,0), STONE (1,0)
#     tile1 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile2 = Tile(cost=999, q=1, r=0, type=HexType.STONE)
#     seen_tiles = {Hex(0, 0): tile1, Hex(1, 0): tile2}
#     cost_dict = OnDemandCostDict(seen_tiles)
#     key = (Hex(0, 0), Hex(1, 0))
#     assert key not in cost_dict or cost_dict[key].cost >= VERY_LARGE_INT


def test_seen_tiles_update():
    tile1 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile2 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    seen = SeenTiles()
    # First update, both are new
    _ = seen.update([tile1, tile2])
    assert seen[Hex(0, 0)] == tile1
    assert seen[Hex(1, 0)] == tile2
    # Second update, both are now seen, so returned as new_tiles
    new_tiles2 = seen.update([tile1, tile2])
    assert len(new_tiles2) == 0


# def test_multiple_updates_in_a_row():
#     # Start with two tiles, then add a third, then a fourth
#     tile1 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile2 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
#     tile3 = Tile(cost=1, q=2, r=0, type=HexType.EMPTY)
#     tile4 = Tile(cost=999, q=3, r=0, type=HexType.STONE)
#     seen_tiles = SeenTiles()
#     cost_dict = OnDemandCostDict(seen_tiles)

#     # First update: add tile1 and tile2
#     new_tiles = seen_tiles.update([tile1, tile2])
#     assert len(new_tiles) == 2
#     assert (Hex(0, 0), Hex(1, 0)) in cost_dict
#     assert cost_dict[(Hex(0, 0), Hex(1, 0))].cost == 2

#     # Second update: add tile3
#     new_tiles = seen_tiles.update([tile1, tile2, tile3])
#     assert new_tiles == [tile3]
#     assert seen_tiles[Hex(2, 0)] == tile3
#     # Now (0,0) -> (2,0) should be possible via (1,0)
#     assert (Hex(0, 0), Hex(2, 0)) in cost_dict
#     assert (
#         cost_dict[(Hex(0, 0), Hex(2, 0))].cost == 3
#     )  # 1 (0,0)->(1,0) + 2 (1,0)->(2,0) + 1 (2,0)
#     # Path should be [Hex(0,0), Hex(1,0), Hex(2,0)]
#     assert cost_dict[(Hex(0, 0), Hex(2, 0))].path == [Hex(0, 0), Hex(1, 0), Hex(2, 0)]

#     # Third update: add tile4 (STONE, impassible)
#     new_tiles = seen_tiles.update([tile1, tile2, tile3, tile4])
#     # (0,0) -> (3,0) should not be possible (impassible)
#     key = (Hex(0, 0), Hex(3, 0))
#     assert key not in cost_dict or cost_dict[key].cost >= VERY_LARGE_INT

#     # SeenTiles should have all four tiles
#     assert Hex(0, 0) in seen_tiles
#     assert Hex(1, 0) in seen_tiles
#     assert Hex(2, 0) in seen_tiles
#     assert Hex(3, 0) in seen_tiles


# # --- Advanced and Edge Case Tests ---
# def test_cost_dict_disconnected_graph():
#     # Two separate regions: (0,0)-(1,0) and (10,10)-(11,10)
#     tile_a = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile_b = Tile(cost=1, q=1, r=0, type=HexType.EMPTY)
#     tile_c = Tile(cost=1, q=10, r=10, type=HexType.EMPTY)
#     tile_d = Tile(cost=1, q=11, r=10, type=HexType.EMPTY)
#     seen_tiles = {
#         Hex(0, 0): tile_a,
#         Hex(1, 0): tile_b,
#         Hex(10, 10): tile_c,
#         Hex(11, 10): tile_d,
#     }
#     cost_dict = OnDemandCostDict(seen_tiles)
#     # No path between (0,0) and (10,10)
#     assert (Hex(0, 0), Hex(10, 10)) not in cost_dict or cost_dict[
#         (Hex(0, 0), Hex(10, 10))
#     ].cost >= VERY_LARGE_INT
#     # Path within each region should exist
#     assert (Hex(0, 0), Hex(1, 0)) in cost_dict
#     assert (Hex(10, 10), Hex(11, 10)) in cost_dict


# def test_cost_dict_cycle():
#     # Create a cycle: (0,0)-(1,0)-(1,1)-(0,1)-(0,0)
#     tiles = [
#         Tile(cost=1, q=0, r=0, type=HexType.EMPTY),
#         Tile(cost=1, q=1, r=0, type=HexType.EMPTY),
#         Tile(cost=1, q=1, r=1, type=HexType.EMPTY),
#         Tile(cost=1, q=0, r=1, type=HexType.EMPTY),
#     ]
#     seen_tiles = {Hex(t.q, t.r): t for t in tiles}
#     cost_dict = OnDemandCostDict(seen_tiles)
#     # Shortest path from (0,0) to (1,1) should be length 2
#     assert (Hex(0, 0), Hex(1, 1)) in cost_dict
#     assert cost_dict[(Hex(0, 0), Hex(1, 1))].cost == 2
#     # Path should not loop infinitely
#     assert len(cost_dict[(Hex(0, 0), Hex(1, 1))].path) <= 3


# def test_cost_dict_all_impassible():
#     # All tiles are STONE except start
#     tile_start = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile_stone1 = Tile(cost=999, q=1, r=0, type=HexType.STONE)
#     tile_stone2 = Tile(cost=999, q=0, r=1, type=HexType.STONE)
#     seen_tiles = {Hex(0, 0): tile_start, Hex(1, 0): tile_stone1, Hex(0, 1): tile_stone2}
#     cost_dict = OnDemandCostDict(seen_tiles)
#     # Only self-path should exist
#     assert (Hex(0, 0), Hex(0, 0)) in cost_dict
#     assert (Hex(0, 0), Hex(1, 0)) not in cost_dict or cost_dict[
#         (Hex(0, 0), Hex(1, 0))
#     ].cost >= VERY_LARGE_INT
#     assert (Hex(0, 0), Hex(0, 1)) not in cost_dict or cost_dict[
#         (Hex(0, 0), Hex(0, 1))
#     ].cost >= VERY_LARGE_INT


# def test_cost_dict_large_mixed_map():
#     # 3x3 grid, center is STONE, rest are EMPTY or DIRT
#     tiles = []
#     for q in range(3):
#         for r in range(3):
#             if q == 1 and r == 1:
#                 t = Tile(cost=999, q=q, r=r, type=HexType.STONE)
#             elif (q + r) % 2 == 0:
#                 t = Tile(cost=1, q=q, r=r, type=HexType.EMPTY)
#             else:
#                 t = Tile(cost=2, q=q, r=r, type=HexType.DIRT)
#             tiles.append(t)
#     seen_tiles = {Hex(t.q, t.r): t for t in tiles}
#     cost_dict = OnDemandCostDict(seen_tiles)
#     # Path from (0,0) to (2,2) must go around the center
#     key = (Hex(0, 0), Hex(2, 2))
#     assert key in cost_dict
#     # Path should not go through (1,1)
#     path = cost_dict[key].path
#     assert Hex(1, 1) not in path
#     # Cost should be > 4 (since must detour)
#     assert cost_dict[key].cost > 4


def test_seen_tiles_update_overlap_and_new():
    # Initial map
    tile1 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile2 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    seen = SeenTiles()
    seen.update([tile1, tile2])
    # Update with one old, one new
    tile3 = Tile(cost=1, q=2, r=0, type=HexType.EMPTY)
    new_tiles = seen.update([tile2, tile3])
    assert new_tiles == [tile3]
    # SeenTiles should have all three
    assert Hex(2, 0) in seen


# def test_cost_dict_path_around_obstacle():
#     # (0,0) -> (2,0) with (1,0) as STONE, must go around
#     tile_start = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
#     tile_obstacle = Tile(cost=999, q=1, r=0, type=HexType.STONE)
#     tile_side1 = Tile(cost=1, q=0, r=1, type=HexType.EMPTY)
#     tile_side2 = Tile(cost=1, q=1, r=1, type=HexType.EMPTY)
#     tile_end = Tile(cost=1, q=2, r=0, type=HexType.EMPTY)
#     seen_tiles = SeenTiles()
#     seen_tiles.update([tile_start, tile_obstacle, tile_side1, tile_side2, tile_end])
#     cost_dict = OnDemandCostDict(seen_tiles)
#     key = (Hex(0, 0), Hex(2, 0))
#     assert key in cost_dict
#     # Path should not go through (1,0)
#     path = cost_dict[key].path
#     assert Hex(1, 0) not in path
#     # Path should be around the obstacle
#     assert path[0] == Hex(0, 0)
#     assert path[1] == Hex(0, 1)
#     assert path[2] == Hex(1, 1)
#     assert path[3] == Hex(2, 0)


def test_path_truncator_truncate():
    # Setup tiles: (0,0) EMPTY, (1,0) DIRT, (2,0) EMPTY
    tile0 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile1 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    tile2 = Tile(cost=1, q=2, r=0, type=HexType.EMPTY)
    seen_tiles = SeenTiles()
    seen_tiles.update([tile0, tile1, tile2])
    truncator = PathTruncator(seen_tiles, set())
    # Ant: WORKER (speed=5)
    ant = Ant(
        food=Food(amount=0, type=0),
        health=100,
        id="ant1",
        lastAttack=None,
        lastEnemyAnt=None,
        q=0,
        r=0,
        type=UnitType.WORKER,
    )
    # Path: [(0,0), (1,0), (2,0)]
    path = [Hex(0, 0), Hex(1, 0), Hex(2, 0)]
    # Total cost: (0,0)->(1,0):2, (1,0)->(2,0):1, total=3 (for truncated), 3<=5
    truncated = truncator.truncate(ant, path)
    # Should be able to move to both (1,0) and (2,0) since total cost=3<=speed
    assert truncated == [Hex(1, 0), Hex(2, 0)]
    # Now test with a slower ant (FIGHTER, speed=4)
    ant_slow = Ant(
        food=Food(amount=0, type=0),
        health=100,
        id="ant2",
        lastAttack=None,
        lastEnemyAnt=None,
        q=0,
        r=0,
        type=UnitType.FIGHTER,
    )
    truncated_slow = truncator.truncate(ant_slow, path)
    # (0,0)->(1,0):2, (1,0)->(2,0):1, total=3<=4, so should also reach (2,0)
    assert truncated_slow == [Hex(1, 0), Hex(2, 0)]
    # Now test with a path that exceeds speed
    path_long = [Hex(0, 0), Hex(1, 0), Hex(2, 0), Hex(3, 0)]
    # Add (3,0) as DIRT (cost=2)
    tile3 = Tile(cost=2, q=3, r=0, type=HexType.DIRT)
    seen_tiles.update([tile3])
    truncated_long = truncator.truncate(ant_slow, path_long)
    # (0,0)->(1,0):2, (1,0)->(2,0):1, (2,0)->(3,0):2, total=5>4, so should stop before (3,0)
    assert truncated_long == [Hex(1, 0), Hex(2, 0)]
