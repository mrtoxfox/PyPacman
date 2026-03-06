import pygame
from src.configs import *
from src.gui.pacman_grid import *
from src.gui.loading_screen import LoadingScreen
from src.gui.score_screen import ScoreScreen
from src.log_handle import get_logger

from pygame.time import wait

logger = get_logger(__name__)

class ScreenManager:
    def __init__(self, screen, game_state, all_sprites):
        logger.info("screen manager initializing")
        self._screen = screen
        self._game_state = game_state
        self.all_sprites = all_sprites
        self.loading_screen = LoadingScreen(self._screen)
        self.pacman = PacmanGrid(screen, game_state)
        self.score_screen = ScoreScreen(self._screen, self._game_state)
        logger.info("pacman grid created")
        self.all_sprites.add(self.pacman.pacman)
        for ghost in self.pacman.ghost.ghosts_list:
            self.all_sprites.add(ghost)

    def pacman_dead_reset(self):
        if self._game_state.is_pacman_dead:
            if self._game_state.lives <= 0:
                self._game_state.game_over = True
                self._game_state.is_pacman_dead = False
                return
            self._game_state.is_pacman_dead = False
            self._game_state.direction = ""
            self._game_state.pacman_direction = None
            self.all_sprites.empty()
            self.pacman.reset_stage()
            self.all_sprites.add(self.pacman.pacman)
            for ghost in self.pacman.ghost.ghosts_list:
                self.all_sprites.add(ghost)
    
    def check_level_complete(self):
        if self._game_state.level_complete:
            wait(2000)
            self._game_state.lives = 3
            self._game_state.is_immortal = False
            self._game_state.immortal_start_time = None
            self.all_sprites.empty()
            self.pacman = PacmanGrid(self._screen, self._game_state)
            self.score_screen = ScoreScreen(self._screen, self._game_state)
            logger.info("pacman grid created")
            self.all_sprites.add(self.pacman.pacman)
            for ghost in self.pacman.ghost.ghosts_list:
                self.all_sprites.add(ghost)
            self._game_state.level_complete = False

    def draw_pause_overlay(self):
        if not self._game_state.is_paused:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self._screen.blit(overlay, (0, 0))
        pause_font = pygame.font.Font(None, 80)
        text = pause_font.render("PAUSED", True, Colors.WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._screen.blit(text, rect)
        hint_font = pygame.font.Font(None, 36)
        hint = hint_font.render("Press SPACE to resume", True, Colors.WHITE)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self._screen.blit(hint, hint_rect)

    def draw_game_over(self):
        if not self._game_state.game_over:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self._screen.blit(overlay, (0, 0))
        big_font = pygame.font.Font(None, 100)
        text = big_font.render("GAME OVER", True, (220, 50, 50))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self._screen.blit(text, rect)
        small_font = pygame.font.Font(None, 40)
        score_text = small_font.render(f"Final Score: {self._game_state.points}", True, Colors.WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self._screen.blit(score_text, score_rect)
        quit_text = small_font.render("Press Q to quit", True, Colors.WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90))
        self._screen.blit(quit_text, quit_rect)

    def draw_screens(self):
        self.pacman.draw_level()
        self.pacman_dead_reset()
        self.score_screen.draw_scores()
        self.check_level_complete()
        self.draw_pause_overlay()
        self.draw_game_over()
