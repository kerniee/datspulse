# odd-r layout

from functools import lru_cache

from game_types import Hex


def oddr_to_cube(hex: Hex):
    x = hex.q - (hex.r - (hex.r & 1)) // 2
    z = hex.r
    y = -x - z
    return (x, y, z)


@lru_cache(maxsize=10000)
def distance(a: Hex, b: Hex) -> int:
    ax, ay, az = oddr_to_cube(a)
    bx, by, bz = oddr_to_cube(b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))


# def neighbors(hex: Hex):
#     # Odd-r horizontal layout
#     # See https://www.redblobgames.com/grids/hexagons/#neighbors-offset
#     if hex.r % 2 == 0:  # even row
#         directions = [(+1, 0), (0, -1), (-1, -1), (-1, 0), (-1, +1), (0, +1)]
#     else:  # odd row
#         directions = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (0, +1), (+1, +1)]
#     for dq, dr in directions:
#         yield Hex(hex.q + dq, hex.r + dr)

# // even rows
# [[+1,  0], [ 0, -1], [-1, -1],
#  [-1,  0], [-1, +1], [ 0, +1]],
# // odd rows
# [[+1,  0], [+1, -1], [ 0, -1],
#  [-1,  0], [ 0, +1], [+1, +1]],


# Define neighbor offsets for Odd-r layout
even_r_neighbors = ((+1, 0), (0, -1), (-1, -1), (-1, 0), (-1, +1), (0, +1))

odd_r_neighbors = ((+1, 0), (+1, -1), (0, -1), (-1, 0), (0, +1), (+1, +1))


@lru_cache(maxsize=10000)
def neighbors(hex: Hex) -> tuple[Hex]:
    neighbors = []
    if hex.r % 2 == 0:
        deltas = even_r_neighbors
    else:
        deltas = odd_r_neighbors
    for dq, dr in deltas:
        neighbor_q = hex.q + dq
        neighbor_r = hex.r + dr
        neighbors.append(Hex(neighbor_q, neighbor_r))
    return tuple(neighbors)


def diff_q_r(a: Hex, b: Hex) -> tuple[int, int]:
    return abs(a.q - b.q), abs(a.r - b.r)


def hex_ring(center: Hex, radius: int) -> list[Hex]:
    """
    Returns a list of Hexes forming a ring at the given radius around center.
    Uses cube coordinates for hex math.
    """
    if radius == 0:
        return [center]

    # Convert to cube coordinates
    def oddr_to_cube(hex: Hex):
        x = hex.q - (hex.r - (hex.r & 1)) // 2
        z = hex.r
        y = -x - z
        return (x, y, z)

    def cube_to_oddr(x, y, z):
        r = z
        q = x + (z - (z & 1)) // 2
        return Hex(q, r)

    # Cube directions (pointy-topped, but works for flat-topped with correct deltas)
    directions = [
        (1, -1, 0),
        (1, 0, -1),
        (0, 1, -1),
        (-1, 1, 0),
        (-1, 0, 1),
        (0, -1, 1),
    ]
    results = []
    cx, cy, cz = oddr_to_cube(center)
    # Start at (cx + radius * dir0)
    x, y, z = (
        cx + directions[4][0] * radius,
        cy + directions[4][1] * radius,
        cz + directions[4][2] * radius,
    )
    for i in range(6):
        for _ in range(radius):
            results.append(cube_to_oddr(x, y, z))
            dx, dy, dz = directions[i]
            x, y, z = x + dx, y + dy, z + dz
    return results
