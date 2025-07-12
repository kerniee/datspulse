import math

import pygame

from game_types import (
    FOOD_TYPE_NAMES,
    UNIT_TYPE_NAMES,
    FoodType,
    Hex,
    HexType,
    PlayerMoveCommands,
    PlayerResponse,
    Tile,
    UnitType,
)

# Color palettes for types
HEX_TYPE_COLORS = {
    HexType.ANTHILL: "#ffcc80",  # Orange-ish for anthill
    HexType.EMPTY: "#eeeeee",  # Light gray for empty
    HexType.DIRT: "#bdb76b",  # Khaki for dirt
    HexType.ACID: "#62df6b",  # Teal for acid
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


class Visualizer:
    def __init__(self, hex_size=30, width=1600, height=900):
        pygame.init()
        self.width = width
        self.height = height
        self.hex_size = hex_size
        self.surface = pygame.display.set_mode((self.width, self.height))
        self.font = pygame.font.SysFont(None, 14)
        self.title_font = pygame.font.SysFont(None, 20)
        self.running = True
        self.camera_offset = [0, 0]  # [x, y] offset in pixels
        self._dragging = False
        self._drag_start = None
        self._camera_start = None
        self._min_hex_size = 10
        self._max_hex_size = 120

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.camera_offset[0] += 40
                elif event.key == pygame.K_RIGHT:
                    self.camera_offset[0] -= 40
                elif event.key == pygame.K_UP:
                    self.camera_offset[1] += 40
                elif event.key == pygame.K_DOWN:
                    self.camera_offset[1] -= 40
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._dragging = True
                    self._drag_start = pygame.mouse.get_pos()
                    self._camera_start = self.camera_offset[:]
                elif event.button == 4 or event.button == 5:
                    # Mouse wheel scroll: 4 = up, 5 = down
                    mx, my = pygame.mouse.get_pos()
                    old_hex_size = self.hex_size
                    if event.button == 4:
                        self.hex_size = min(self.hex_size + 5, self._max_hex_size)
                    elif event.button == 5:
                        self.hex_size = max(self.hex_size - 5, self._min_hex_size)
                    # Adjust camera offset to zoom on mouse position
                    if self.hex_size != old_hex_size:
                        scale = self.hex_size / old_hex_size
                        self.camera_offset[0] = int(
                            (self.camera_offset[0] - mx) * scale + mx
                        )
                        self.camera_offset[1] = int(
                            (self.camera_offset[1] - my) * scale + my
                        )
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._dragging = False
                    self._drag_start = None
                    self._camera_start = None
            elif event.type == pygame.MOUSEMOTION:
                if (
                    self._dragging
                    and self._drag_start is not None
                    and self._camera_start is not None
                ):
                    mx, my = pygame.mouse.get_pos()
                    dx = mx - self._drag_start[0]
                    dy = my - self._drag_start[1]
                    self.camera_offset[0] = self._camera_start[0] + dx
                    self.camera_offset[1] = self._camera_start[1] + dy

    def update(
        self,
        resp: PlayerResponse,
        seen_tiles: dict[Hex, Tile],
        move_commands: PlayerMoveCommands,
        remembered_enemies=None,  # New argument: list of Hex or PlayerEnemy
        remembered_food=None,  # New argument: list of FoodOnMap or Hex
    ):
        self.handle_events()
        if not self.running:
            return False
        self.surface.fill((255, 255, 255))
        hex_size = self.hex_size
        surface = self.surface
        font = self.font
        title_font = self.title_font

        # Compute map center for centering (use min/max for better fit)
        map_tiles = resp.map if seen_tiles is None else list(seen_tiles.values())
        if map_tiles:
            min_q = min(tile.q for tile in map_tiles)
            max_q = max(tile.q for tile in map_tiles)
            min_r = min(tile.r for tile in map_tiles)
            max_r = max(tile.r for tile in map_tiles)
            center_q = (min_q + max_q) / 2
            center_r = (min_r + max_r) / 2
        else:
            center_q = 0
            center_r = 0

        # Flat-topped, odd-r horizontal layout
        def hex_to_pixel(q, r, size=1):
            w = math.sqrt(3) * size
            h = 2 * size
            x = w * (q + 0.5 * (r % 2))
            y = 0.75 * h * r
            # Centering
            cx = w * (center_q + 0.5 * (center_r % 2))
            cy = 0.75 * h * center_r
            x = x - cx + self.width // 2 + self.camera_offset[0]
            y = y - cy + self.height // 2 + self.camera_offset[1]
            return x, y

        # --- Hover detection for ants ---
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hovered_ant = None
        ant_screen_positions = {}
        for ant in resp.ants:
            x, y = hex_to_pixel(ant.q, ant.r, hex_size)
            x += self.width // 2
            y += self.height // 2
            ant_screen_positions[ant.id] = (x, y)
            dist = math.hypot(mouse_x - x, mouse_y - y)
            if dist <= hex_size * 0.6:
                hovered_ant = ant
        # --- End hover detection ---

        def draw_hex(
            surface, q, r, size, color, alpha=255, border_color=(128, 128, 128)
        ):
            x, y = hex_to_pixel(q, r, size)
            x += self.width // 2
            y += self.height // 2
            points = []
            for i in range(6):
                angle = math.pi / 3 * i + math.radians(30)
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((int(px), int(py)))
            s = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.polygon(
                s,
                color + (alpha,),
                [(p[0] - x + size, p[1] - y + size) for p in points],
            )
            surface.blit(s, (x - size, y - size))
            pygame.draw.polygon(surface, border_color, points, 1)

        # Compute current vision
        current_vision = {(tile.q, tile.r) for tile in resp.map}
        tiles_to_draw = seen_tiles.values() if seen_tiles is not None else resp.map
        # Draw map tiles
        for tile in tiles_to_draw:
            hex_type = HexType(tile.type)
            color_hex = HEX_TYPE_COLORS.get(hex_type, "#eeeeee")
            color = tuple(int(color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            in_vision = (tile.q, tile.r) in current_vision
            alpha = 200 if in_vision else 40  # Make fog tiles very faint
            draw_hex(surface, tile.q, tile.r, hex_size, color, alpha=alpha)
            # Overlay a dark fog if not in vision
            if not in_vision:
                fog_color = (0, 0, 0)
                fog_alpha = 140  # Stronger fog overlay
                draw_hex(
                    surface,
                    tile.q,
                    tile.r,
                    hex_size,
                    fog_color,
                    alpha=fog_alpha,
                    border_color=(80, 80, 80),
                )
            # Draw hex coordinates at the center
            x, y = hex_to_pixel(tile.q, tile.r, hex_size)
            x += self.width // 2
            y += self.height // 2
            # coord_text = font.render(f"({tile.q},{tile.r})", True, (0, 0, 0, 50))
            # text_rect = coord_text.get_rect(center=(int(x), int(y)))
            # surface.blit(coord_text, text_rect)
        # Draw home (only in current vision)
        for home in resp.home:
            if (home.q, home.r) not in current_vision:
                continue
            x, y = hex_to_pixel(home.q, home.r, hex_size)
            x += self.width // 2
            y += self.height // 2
            pygame.draw.polygon(
                surface,
                (255, 165, 0),
                [
                    (
                        int(
                            x + hex_size * math.cos(math.pi / 3 * i + math.radians(30))
                        ),
                        int(
                            y + hex_size * math.sin(math.pi / 3 * i + math.radians(30))
                        ),
                    )
                    for i in range(6)
                ],
            )
            # Draw spot (always)
        x, y = hex_to_pixel(resp.spot.q, resp.spot.r, hex_size)
        x += self.width // 2
        y += self.height // 2
        pygame.draw.circle(
            surface, (255, 215, 0), (int(x), int(y)), int(hex_size * 0.8)
        )
        # Draw food (only in current vision)
        for food in resp.food:
            if (food.q, food.r) not in current_vision:
                continue
            food_type = FoodType(food.type)
            x, y = hex_to_pixel(food.q, food.r, hex_size)
            x += self.width // 2
            y += self.height // 2
            color_hex = FOOD_TYPE_COLORS.get(food_type, "#8B4513")
            color = tuple(int(color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            label = (
                f"{FOOD_TYPE_NAMES[food_type]}\n{food.amount}"
                if food_type
                else f"{food.type}\n{food.amount}"
            )
            for idx, line in enumerate(label.split("\n")):
                text = font.render(line, True, color)
                surface.blit(text, (x - hex_size // 2, y - hex_size // 2 + idx * 15))
        # Draw ants (only in current vision)
        for ant in resp.ants:
            if (ant.q, ant.r) not in current_vision:
                continue
            ant_type = UnitType(ant.type)
            x, y = ant_screen_positions[ant.id]
            color_hex = ANT_TYPE_COLORS.get(ant_type, "#ff0000")
            color = tuple(int(color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            pygame.draw.circle(surface, color, (int(x), int(y)), int(hex_size * 0.6))
            if ant_type:
                text = font.render(UNIT_TYPE_NAMES[ant_type], True, (0, 0, 0))
                surface.blit(text, (x - hex_size // 2, y - hex_size // 2))
            # Draw a colored dot if ant is carrying food
            if hasattr(ant, "food") and getattr(ant.food, "amount", 0) > 0:
                food_type = getattr(ant.food, "type", None)
                if food_type is not None:
                    try:
                        food_type_enum = FoodType(food_type)
                        food_color_hex = FOOD_TYPE_COLORS.get(food_type_enum, "#8B4513")
                    except Exception:
                        food_color_hex = "#8B4513"
                else:
                    food_color_hex = "#8B4513"
                food_color = tuple(
                    int(food_color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
                )
                # Draw small dot at bottom right of ant
                dot_radius = max(4, int(hex_size * 0.18))
                pygame.draw.circle(
                    surface,
                    food_color,
                    (int(x + hex_size * 0.32), int(y + hex_size * 0.32)),
                    dot_radius,
                )
            # Draw a border if hovered
            if hovered_ant is not None and ant.id == hovered_ant.id:
                pygame.draw.circle(
                    surface, (255, 255, 0), (int(x), int(y)), int(hex_size * 0.6), 3
                )
        # Draw enemies (only in current vision)
        for enemy in resp.enemies:
            if (enemy.q, enemy.r) not in current_vision:
                continue
            ant_type = UnitType(enemy.type)
            x, y = hex_to_pixel(enemy.q, enemy.r, hex_size)
            x += self.width // 2
            y += self.height // 2
            color_hex = ANT_TYPE_COLORS.get(ant_type, "#000000")
            color = tuple(int(color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            pygame.draw.rect(
                surface,
                color,
                (x - hex_size // 2, y - hex_size // 2, hex_size, hex_size),
            )
            if ant_type:
                text = font.render(UNIT_TYPE_NAMES[ant_type], True, (255, 255, 255))
                surface.blit(text, (x - hex_size // 2, y - hex_size // 2))

        # Draw remembered enemies (out of vision)
        if remembered_enemies is not None:
            for enemy in remembered_enemies:
                # Accept either Hex or PlayerEnemy
                if hasattr(enemy, "q") and hasattr(enemy, "r"):
                    q, r = enemy.q, enemy.r
                    ant_type = getattr(enemy, "type", None)
                else:
                    q, r = enemy.q, enemy.r
                    ant_type = None
                if (q, r) in current_vision:
                    continue  # Already drawn as visible enemy
                x, y = hex_to_pixel(q, r, hex_size)
                x += self.width // 2
                y += self.height // 2
                # Draw as outlined faded square
                color_hex = (
                    ANT_TYPE_COLORS.get(UnitType(ant_type), "#000000")
                    if ant_type is not None
                    else "#888888"
                )
                color = tuple(
                    int(color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
                )
                faded_color = tuple(int(c * 0.5) for c in color)
                rect = pygame.Rect(
                    x - hex_size // 2, y - hex_size // 2, hex_size, hex_size
                )
                pygame.draw.rect(surface, faded_color, rect, 2)  # outline only
                pygame.draw.rect(
                    surface, (128, 0, 128), rect, 1
                )  # purple border for memory
                if ant_type is not None:
                    text = font.render(
                        UNIT_TYPE_NAMES[UnitType(ant_type)], True, (128, 0, 128)
                    )
                    surface.blit(text, (x - hex_size // 2, y - hex_size // 2))

        # Draw remembered food (out of vision)
        if remembered_food is not None:
            for food in remembered_food:
                # Accept either FoodOnMap or Hex
                if hasattr(food, "q") and hasattr(food, "r"):
                    q, r = food.q, food.r
                    food_type = getattr(food, "type", None)
                    amount = getattr(food, "amount", None)
                else:
                    q, r = food.q, food.r
                    food_type = None
                    amount = None
                if (q, r) in current_vision:
                    continue  # Already drawn as visible food
                x, y = hex_to_pixel(q, r, hex_size)
                x += self.width // 2
                y += self.height // 2
                # Draw as outlined faded circle
                color_hex = (
                    FOOD_TYPE_COLORS.get(FoodType(food_type), "#8B4513")
                    if food_type is not None
                    else "#8B4513"
                )
                color = tuple(
                    int(color_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
                )
                faded_color = tuple(int(c * 0.5) for c in color)
                pygame.draw.circle(
                    surface, faded_color, (int(x), int(y)), int(hex_size * 0.7), 2
                )  # outline only
                pygame.draw.circle(
                    surface, (0, 128, 128), (int(x), int(y)), int(hex_size * 0.7), 1
                )  # teal border for memory
                # Draw label
                label = ""
                if food_type is not None:
                    label += FOOD_TYPE_NAMES.get(FoodType(food_type), str(food_type))
                if amount is not None:
                    label += f"\n{amount}"
                if label:
                    for idx, line in enumerate(label.split("\n")):
                        text = font.render(line, True, (0, 128, 128))
                        surface.blit(
                            text, (x - hex_size // 2, y - hex_size // 2 + idx * 15)
                        )

        # Draw arrows for ant move commands if provided
        # Build a mapping from ant id to its current position
        ant_pos = {ant.id: (ant.q, ant.r) for ant in resp.ants}
        for move in move_commands.moves:
            if not hasattr(move, "path") or not move.path:
                continue
            # Get the ant's current position
            if move.ant not in ant_pos:
                continue  # Ant not found
            src_q, src_r = ant_pos[move.ant]
            dst = move.path[-1]
            if (src_q, src_r) == (dst.q, dst.r):
                continue  # No movement
            x1, y1 = hex_to_pixel(src_q, src_r, hex_size)
            x2, y2 = hex_to_pixel(dst.q, dst.r, hex_size)
            x1 += self.width // 2
            y1 += self.height // 2
            x2 += self.width // 2
            y2 += self.height // 2
            # Highlight if hovered
            if hovered_ant is not None and move.ant == hovered_ant.id:
                arrow_color = (255, 215, 0)  # bright yellow
                arrow_width = 5
            else:
                arrow_color = (0, 0, 255)
                arrow_width = 3
            # Draw main line
            pygame.draw.line(surface, arrow_color, (x1, y1), (x2, y2), arrow_width)
            # Draw arrowhead
            angle = math.atan2(y2 - y1, x2 - x1)
            arrow_length = 18
            arrow_angle = math.pi / 7
            for sign in [-1, 1]:
                dx = arrow_length * math.cos(angle + sign * arrow_angle)
                dy = arrow_length * math.sin(angle + sign * arrow_angle)
                pygame.draw.line(
                    surface, arrow_color, (x2, y2), (x2 - dx, y2 - dy), arrow_width
                )

        # Draw hovered ant's path as a special color polyline
        if hovered_ant is not None:
            # Find the move path for this ant
            for move in move_commands.moves:
                if move.ant == hovered_ant.id and hasattr(move, "path") and move.path:
                    path = move.path
                    if len(path) > 1:
                        points = []
                        for hex in path:
                            x, y = hex_to_pixel(hex.q, hex.r, hex_size)
                            x += self.width // 2
                            y += self.height // 2
                            points.append((int(x), int(y)))
                        pygame.draw.lines(
                            surface, (255, 0, 255), False, points, 6
                        )  # magenta, thick
                    break

        # Draw tooltip for hovered ant
        if hovered_ant is not None:
            lines = []
            ant_type = UnitType(hovered_ant.type)
            lines.append(f"ID: {hovered_ant.id[:8]}")
            lines.append(f"Type: {UNIT_TYPE_NAMES[ant_type]}")
            lines.append(f"Pos: ({hovered_ant.q},{hovered_ant.r})")
            # Show food carried if any
            if (
                hasattr(hovered_ant, "food")
                and getattr(hovered_ant.food, "amount", 0) > 0
            ):
                food_type = getattr(hovered_ant.food, "type", None)
                food_amount = getattr(hovered_ant.food, "amount", 0)
                if food_type is not None:
                    try:
                        food_type_enum = FoodType(food_type)
                        food_name = FOOD_TYPE_NAMES.get(food_type_enum, str(food_type))
                    except Exception:
                        food_name = str(food_type)
                else:
                    food_name = "?"
                lines.append(f"Food: {food_name} x{food_amount}")
            # Find destination
            dest = None
            for move in move_commands.moves:
                if move.ant == hovered_ant.id and hasattr(move, "path") and move.path:
                    dest = move.path[-1]
                    break
            if dest:
                lines.append(f"Dest: ({dest.q},{dest.r})")
            else:
                lines.append("Dest: -")
            # Draw tooltip background
            tooltip_w = max(font.size(line)[0] for line in lines) + 10
            tooltip_h = len(lines) * (font.get_height() + 2) + 6
            tooltip_x = mouse_x + 16
            tooltip_y = mouse_y + 16
            pygame.draw.rect(
                surface, (255, 255, 220), (tooltip_x, tooltip_y, tooltip_w, tooltip_h)
            )
            pygame.draw.rect(
                surface, (128, 128, 0), (tooltip_x, tooltip_y, tooltip_w, tooltip_h), 1
            )
            for i, line in enumerate(lines):
                text = font.render(line, True, (0, 0, 0))
                surface.blit(
                    text, (tooltip_x + 5, tooltip_y + 3 + i * (font.get_height() + 2))
                )

        # Draw title
        title = title_font.render(
            f"Turn {resp.turnNo} | Score: {resp.score}", True, (0, 0, 0)
        )
        surface.blit(title, (10, 10))
        pygame.display.flip()
        pygame.display.update()
        return True

    def close(self):
        pygame.quit()
