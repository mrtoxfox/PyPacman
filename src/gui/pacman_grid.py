import json

from src.configs import *
from src.gui.fog_manager import FogManager
from src.sprites.pacman import Pacman
from src.sprites.ghosts import GhostManager
from src.utils.coord_utils import (get_coords_from_idx, place_elements_offset,
                                   precompute_matrix_coords)
from src.utils.draw_utils import (draw_circle, draw_debug_rects, draw_rect)
from src.log_handle import get_logger
logger = get_logger(__name__)

class PacmanGrid:
    def __init__(self, screen, game_state):
        logger.info("initializing pacman grid")
        self.function_mapper = {
            "void": self.draw_void,
            "wall": self.draw_wall,
            "dot": self.draw_dot,
            "spoint": self.draw_special_point,
            "power": self.draw_power,
            "null": self.draw_void,
            "elec": self.draw_elec,
        }
        self._screen = screen
        self._game_state = game_state
        self._level_number = self._game_state.level
        self.load_level(self._level_number)
        logger.info("level loaded")
        self.fog = FogManager(self.num_rows, self.num_cols, self.start_x, self.start_y)
        self._pre_reveal_static_cells()
        self.pacman = Pacman(
            self._screen,
            self._game_state,
            self._matrix,
            self._pacman_pos,
            (self.start_x, self.start_y)
        )
        self.ghost = GhostManager(
            self._screen,
            self._game_state,
            self._matrix,
            self.ghost_den,
            (self.start_x, self.start_y)
        )
        logger.info("pacman created")

    def _pre_reveal_static_cells(self):
        # Pacman start position
        pr, pc = self._pacman_pos
        self.fog.reveal_around(pr, pc)

        # Ghost den perimeter so players understand where ghosts come from
        gr, gc = self.ghost_den
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = gr + dr, gc + dc
                if 0 <= nr < self.num_rows and 0 <= nc < self.num_cols:
                    self.fog.reveal_around(nr, nc)

    def get_json(self, path):
        with open(path) as fp:
            payload = json.load(fp)
        return payload

    def load_level(self, level_number):
        level_path = f"levels/level{level_number}.json"
        level_json = self.get_json(level_path)
        num_rows = level_json["num_rows"]
        num_cols = level_json["num_cols"]
        self.ghost_den = level_json['ghost_den']
        self._matrix = level_json["matrix"]
        self._pacman_pos = level_json["pacman_start"]
        self.elec_pos = level_json['elec']
        self.mode_change_times = level_json['scatter_times']
        self.power_up_time = level_json['power_up_time']
        self._game_state.scared_time = self.power_up_time
        self._game_state.mode_change_events = self.mode_change_times
        self.start_x, self.start_y = place_elements_offset(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            CELL_SIZE[0] * num_cols,
            CELL_SIZE[0] * num_rows,
            0.5,
            0.5,
        )
        self._coord_matrix = precompute_matrix_coords(
            self.start_x, self.start_y, CELL_SIZE[0], num_rows, num_cols
        )
        self.num_rows = num_rows
        self.num_cols = num_cols

    def draw_void(self, **kwargs): ...

    def draw_wall(self, **kwargs):
        draw_rect(
            kwargs["x"],
            kwargs["y"],
            kwargs["w"],
            kwargs["h"],
            self._screen,
            Colors.WALL_BLUE,
        )

    def draw_dot(self, **kwargs):
        dot_x = kwargs["x"] + kwargs["w"]
        dot_y = kwargs["y"] + kwargs["h"]
        draw_rect(dot_x, dot_y, 5, 5, self._screen, Colors.WHITE)

    def draw_special_point(self): ...

    def draw_power(self, **kwargs):
        circle_x = kwargs["x"] + kwargs["w"]
        circle_y = kwargs["y"] + kwargs["h"]
        draw_circle(circle_x, circle_y, 7, self._screen, Colors.YELLOW)

    def draw_elec(self, **kwargs):
        draw_rect(kwargs["x"], kwargs["y"], kwargs["w"], 1, self._screen, Colors.RED)

    def update_fog(self):
        subdiv = self.pacman.subdiv
        row = max(0, min(self.pacman.tiny_start_x // subdiv, self.num_rows - 1))
        col = max(0, min(self.pacman.tiny_start_y // subdiv, self.num_cols - 1))
        self.fog.reveal_around(row, col)

    def draw_level(self):
        curr_x, curr_y = self.start_x, self.start_y
        for _, row in enumerate(self._matrix):
            for _, col in enumerate(row):
                draw_func = self.function_mapper[col]
                draw_func(x=curr_x, y=curr_y, w=CELL_SIZE[0], h=CELL_SIZE[0])
                curr_x += CELL_SIZE[0]
            curr_x = self.start_x
            curr_y += CELL_SIZE[0]
        self.update_fog()

    def reset_stage(self):
        self.fog.reset()
        self._pre_reveal_static_cells()
        self.pacman = Pacman(
            self._screen,
            self._game_state,
            self._matrix,
            self._pacman_pos,
            (self.start_x, self.start_y)
        )
        self.ghost = GhostManager(
            self._screen,
            self._game_state,
            self._matrix,
            self.ghost_den,
            (self.start_x, self.start_y)
        )

    def draw_outliners(self):
        draw_debug_rects(
            self.start_x, self.start_y, 128, 140, 5, Colors.GREEN, self._screen
        )
        draw_debug_rects(
            self.start_x,
            self.start_y,
            self.num_rows,
            self.num_cols,
            CELL_SIZE[0],
            Colors.BLUE,
            self._screen,
        )
