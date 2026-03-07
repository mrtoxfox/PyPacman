import math

import pygame

from src.configs import CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

# Magenta — absent from the game palette; used as the shadow-surface colorkey
# so painted pixels become fully transparent when blitted.
_COLORKEY   = (255, 0, 255)
_WALL_COLOR = (24, 24, 217)   # same as Colors.WALL_BLUE


class Flashlight:
    FORWARD_HALF_ANGLE = math.radians(55)
    REAR_HALF_ANGLE    = math.radians(20)
    FORWARD_RADIUS     = 220   # pixels (~11 cells)
    REAR_RADIUS        = 60    # pixels (~3 cells)
    RAY_STEP           = 4     # pixels — matches PACMAN_SPEED
    NUM_FORWARD_RAYS   = 120
    NUM_REAR_RAYS      = 20
    AMBIENT_ALPHA      = 245
    PACMAN_HALO        = 22    # always-lit circle radius around Pacman

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

        self.shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.shadow_surf.set_colorkey(_COLORKEY)
        self.shadow_surf.set_alpha(self.AMBIENT_ALPHA)

    # ------------------------------------------------------------------
    # Ray marching
    # ------------------------------------------------------------------

    def _cast_ray(self, orig_x, orig_y, angle, max_dist):
        """March a ray until a wall or max_dist. Snaps endpoint to wall face."""
        dx = math.cos(angle) * self.RAY_STEP
        dy = math.sin(angle) * self.RAY_STEP
        x, y  = float(orig_x), float(orig_y)
        steps = int(max_dist / self.RAY_STEP)
        for _ in range(steps):
            x += dx
            y += dy
            col = int((x - self.grid_x) / CELL_SIZE[0])
            row = int((y - self.grid_y) / CELL_SIZE[1])
            if row < 0 or col < 0 or row >= self.num_rows or col >= self.num_cols:
                break
            if self.matrix[row][col] == "wall":
                px, py = x - dx, y - dy
                cx0 = self.grid_x + col * CELL_SIZE[0]
                cy0 = self.grid_y + row * CELL_SIZE[1]
                cx1 = cx0 + CELL_SIZE[0]
                cy1 = cy0 + CELL_SIZE[1]
                over_x = max(cx0 - px, px - cx1, 0)
                over_y = max(cy0 - py, py - cy1, 0)
                if over_x >= over_y:
                    x = cx0 if dx > 0 else cx1
                else:
                    y = cy0 if dy > 0 else cy1
                break
        return (x, y)

    # ------------------------------------------------------------------
    # Polygon builders
    # ------------------------------------------------------------------

    def _build_forward_polygon(self, cx, cy, facing_angle):
        points = [(cx, cy)]
        start  = facing_angle - self.FORWARD_HALF_ANGLE
        step   = (self.FORWARD_HALF_ANGLE * 2) / (self.NUM_FORWARD_RAYS - 1)
        for i in range(self.NUM_FORWARD_RAYS):
            points.append(self._cast_ray(cx, cy, start + i * step, self.FORWARD_RADIUS))
        return points

    def _build_rear_polygon(self, cx, cy, facing_angle):
        rear_centre = facing_angle + math.pi
        start = rear_centre - self.REAR_HALF_ANGLE
        step  = (self.REAR_HALF_ANGLE * 2) / (self.NUM_REAR_RAYS - 1)
        points = [(cx, cy)]
        for i in range(self.NUM_REAR_RAYS):
            points.append(self._cast_ray(cx, cy, start + i * step, self.REAR_RADIUS))
        return points

    # ------------------------------------------------------------------
    # Wall-face highlight lines
    # ------------------------------------------------------------------

    def _draw_lit_wall_faces(self, cx, cy):
        """For every wall face that borders a lit corridor cell, draw a clean
        axis-aligned line directly on the screen.

        The shadow_surf pixel check is the sole arbiter of whether a face is
        lit — it reflects the actual polygon with wall occlusion.  The only
        extra filter is a distance floor (PACMAN_HALO) so the always-lit halo
        circle around Pacman doesn't produce stray face lines on walls that are
        outside the visible cone.
        """
        cs    = CELL_SIZE[0]
        pcol  = int((cx - self.grid_x) / cs)
        prow  = int((cy - self.grid_y) / cs)
        reach = self.FORWARD_RADIUS // cs + 2

        r0 = max(0, prow - reach);  r1 = min(self.num_rows, prow + reach + 1)
        c0 = max(0, pcol - reach);  c1 = min(self.num_cols, pcol + reach + 1)

        for row in range(r0, r1):
            for col in range(c0, c1):
                if self.matrix[row][col] != "wall":
                    continue
                wx = int(self.grid_x + col * cs)
                wy = int(self.grid_y + row * cs)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if not (0 <= nr < self.num_rows and 0 <= nc < self.num_cols):
                        continue
                    if self.matrix[nr][nc] == "wall":
                        continue

                    # Face centre — used for the halo distance filter only.
                    if dr == -1:   fcx, fcy = wx + cs // 2, wy
                    elif dr == 1:  fcx, fcy = wx + cs // 2, wy + cs
                    elif dc == -1: fcx, fcy = wx,           wy + cs // 2
                    else:          fcx, fcy = wx + cs,      wy + cs // 2

                    # Skip faces that are only lit because of the halo circle
                    # (those are within PACMAN_HALO pixels of Pacman's centre).
                    if math.hypot(fcx - cx, fcy - cy) <= self.PACMAN_HALO:
                        continue

                    # Sample 3 points 2px into the corridor along the face
                    # (25 %, 50 %, 75 %).  Close sampling catches faces at the
                    # angular cone boundary whose cell-centre is outside the polygon.
                    NUDGE = 2
                    if dr == -1:    # top face — corridor above
                        sxs = [wx + cs//4, wx + cs//2, wx + 3*cs//4]
                        sys_ = [wy - NUDGE, wy - NUDGE, wy - NUDGE]
                    elif dr == 1:   # bottom face — corridor below
                        sxs = [wx + cs//4, wx + cs//2, wx + 3*cs//4]
                        sys_ = [wy + cs + NUDGE, wy + cs + NUDGE, wy + cs + NUDGE]
                    elif dc == -1:  # left face — corridor to left
                        sxs = [wx - NUDGE, wx - NUDGE, wx - NUDGE]
                        sys_ = [wy + cs//4, wy + cs//2, wy + 3*cs//4]
                    else:           # right face — corridor to right
                        sxs = [wx + cs + NUDGE, wx + cs + NUDGE, wx + cs + NUDGE]
                        sys_ = [wy + cs//4, wy + cs//2, wy + 3*cs//4]

                    lit = False
                    for tx, ty in zip(sxs, sys_):
                        if not (0 <= tx < SCREEN_WIDTH and 0 <= ty < SCREEN_HEIGHT):
                            continue
                        if self.shadow_surf.get_at((tx, ty))[0] >= 200:
                            lit = True
                            break
                    if not lit:
                        continue

                    # Draw the shared face as a solid 1-px line.
                    if dr == -1:
                        pygame.draw.line(self.screen, _WALL_COLOR,
                                         (wx, wy), (wx + cs, wy))
                    elif dr == 1:
                        pygame.draw.line(self.screen, _WALL_COLOR,
                                         (wx, wy + cs), (wx + cs, wy + cs))
                    elif dc == -1:
                        pygame.draw.line(self.screen, _WALL_COLOR,
                                         (wx, wy), (wx, wy + cs))
                    else:
                        pygame.draw.line(self.screen, _WALL_COLOR,
                                         (wx + cs, wy), (wx + cs, wy + cs))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_level(self, matrix, grid_start_pos):
        self.matrix   = matrix
        self.num_rows = len(matrix)
        self.num_cols = len(matrix[0])
        self.grid_x, self.grid_y = grid_start_pos

    def draw(self):
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

        self.shadow_surf.fill((0, 0, 0))
        if len(forward_poly) >= 3:
            pygame.draw.polygon(self.shadow_surf, _COLORKEY, forward_poly)
        if len(rear_poly) >= 3:
            pygame.draw.polygon(self.shadow_surf, _COLORKEY, rear_poly)
        pygame.draw.circle(self.shadow_surf, _COLORKEY, (cx, cy), self.PACMAN_HALO)

        # Apply darkness overlay
        self.screen.blit(self.shadow_surf, (0, 0))

        # Draw clean wall-face lines on top — one solid segment per lit face
        self._draw_lit_wall_faces(cx, cy)
