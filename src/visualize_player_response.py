import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from pathlib import Path
import sys

# Add src to sys.path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))
from game_types import PlayerResponse, Hex, Ant, FoodOnMap, Tile
from game_types import (
    UnitType,
    UNIT_TYPE_NAMES,
    FoodType,
    FOOD_TYPE_NAMES,
    HexType,
    HEX_TYPE_NAMES,
)

# Color palettes for types
HEX_TYPE_COLORS = {
    HexType.ANTHILL: "#ffcc80",  # Orange-ish for anthill
    HexType.EMPTY: "#eeeeee",  # Light gray for empty
    HexType.DIRT: "#bdb76b",  # Khaki for dirt
    HexType.ACID: "#b2dfdb",  # Teal for acid
    HexType.STONE: "#888888",  # Gray for stone
}

ANT_TYPE_COLORS = {
    UnitType.WORKER: "#4caf50",  # Green
    UnitType.FIGHTER: "#f44336",  # Red
    UnitType.SCOUT: "#2196f3",  # Blue
}

FOOD_TYPE_COLORS = {
    FoodType.APPLE: "#ff7040",  # Orange
    FoodType.BREAD: "#c05020",  # Yellow
    FoodType.NECTAR: "#702000",  # Purple
}


def hex_to_pixel(q, r, size=1):
    """Convert hex coordinates (q, r) to pixel coordinates (x, y)."""
    x = size * (3 / 2 * q)
    y = size * (math.sqrt(3) * (r + q / 2))
    return x, y


def draw_hex(ax, q, r, size=1, **kwargs):
    """Draw a single hex at (q, r)."""
    x, y = hex_to_pixel(q, r, size)
    hexagon = patches.RegularPolygon(
        (x, y), numVertices=6, radius=size, orientation=math.radians(30), **kwargs
    )
    ax.add_patch(hexagon)
    return hexagon


def plot_player_response(
    resp: PlayerResponse, hex_size=1, ax=None, fig=None, seen_tiles=None
):
    if ax is None or fig is None:
        fig, ax = plt.subplots(figsize=(10, 10))
    else:
        ax.clear()
    # Compute current vision
    current_vision = {(tile.q, tile.r) for tile in resp.map}
    # Use seen_tiles if provided, else just current map
    tiles_to_draw = seen_tiles.values() if seen_tiles is not None else resp.map
    # Draw map tiles
    for tile in tiles_to_draw:
        hex_type = HexType(tile.type)
        color = HEX_TYPE_COLORS.get(hex_type, "#eeeeee")
        alpha = 0.7 if (tile.q, tile.r) in current_vision else 0.2
        draw_hex(
            ax,
            tile.q,
            tile.r,
            size=hex_size,
            facecolor=color,
            edgecolor="gray",
            alpha=alpha,
        )
        # Show hex type name
        if hex_type:
            x, y = hex_to_pixel(tile.q, tile.r, hex_size)
            # ax.text(
            #     x,
            #     y,
            #     HEX_TYPE_NAMES[hex_type],
            #     ha="center",
            #     va="center",
            #     fontsize=7,
            #     color="#444",
            #     alpha=alpha,
            # )
    # Draw food (only in current vision)
    for food in resp.food:
        if (food.q, food.r) not in current_vision:
            continue
        food_type = FoodType(food.type)
        x, y = hex_to_pixel(food.q, food.r, hex_size)
        color = FOOD_TYPE_COLORS.get(food_type, "brown")
        label = (
            f"{FOOD_TYPE_NAMES[food_type]}\n{food.amount}"
            if food_type
            else f"{food.type}\n{food.amount}"
        )
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            color=color,
            fontweight="bold",
        )
    # Draw ants (only in current vision)
    for ant in resp.ants:
        if (ant.q, ant.r) not in current_vision:
            continue
        ant_type = UnitType(ant.type)
        x, y = hex_to_pixel(ant.q, ant.r, hex_size)
        color = ANT_TYPE_COLORS.get(ant_type, "red")
        ax.plot(x, y, "o", color=color, markersize=hex_size * 15)
        if ant_type:
            ax.text(
                x,
                y,
                UNIT_TYPE_NAMES[ant_type],
                ha="center",
                va="center",
                fontsize=6,
                color="black",
                fontweight="bold",
            )
    # Draw enemies (only in current vision)
    for enemy in resp.enemies:
        if (enemy.q, enemy.r) not in current_vision:
            continue
        ant_type = UnitType(enemy.type)
        x, y = hex_to_pixel(enemy.q, enemy.r, hex_size)
        color = ANT_TYPE_COLORS.get(ant_type, "black")
        ax.plot(x, y, "X", color=color, markersize=hex_size * 15)
        if ant_type:
            ax.text(
                x,
                y,
                UNIT_TYPE_NAMES[ant_type],
                ha="center",
                va="center",
                fontsize=6,
                color="white",
                fontweight="bold",
            )
    # Draw home (only in current vision)
    for home in resp.home:
        if (home.q, home.r) not in current_vision:
            continue
        x, y = hex_to_pixel(home.q, home.r, hex_size)
        ax.plot(x, y, "s", color="orange", markersize=hex_size * 10)
    # Draw spot (always)
    x, y = hex_to_pixel(resp.spot.q, resp.spot.r, hex_size)
    ax.plot(x, y, "*", color="gold", markersize=hex_size * 20)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Turn {resp.turnNo} | Score: {resp.score}")
    return fig, ax


def load_player_response_from_json(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    # Convert dicts to dataclasses recursively
    def from_dict(cls, d):
        if hasattr(cls, "__origin__") and cls.__origin__ is list:
            return [from_dict(cls.__args__[0], x) for x in d]
        if hasattr(cls, "__dataclass_fields__"):
            kwargs = {}
            for k, v in d.items():
                field_type = cls.__dataclass_fields__[k].type
                kwargs[k] = from_dict(field_type, v)
            return cls(**kwargs)
        return d

    return from_dict(PlayerResponse, data)
