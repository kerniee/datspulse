from data_structs import SeenTiles
from hex import Hex, neighbors, distance
from ai import AI
from game_types import Tile, Hex, HexType


def test_neighbors():
    assert set(neighbors(Hex(3, 3))) == {
        Hex(3, 2),
        Hex(4, 2),
        Hex(2, 3),
        Hex(4, 3),
        Hex(3, 4),
        Hex(4, 4),
    }

    assert set(neighbors(Hex(5, 1))) == {
        Hex(5, 0),
        Hex(6, 0),
        Hex(4, 1),
        Hex(6, 1),
        Hex(5, 2),
        Hex(6, 2),
    }

    assert set(neighbors(Hex(2, 2))) == {
        Hex(1, 1),
        Hex(2, 1),
        Hex(1, 2),
        Hex(3, 2),
        Hex(1, 3),
        Hex(2, 3),
    }


def test_distance():
    assert distance(Hex(3, 3), Hex(3, 3)) == 0
    for hex in neighbors(Hex(3, 3)):
        assert distance(Hex(3, 3), hex) == 1
    assert distance(Hex(0, 0), Hex(5, 2)) == 6
    assert distance(Hex(1, 2), Hex(5, 5)) == 6
    assert distance(Hex(0, 6), Hex(6, 0)) == 9


def test_update_cost_dict_simple():
    # Create two adjacent tiles: EMPTY and DIRT
    tile1 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile2 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    ai = AI()
    ai.seen_tiles.update([tile1, tile2])
    # Cost from (0,0) to (1,0) should be 2 (EMPTY->DIRT)
    key = (Hex(0, 0), Hex(1, 0))
    assert key in ai.cost_dict
    assert ai.cost_dict[key].cost == 2
    assert ai.cost_dict[key].path == [Hex(0, 0), Hex(1, 0)]
    # Cost from (1,0) to (0,0) should be 1 (DIRT->EMPTY)
    key_rev = (Hex(1, 0), Hex(0, 0))
    assert key_rev in ai.cost_dict
    assert ai.cost_dict[key_rev].cost == 1
    assert ai.cost_dict[key_rev].path == [Hex(1, 0), Hex(0, 0)]


def test_update_cost_dict_complex():
    # Create a row: EMPTY (0,0), DIRT (1,0), STONE (2,0)
    tile_empty = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile_dirt = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    tile_stone = Tile(cost=999, q=2, r=0, type=HexType.STONE)
    ai = AI()
    ai.seen_tiles.update([tile_empty, tile_dirt, tile_stone])
    # EMPTY -> DIRT
    key_ed = (Hex(0, 0), Hex(1, 0))
    assert key_ed in ai.cost_dict
    assert ai.cost_dict[key_ed].cost == 2
    assert ai.cost_dict[key_ed].path == [Hex(0, 0), Hex(1, 0)]
    # DIRT -> EMPTY
    key_de = (Hex(1, 0), Hex(0, 0))
    assert key_de in ai.cost_dict
    assert ai.cost_dict[key_de].cost == 1
    assert ai.cost_dict[key_de].path == [Hex(1, 0), Hex(0, 0)]
    # EMPTY -> STONE (should be unreachable)
    key_es = (Hex(0, 0), Hex(2, 0))
    assert key_es not in ai.cost_dict or ai.cost_dict[key_es].cost >= 999999999
    # DIRT -> STONE (should be unreachable)
    key_ds = (Hex(1, 0), Hex(2, 0))
    assert key_ds not in ai.cost_dict or ai.cost_dict[key_ds].cost >= 999999999


