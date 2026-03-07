import math

import pygame

from src.configs import CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

# A color that does not appear anywhere in the game palette.
# Pixels painted this color become transparent via colorkey.
_COLORKEY = (255, 0, 255)


class Flashlight:
    FORWARD_HALF_ANGLE = math.radians(55)
    REAR_HALF_ANGLE    = math.radians(20)
    FORWARD_RADIUS     = 220   # pixels (~11 cells)
    REAR_RADIUS        = 60    # pixels (~3 cells)
    RAY_STEP           = 4     # pixels — matches PACMAN_SPEED
    NUM_FORWARD_RAYS   = 120
    NUM_REAR_RAYS      = 20
    AMBIENT_ALPHA      = 245   # darkness outside cone (0=transparent, 255=opaque)
    # Radius of the always-lit circle centred on Pacman so the full sprite is visible
    PACMAN_HALO        = 22    # slightly larger than half the 32 px sprite

    DIR_TO_ANGLE = {
        'r':  0.0,
        'd':  math.pi / 2,
        'l':  math.pi,
        'u': -math.pi / 2,
    }

    def __init__(self, screen, game_state, matrix, grid_start_pos):
        self.screen     = screen
        self.game_state = game_state
        self.matrix     = matrix
        self.grid_x, self.grid_y = grid_start_pos
        self.num_rows   = len(matrix)
        self.num_cols   = len(matrix[0])
        self._last_angle = 0.0

        # Regular (non-SRCALPHA) surface so set_colorkey + set_alpha work reliably.
        # Pixels painted _COLORKEY become fully transparent holes in the darkness.
        # All other pixels (black) are blitted at AMBIENT_ALPHA opacity.
        self.shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.shadow_surf.set_colorkey(_COLORKEY)
        self.shadow_surf.set_alpha(self.AMBIENT_ALPHA)

    # ------------------------------------------------------------------
    # Ray marching
    # ------------------------------------------------------------------

    def _cast_ray(self, ox, oy, angle, max_dist):
        """March a ray from (ox, oy) at angle until a wall or max_dist."""
        dx = math.cos(angle) * self.RAY_STEP
        dy = math.sin(angle) * self.RAY_STEP
        x, y  = float(ox), float(oy)
        steps = int(max_dist / self.RAY_STEP)
        for _ in range(steps):
            x += dx
            y += dy
            col = int((x - self.grid_x) / CELL_SIZE[0])
            row = int((y - self.grid_y) / CELL_SIZE[1])
            if row < 0 or col < 0 or row >= self.num_rows or col >= self.num_cols:
                break
            if self.matrix[row][col] == "wall":
                break
        return (x, y)

    # ------------------------------------------------------------------
    # Polygon builders
    # ------------------------------------------------------------------

    def _build_forward_polygon(self, cx, cy, facing_angle):
        """Fan of rays covering the forward cone."""
        points = [(cx, cy)]
        start  = facing_angle - self.FORWARD_HALF_ANGLE
        step   = (self.FORWARD_HALF_ANGLE * 2) / (self.NUM_FORWARD_RAYS - 1)
        for i in range(self.NUM_FORWARD_RAYS):
            angle = start + i * step
            points.append(self._cast_ray(cx, cy, angle, self.FORWARD_RADIUS))
        return points

    def _build_rear_polygon(self, cx, cy, facing_angle):
        """Narrow fan covering the rear glow arc."""
        rear_centre = facing_angle + math.pi
        start = rear_centre - self.REAR_HALF_ANGLE
        step  = (self.REAR_HALF_ANGLE * 2) / (self.NUM_REAR_RAYS - 1)
        points = [(cx, cy)]
        for i in range(self.NUM_REAR_RAYS):
            angle = start + i * step
            points.append(self._cast_ray(cx, cy, angle, self.REAR_RADIUS))
        return points

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_level(self, matrix, grid_start_pos):
        """Call after a level reset so the flashlight uses the new matrix."""
        self.matrix   = matrix
        self.num_rows = len(matrix)
        self.num_cols = len(matrix[0])
        self.grid_x, self.grid_y = grid_start_pos

    def draw(self):
        # Guard: pacman_rect is None on the very first frame before update runs
        if self.game_state.pacman_rect is None:
            self.shadow_surf.fill((0, 0, 0))
            self.screen.blit(self.shadow_surf, (0, 0))
            return

        px, py, pw, ph = self.game_state.pacman_rect
        cx = int(px + pw / 2)
        cy = int(py + ph / 2)

        direction = self.game_state.pacman_direction
        if direction in self.DIR_TO_ANGLE:
            self._last_angle = self.DIR_TO_ANGLE[direction]

        forward_poly = self._build_forward_polygon(cx, cy, self._last_angle)
        rear_poly    = self._build_rear_polygon(cx, cy, self._last_angle)

        # Fill the entire surface with opaque black
        self.shadow_surf.fill((0, 0, 0))

        # Paint lit areas with _COLORKEY — colorkey makes these pixels
        # fully transparent when blitted, so the game content shows through
        # at full brightness with no tinting or alpha reduction.
        if len(forward_poly) >= 3:
            pygame.draw.polygon(self.shadow_surf, _COLORKEY, forward_poly)
        if len(rear_poly) >= 3:
            pygame.draw.polygon(self.shadow_surf, _COLORKEY, rear_poly)

        # Always fully illuminate Pacman's own sprite.
        # The cone polygon fans outward from Pacman's centre, leaving the
        # sides/back of the sprite partially in shadow without this circle.
        pygame.draw.circle(self.shadow_surf, _COLORKEY, (cx, cy), self.PACMAN_HALO)

        # Composite the darkness onto the screen at AMBIENT_ALPHA opacity.
        # Black pixels dim the scene; colorkey pixels are skipped entirely.
        self.screen.blit(self.shadow_surf, (0, 0))
