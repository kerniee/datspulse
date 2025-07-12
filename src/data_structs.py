from game_types import Hex, Tile

VERY_LARGE_INT = 999999999


class SeenTiles(dict[Hex, Tile]):
    def __init__(self):
        super().__init__()

    """
    Update the seen tiles with new tiles.
    Returns the new tiles.
    """

    def update(self, map: list[Tile]) -> list[Tile]:
        new_tiles: list[Tile] = []
        for tile in map:
            tile_hex = Hex(tile.q, tile.r)
            if tile_hex not in self:
                new_tiles.append(tile)
            self[tile_hex] = tile
        return new_tiles