def test_update_cost_dict_obstacle():
    # (0,0) EMPTY   (1,0) DIRT
    # (0,1) STONE   (1,1) EMPTY
    tile_00 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile_10 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    tile_01 = Tile(cost=999, q=0, r=1, type=HexType.STONE)
    tile_11 = Tile(cost=1, q=1, r=1, type=HexType.EMPTY)
    ai = AI()
    ai.seen_tiles.update([tile_00, tile_10, tile_01, tile_11])
    # (0,0) to (1,0): direct neighbor, cost 2
    key_00_10 = (Hex(0, 0), Hex(1, 0))
    assert key_00_10 in ai.cost_dict
    assert ai.cost_dict[key_00_10].cost == 2
    assert ai.cost_dict[key_00_10].path == [Hex(0, 0), Hex(1, 0)]
    # (0,0) to (1,1): path is (0,0)->(1,0)->(1,1), cost 1+2=3
    key_00_11 = (Hex(0, 0), Hex(1, 1))
    assert key_00_11 in ai.cost_dict
    assert ai.cost_dict[key_00_11].cost == 3
    assert ai.cost_dict[key_00_11].path == [Hex(0, 0), Hex(1, 0), Hex(1, 1)]
    # (1,1) to (0,0): path is (1,1)->(1,0)->(0,0), cost 2+1=3
    key_11_00 = (Hex(1, 1), Hex(0, 0))
    assert key_11_00 in ai.cost_dict
    assert ai.cost_dict[key_11_00].cost == 3
    assert ai.cost_dict[key_11_00].path == [Hex(1, 1), Hex(1, 0), Hex(0, 0)]
    # (1,0) to (1,1): direct neighbor, cost 1
    key_10_11 = (Hex(1, 0), Hex(1, 1))
    assert key_10_11 in ai.cost_dict
    assert ai.cost_dict[key_10_11].cost == 1
    assert ai.cost_dict[key_10_11].path == [Hex(1, 0), Hex(1, 1)]
    # (1,1) to (1,0): direct neighbor, cost 2
    key_11_10 = (Hex(1, 1), Hex(1, 0))
    assert key_11_10 in ai.cost_dict
    assert ai.cost_dict[key_11_10].cost == 2
    assert ai.cost_dict[key_11_10].path == [Hex(1, 1), Hex(1, 0)]
    # (0,1) is STONE, so no path to (0,1) from any other tile
    for h in [Hex(0, 0), Hex(1, 0), Hex(1, 1)]:
        assert (h, Hex(0, 1)) not in ai.cost_dict or ai.cost_dict[
            (h, Hex(0, 1))
        ].cost >= 999999999


def test_update_cost_dict_2_way_path():
    # (0,0) EMPTY   (1,0) DIRT
    # (0,1) EMPTY   (1,1) EMPTY
    tile_00 = Tile(cost=1, q=0, r=0, type=HexType.EMPTY)
    tile_10 = Tile(cost=2, q=1, r=0, type=HexType.DIRT)
    tile_01 = Tile(cost=1, q=0, r=1, type=HexType.EMPTY)
    tile_11 = Tile(cost=1, q=1, r=1, type=HexType.EMPTY)
    ai = AI()
    ai.seen_tiles.update([tile_00, tile_10, tile_01, tile_11])
    # (0,0) to (1,0): direct neighbor, cost 2
    key_00_10 = (Hex(0, 0), Hex(1, 0))
    assert key_00_10 in ai.cost_dict
    assert ai.cost_dict[key_00_10].cost == 2
    assert ai.cost_dict[key_00_10].path == [Hex(0, 0), Hex(1, 0)]
    # (0,0) to (1,1): path is (0,0)->(0,1)->(1,1), cost 1+1=2
    key_00_11 = (Hex(0, 0), Hex(1, 1))
    assert key_00_11 in ai.cost_dict
    assert ai.cost_dict[key_00_11].cost == 2
    assert ai.cost_dict[key_00_11].path == [Hex(0, 0), Hex(0, 1), Hex(1, 1)]
    # (1,1) to (0,0): path is (1,1)->(1,0)->(0,0), cost 1+1=2
    key_11_00 = (Hex(1, 1), Hex(0, 0))
    assert key_11_00 in ai.cost_dict
    assert ai.cost_dict[key_11_00].cost == 2
    assert ai.cost_dict[key_11_00].path == [Hex(1, 1), Hex(0, 1), Hex(0, 0)]
    # (1,0) to (1,1): direct neighbor, cost 1
    key_10_11 = (Hex(1, 0), Hex(1, 1))
    assert key_10_11 in ai.cost_dict
    assert ai.cost_dict[key_10_11].cost == 1
    assert ai.cost_dict[key_10_11].path == [Hex(1, 0), Hex(1, 1)]
    # (1,1) to (1,0): direct neighbor, cost 2
    key_11_10 = (Hex(1, 1), Hex(1, 0))
    assert key_11_10 in ai.cost_dict
    assert ai.cost_dict[key_11_10].cost == 2
    assert ai.cost_dict[key_11_10].path == [Hex(1, 1), Hex(1, 0)]
    # (0,1) to (1,1): direct neighbor, cost 1
    key_01_11 = (Hex(0, 1), Hex(1, 1))
    assert key_01_11 in ai.cost_dict
    assert ai.cost_dict[key_01_11].cost == 1
    assert ai.cost_dict[key_01_11].path == [Hex(0, 1), Hex(1, 1)]
