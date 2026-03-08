import math

import pygame

from src.configs import CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

# Magenta — absent from the game palette; used as the shadow-surface colorkey
# so painted pixels become fully transparent when blitted.
_COLORKEY   = (255, 0, 255)
_WALL_COLOR = (24, 24, 217)   # same as Colors.WALL_BLUE

# Distance jump (in pixels) between adjacent rays that triggers a binary
# search for the wall-corner transition angle.  Roughly 1.5 cells.
_TRANSITION_THRESHOLD = CELL_SIZE[0] * 1.5


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
        self._lit_cells  = set()

        self.shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.shadow_surf.set_colorkey(_COLORKEY)
        self.shadow_surf.set_alpha(self.AMBIENT_ALPHA)

    # ------------------------------------------------------------------
    # Ray marching
    # ------------------------------------------------------------------

    def _cast_ray(self, orig_x, orig_y, angle, max_dist, lit_cells=None):
        """March a ray until a wall or max_dist.

        Uses parametric line-cell intersection to snap the endpoint to the
        exact wall boundary.

        If *lit_cells* is a set, every corridor cell the ray passes through
        is added to it (used later for wall-face highlighting).
        """
        dx = math.cos(angle) * self.RAY_STEP
        dy = math.sin(angle) * self.RAY_STEP
        x, y  = float(orig_x), float(orig_y)
        steps = int(max_dist / self.RAY_STEP)
        cs_x  = CELL_SIZE[0]
        cs_y  = CELL_SIZE[1]
        gx, gy = self.grid_x, self.grid_y

        for _ in range(steps):
            x += dx
            y += dy
            col = int((x - gx) / cs_x)
            row = int((y - gy) / cs_y)
            if row < 0 or col < 0 or row >= self.num_rows or col >= self.num_cols:
                break
            if self.matrix[row][col] == "wall":
                # Previous position — still in corridor (or on boundary).
                px, py = x - dx, y - dy
                # Wall cell screen bounds.
                cx0 = gx + col * cs_x
                cy0 = gy + row * cs_y
                cx1 = cx0 + cs_x
                cy1 = cy0 + cs_y

                # Find the parametric t (0..1] where the segment (px,py)->(x,y)
                # first crosses this wall cell's boundary.
                best_t = 1.0

                if dx != 0:
                    face_x = cx0 if dx > 0 else cx1
                    t = (face_x - px) / dx
                    if 0 < t <= 1:
                        iy = py + t * dy
                        if cy0 - 0.5 <= iy <= cy1 + 0.5:
                            best_t = min(best_t, t)

                if dy != 0:
                    face_y = cy0 if dy > 0 else cy1
                    t = (face_y - py) / dy
                    if 0 < t <= 1:
                        ix = px + t * dx
                        if cx0 - 0.5 <= ix <= cx1 + 0.5:
                            best_t = min(best_t, t)

                x = px + best_t * dx
                y = py + best_t * dy
                break
            elif lit_cells is not None:
                lit_cells.add((row, col))
        return (x, y)

    # ------------------------------------------------------------------
    # Transition refinement
    # ------------------------------------------------------------------

    def _refine_transition(self, cx, cy, angle_a, dist_a,
                           angle_b, dist_b, max_dist, depth=6):
        """Binary-search between two ray angles that have a large distance
        jump to find the wall-corner transition.  Returns a list of
        intermediate (x, y) points to splice into the polygon."""
        if depth <= 0:
            return []

        mid_angle = (angle_a + angle_b) * 0.5
        ep = self._cast_ray(cx, cy, mid_angle, max_dist, self._lit_cells)
        dist_mid = math.hypot(ep[0] - cx, ep[1] - cy)

        result = []

        if abs(dist_a - dist_mid) > _TRANSITION_THRESHOLD:
            result.extend(self._refine_transition(
                cx, cy, angle_a, dist_a, mid_angle, dist_mid,
                max_dist, depth - 1))

        result.append(ep)

        if abs(dist_mid - dist_b) > _TRANSITION_THRESHOLD:
            result.extend(self._refine_transition(
                cx, cy, mid_angle, dist_mid, angle_b, dist_b,
                max_dist, depth - 1))

        return result

    # ------------------------------------------------------------------
    # Polygon builders
    # ------------------------------------------------------------------

    def _build_forward_polygon(self, cx, cy, facing_angle):
        start = facing_angle - self.FORWARD_HALF_ANGLE
        step  = (self.FORWARD_HALF_ANGLE * 2) / (self.NUM_FORWARD_RAYS - 1)

        # Cast all primary rays, keeping angle + distance for transition detection.
        rays = []
        for i in range(self.NUM_FORWARD_RAYS):
            a  = start + i * step
            ep = self._cast_ray(cx, cy, a, self.FORWARD_RADIUS, self._lit_cells)
            d  = math.hypot(ep[0] - cx, ep[1] - cy)
            rays.append((a, ep, d))

        # Build polygon, inserting refined points at large distance jumps.
        points = [(cx, cy)]
        for i, (a, ep, d) in enumerate(rays):
            if i > 0:
                pa, _, pd = rays[i - 1]
                if abs(d - pd) > _TRANSITION_THRESHOLD:
                    points.extend(self._refine_transition(
                        cx, cy, pa, pd, a, d, self.FORWARD_RADIUS))
            points.append(ep)
        return points

    def _build_rear_polygon(self, cx, cy, facing_angle):
        rear_centre = facing_angle + math.pi
        start = rear_centre - self.REAR_HALF_ANGLE
        step  = (self.REAR_HALF_ANGLE * 2) / (self.NUM_REAR_RAYS - 1)
        points = [(cx, cy)]
        for i in range(self.NUM_REAR_RAYS):
            points.append(
                self._cast_ray(cx, cy, start + i * step,
                               self.REAR_RADIUS, self._lit_cells))
        return points

    # ------------------------------------------------------------------
    # Wall-face highlight lines
    # ------------------------------------------------------------------

    def _draw_lit_wall_faces(self, cx, cy):
        """Draw a 1-px blue line on every wall face whose adjacent corridor
        cell was traversed by at least one ray.

        Uses the _lit_cells set built during ray casting instead of sampling
        pixels on the shadow surface — this eliminates the torn/flickering
        highlights caused by polygon rasterisation artifacts at cone edges.
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

                    # Only highlight if the corridor cell was hit by a ray.
                    if (nr, nc) not in self._lit_cells:
                        continue

                    # Face centre — used for the halo distance filter only.
                    if dr == -1:   fcx, fcy = wx + cs // 2, wy
                    elif dr == 1:  fcx, fcy = wx + cs // 2, wy + cs
                    elif dc == -1: fcx, fcy = wx,           wy + cs // 2
                    else:          fcx, fcy = wx + cs,      wy + cs // 2

                    # Skip faces that are only lit because of the halo circle.
                    if math.hypot(fcx - cx, fcy - cy) <= self.PACMAN_HALO:
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

        # Reset lit-cell tracking for this frame.
        self._lit_cells.clear()

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

        # Draw clean wall-face lines on top
        self._draw_lit_wall_faces(cx, cy)
