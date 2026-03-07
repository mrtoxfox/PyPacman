import random

import pygame
from pygame.time import get_ticks

from src.configs import (CELL_SIZE, BONUS_DURATION, BONUS_SPAWN_INTERVAL,
                         BONUS_FIRST_SPAWN_DELAY, MAX_ACTIVE_BONUSES)
from src.sounds import SoundManager


class BonusType:
    FREEZE = "freeze"
    SLOW = "slow"
    SPEED = "speed"


BONUS_LABELS = {
    BonusType.FREEZE: "F",
    BonusType.SLOW:   "S",
    BonusType.SPEED:  "X",
}


class _ActiveBonus:
    def __init__(self, bonus_type, row, col, screen_x, screen_y):
        self.type = bonus_type
        self.row = row
        self.col = col
        self.x = screen_x
        self.y = screen_y
        self.color = (random.randint(50, 255),
                      random.randint(50, 255),
                      random.randint(50, 255))


class BonusManager:
    def __init__(self, screen, game_state, matrix, ghost_manager, grid_start_pos):
        self._screen = screen
        self._game_state = game_state
        self._matrix = matrix
        self._ghost_manager = ghost_manager
        self._start_x, self._start_y = grid_start_pos
        self._sounds = SoundManager()
        self._font = pygame.font.SysFont(None, 14)

        self._active_bonuses: list[_ActiveBonus] = []
        # Each entry: {"type": str, "expire_time": int}
        self._active_effects: list[dict] = []
        self._next_spawn_time = get_ticks() + BONUS_FIRST_SPAWN_DELAY
        self._all_types = [BonusType.FREEZE, BonusType.SLOW, BonusType.SPEED]

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _food_cells(self) -> list[tuple[int, int]]:
        """Return (row, col) of every cell currently containing a dot."""
        cells = []
        for r, row in enumerate(self._matrix):
            for c, cell in enumerate(row):
                if cell == "dot":
                    cells.append((r, c))
        return cells

    def _cell_to_screen(self, row, col) -> tuple[int, int]:
        x = self._start_x + col * CELL_SIZE[0] + CELL_SIZE[0]
        y = self._start_y + row * CELL_SIZE[1] + CELL_SIZE[1]
        return x, y

    # ------------------------------------------------------------------ #
    #  Spawn                                                               #
    # ------------------------------------------------------------------ #

    def _try_spawn(self):
        now = get_ticks()
        if now < self._next_spawn_time:
            return
        if len(self._active_bonuses) >= MAX_ACTIVE_BONUSES:
            return

        occupied = {(b.row, b.col) for b in self._active_bonuses}
        available = [c for c in self._food_cells() if c not in occupied]
        if not available:
            return

        row, col = random.choice(available)
        bonus_type = random.choice(self._all_types)
        sx, sy = self._cell_to_screen(row, col)
        self._active_bonuses.append(_ActiveBonus(bonus_type, row, col, sx, sy))
        self._next_spawn_time = now + BONUS_SPAWN_INTERVAL
        self._sounds.play_sound("bonus_spawn")

    # ------------------------------------------------------------------ #
    #  Collision                                                           #
    # ------------------------------------------------------------------ #

    def _check_collision(self):
        if self._game_state.pacman_rect is None:
            return
        px, py, pw, ph = self._game_state.pacman_rect
        pacman_cx = px + pw // 2
        pacman_cy = py + ph // 2

        for bonus in list(self._active_bonuses):
            if abs(pacman_cx - bonus.x) < CELL_SIZE[0] and \
               abs(pacman_cy - bonus.y) < CELL_SIZE[1]:
                self._active_bonuses.remove(bonus)
                self._apply_effect(bonus.type)
                self._sounds.play_sound("bonus_collect")

    # ------------------------------------------------------------------ #
    #  Effects                                                             #
    # ------------------------------------------------------------------ #

    def _apply_effect(self, bonus_type: str):
        now = get_ticks()
        # Remove any existing effect of the same type so duration resets
        self._active_effects = [e for e in self._active_effects
                                 if e["type"] != bonus_type]
        self._active_effects.append({"type": bonus_type,
                                     "expire_time": now + BONUS_DURATION})

        match bonus_type:
            case BonusType.FREEZE:
                self._ghost_manager.freeze_all()
            case BonusType.SLOW:
                self._ghost_manager.set_speed_all(0.5)
            case BonusType.SPEED:
                self._ghost_manager.set_speed_all(2.0)

    def _expire_effect(self, bonus_type: str):
        match bonus_type:
            case BonusType.FREEZE:
                self._ghost_manager.unfreeze_all()
            case BonusType.SLOW:
                self._ghost_manager.set_speed_all(1.0)
            case BonusType.SPEED:
                self._ghost_manager.set_speed_all(1.0)
        self._sounds.play_sound("bonus_expire")

    def _check_expirations(self):
        now = get_ticks()
        expired = [e for e in self._active_effects if now >= e["expire_time"]]
        for effect in expired:
            self._active_effects.remove(effect)
            self._expire_effect(effect["type"])

    # ------------------------------------------------------------------ #
    #  Reset (on death or level complete)                                  #
    # ------------------------------------------------------------------ #

    def reset(self):
        self._active_bonuses.clear()
        self._active_effects.clear()
        self._next_spawn_time = get_ticks() + BONUS_FIRST_SPAWN_DELAY
        self._ghost_manager.unfreeze_all()
        self._ghost_manager.set_speed_all(1.0)

    # ------------------------------------------------------------------ #
    #  Draw                                                                #
    # ------------------------------------------------------------------ #

    def draw(self):
        for bonus in self._active_bonuses:
            cx, cy = int(bonus.x), int(bonus.y)
            pygame.draw.circle(self._screen, bonus.color, (cx, cy), 8)
            pygame.draw.circle(self._screen, (255, 255, 255), (cx, cy), 8, 1)
            label = self._font.render(BONUS_LABELS[bonus.type], True, (0, 0, 0))
            self._screen.blit(label, (cx - label.get_width() // 2,
                                      cy - label.get_height() // 2))

    # ------------------------------------------------------------------ #
    #  Update (called every frame)                                         #
    # ------------------------------------------------------------------ #

    def update(self):
        self._try_spawn()
        self._check_collision()
        self._check_expirations()
