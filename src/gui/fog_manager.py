import math

import pygame

from src.configs import CELL_SIZE, FOG_ALPHA, FOG_REVEAL_RADIUS


class FogManager:
    def __init__(self, num_rows, num_cols, start_x, start_y):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.start_x = start_x
        self.start_y = start_y
        self.cell_w = CELL_SIZE[0]
        self.cell_h = CELL_SIZE[1]
        self.revealed = [[False] * num_cols for _ in range(num_rows)]
        self.fog_surface = self._make_surface()

    def _make_surface(self):
        w = self.num_cols * self.cell_w
        h = self.num_rows * self.cell_h
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        surface.fill((0, 0, 0, FOG_ALPHA))
        return surface

    def reveal_around(self, row, col, radius=FOG_REVEAL_RADIUS):
        r_int = int(radius) + 1
        for dr in range(-r_int, r_int + 1):
            for dc in range(-r_int, r_int + 1):
                if math.sqrt(dr * dr + dc * dc) > radius:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.num_rows and 0 <= nc < self.num_cols:
                    if not self.revealed[nr][nc]:
                        self.revealed[nr][nc] = True
                        rect = pygame.Rect(
                            nc * self.cell_w, nr * self.cell_h,
                            self.cell_w, self.cell_h
                        )
                        self.fog_surface.fill((0, 0, 0, 0), rect)

    def reset(self):
        self.revealed = [[False] * self.num_cols for _ in range(self.num_rows)]
        self.fog_surface = self._make_surface()

    def draw(self, screen):
        screen.blit(self.fog_surface, (self.start_x, self.start_y))
