# PyPacman Feature Implementation Plan

## Game Cycle Summary (for context)

The main loop in `runner.py` runs at 60 FPS:
1. Poll pygame events → `EventHandler.handle_events()`
2. Clear screen, call `ScreenManager.draw_screens()` (draws maze, handles death reset, level complete)
3. `all_sprites.draw()` and `all_sprites.update(dt)` — updates Pacman and all Ghosts
4. Flip display, tick clock

**Death flow**: `Ghost.check_collisions()` detects overlap → sets `game_state.is_pacman_dead = True`, plays death sound, `wait(1000)` → `ScreenManager.pacman_dead_reset()` tears down and rebuilds all sprites. The game currently resets infinitely with no game-over screen and no life tracking.

**Scoring**: `game_state.points` (int). Incremented in `Pacman.eat_dots()` (DOT_POINT, POWER_POINT) and `Ghost.check_collisions()` when eating a scared ghost (GHOST_POINT). Displayed by `ScoreScreen.draw_scores()`.

**Power-up timing**: Uses `pygame.USEREVENT+2` set via `Pacman.create_power_up_event()`. Expiry is handled in `EventHandler.handle_events()` which sets `is_pacman_powered = False`.

---

## Feature 1: Pause Mechanics

### Goal
Press SPACE to pause/resume. While paused: all sprite movement freezes, ghost timers freeze, sounds pause, a "PAUSED" overlay is displayed.

### Step-by-step instructions

#### 1. Add pause state to `GameState` (`src/game/state_management.py`)

Add one new private attribute and its property:

```python
self.__is_paused = False
```

```python
@property
def is_paused(self):
    return self.__is_paused

@is_paused.setter
def is_paused(self, val):
    self.__is_paused = val
```

#### 2. Handle SPACE key in `EventHandler` (`src/game/event_management.py`)

In `key_bindings()`, add a case for `K_SPACE` that toggles the pause flag and pauses/resumes pygame mixer music:

```python
elif key == K_SPACE:
    self._game_screen.is_paused = not self._game_screen.is_paused
    if self._game_screen.is_paused:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()
```

Import `pygame` at the top if not already imported (`from pygame import ...` or `import pygame`).

#### 3. Freeze sprite updates in the main loop (`src/runner.py`)

In `main()`, wrap `all_sprites.update(dt)` with a pause guard. Also freeze the ghost-mode timer by stopping and restarting it:

```python
if not self.game_state.is_paused:
    self.all_sprites.update(dt)
```

The pygame `USEREVENT` timers for ghost mode switching continue firing while paused. To freeze them, stop the timer on pause and restart it on resume. The cleanest way is to track the remaining time. A simpler acceptable approach: set the timer interval to 0 (stops it) on pause and recreate it on resume by calling `create_ghost_mode_event()` again. Implement a helper:

```python
def toggle_pause_timers(self):
    if self.game_state.is_paused:
        pygame.time.set_timer(self.game_state.custom_event, 0)   # stop
        if self.game_state.power_up_event:
            pygame.time.set_timer(self.game_state.power_up_event, 0)
    else:
        self.create_ghost_mode_event()
        # power-up timer: if still powered, restart with remaining time
        if self.game_state.is_pacman_powered and self.game_state.power_event_trigger_time:
            elapsed = pygame.time.get_ticks() - self.game_state.power_event_trigger_time
            remaining = max(0, self.game_state.scared_time - elapsed)
            pygame.time.set_timer(self.game_state.power_up_event, remaining)
```

Call `toggle_pause_timers()` each time pause is toggled. To detect the toggle, track the previous pause state in `main()`:

```python
prev_paused = False
while self.game_state.running:
    ...
    if self.game_state.is_paused != prev_paused:
        self.toggle_pause_timers()
        prev_paused = self.game_state.is_paused
    if not self.game_state.is_paused:
        self.all_sprites.update(dt)
    ...
```

#### 4. Draw "PAUSED" overlay in `ScreenManager` (`src/gui/screen_management.py`)

Add a method and call it in `draw_screens()`:

```python
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
```

In `draw_screens()`, call it last so it renders on top:

```python
def draw_screens(self):
    self.pacman.draw_level()
    self.pacman_dead_reset()
    self.score_screen.draw_scores()
    self.check_level_complete()
    self.draw_pause_overlay()
```

Import `pygame` at the top of `screen_management.py`.

#### 5. Prevent direction changes while paused

In `EventHandler.key_bindings()`, guard movement keys:

```python
def key_bindings(self, key):
    if key == K_SPACE:
        ...  # toggle pause (always allowed)
        return
    if self._game_screen.is_paused:
        return
    # existing arrow key logic below
    if key == K_LEFT:
        ...
```

---

## Feature 2: Lives System with Invincibility

### Goal
Pac-Man starts with 3 lives. On ghost collision (when not scared and not immortal): lose 1 life, halve score, become immortal for 5 seconds (semi-transparent, ghosts ignore him). When lives reach 0, trigger a real game-over. Lives are displayed on the score screen.

### Step-by-step instructions

#### 1. Add lives and invincibility state to `GameState` (`src/game/state_management.py`)

Add new attributes:

```python
self._lives = 3
self._is_immortal = False
self._immortal_start_time = None
```

Add properties:

```python
@property
def lives(self):
    return self._lives

@lives.setter
def lives(self, val):
    self._lives = val

@property
def is_immortal(self):
    return self._is_immortal

@is_immortal.setter
def is_immortal(self, val):
    self._is_immortal = val

@property
def immortal_start_time(self):
    return self._immortal_start_time

@immortal_start_time.setter
def immortal_start_time(self, val):
    self._immortal_start_time = val
```

Also add a constant to `src/configs.py` for the immortality duration:

```python
IMMORTAL_DURATION = 5000  # milliseconds
```

#### 2. Rework the death/collision logic in `Ghost.check_collisions()` (`src/sprites/ghosts.py`)

The current logic immediately sets `is_pacman_dead = True`. Replace the `else` branch with the new multi-life logic:

```python
def check_collisions(self):
    ghost_rect = Rect(self.rect.x, self.rect.y,
                      PACMAN[0] // 2, PACMAN[1] // 2)
    pacman_coords = (self._game_state.pacman_rect[0],
                     self._game_state.pacman_rect[1],
                     self._game_state.pacman_rect[2] // 2,
                     self._game_state.pacman_rect[3] // 2)
    pacman_rect = Rect(pacman_coords)
    if ghost_rect.colliderect(pacman_rect):
        if self.is_scared:
            self.reset_ghost()
            self.sounds.play_sound("eat_ghost")
            self._game_state.points += GHOST_POINT
        elif not self._game_state.is_immortal:
            self._game_state.lives -= 1
            self._game_state.points = max(0, self._game_state.points // 2)
            self.sounds.play_sound("death")
            wait(1000)
            if self._game_state.lives <= 0:
                self._game_state.is_pacman_dead = True
            else:
                # Grant immortality
                self._game_state.is_immortal = True
                self._game_state.immortal_start_time = pytime.get_ticks()
                # Trigger a soft reset: reposition Pacman and ghosts without losing dots
                self._game_state.is_pacman_dead = True  # reuse existing reset flow
```

Note: reusing `is_pacman_dead = True` triggers the existing `pacman_dead_reset()` in `ScreenManager`, which repositions sprites without resetting the level. When `lives <= 0`, the same flag is set — the game-over screen (added in step 5) will intercept it before the normal reset runs.

#### 3. Track immortality expiry in the main loop (`src/runner.py`)

Add a check inside `main()` each frame:

```python
from src.configs import IMMORTAL_DURATION

# Inside the while loop, before gui.draw_screens():
if self.game_state.is_immortal and self.game_state.immortal_start_time is not None:
    elapsed = pygame.time.get_ticks() - self.game_state.immortal_start_time
    if elapsed >= IMMORTAL_DURATION:
        self.game_state.is_immortal = False
        self.game_state.immortal_start_time = None
```

#### 4. Make Pacman semi-transparent during immortality (`src/sprites/pacman.py`)

In `Pacman.update()`, set the image alpha based on the immortality flag. Use a flicker effect (alternating alpha) to signal the state visually:

```python
def apply_immortal_effect(self):
    if self.game_state.is_immortal:
        # Flicker: alternate between opaque and semi-transparent every ~10 frames
        tick = pygame.time.get_ticks() // 100  # changes every 100ms
        alpha = 80 if tick % 2 == 0 else 200
        self.image = self.image.copy()
        self.image.set_alpha(alpha)
    else:
        self.image.set_alpha(255)
```

Call `apply_immortal_effect()` at the end of `update()`, after `frame_direction_update()`:

```python
def update(self, dt: float):
    self.frame_update()
    self.build_bounding_boxes(self.rect_x, self.rect_y)
    self.movement_bind()
    self.move_pacman(dt)
    self.boundary_check()
    self.eat_dots()
    self.frame_direction_update()
    self.apply_immortal_effect()
    if self.collectibles == 0:
        self.game_state.level_complete = True
```

Import `pygame` at the top of `pacman.py` if not already available (it is via `pygame.sprite`, `pygame.image`, etc — just add `import pygame` or use `pygame.time.get_ticks()`).

#### 5. Make ghosts ignore Pacman during immortality

The guard `elif not self._game_state.is_immortal` added in step 2 already prevents damage. To make ghosts visually "lose interest" (wander randomly instead of chasing), modify `Ghost.determine_target()` behavior by overriding the target selection when Pacman is immortal. The cleanest approach is to add an override in `prepare_movement()`:

```python
def prepare_movement(self):
    ghost_x, ghost_y = self._get_idx_from_coords((self.rect_x, self.rect_y))
    if self.next_tile:
        ghost_x, ghost_y = self.next_tile
    if self.is_scared or self._game_state.is_immortal:
        self._target = self.get_random_target()
    else:
        self._target = self.determine_target()
    ...  # rest unchanged
```

This causes all ghosts to wander randomly for the entire immortality window.

#### 6. Reset lives on full game reset and after level complete

In `ScreenManager.pacman_dead_reset()`, add a check: if `lives <= 0`, show game-over instead of resetting. Add a `game_over` flag to `GameState`:

```python
# In GameState.__init__:
self._game_over = False

# Property:
@property
def game_over(self):
    return self._game_over

@game_over.setter
def game_over(self, val):
    self._game_over = val
```

In `ScreenManager.pacman_dead_reset()`:

```python
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
```

Add `draw_game_over()` to `ScreenManager` and call it in `draw_screens()`:

```python
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
```

Handle Q key during game over in `EventHandler.key_bindings()`:

```python
elif key == K_q:
    if self._game_screen.game_over:
        self._game_screen.running = False
```

Also stop sprite updates in `runner.py` when game over:

```python
if not self.game_state.is_paused and not self.game_state.game_over:
    self.all_sprites.update(dt)
```

On level complete (`ScreenManager.check_level_complete()`), reset lives back to 3 to give the player a fresh start on the new level:

```python
def check_level_complete(self):
    if self._game_state.level_complete:
        wait(2000)
        self._game_state.lives = 3
        self._game_state.is_immortal = False
        ...  # existing reset code
```

#### 7. Display lives on the score screen (`src/gui/score_screen.py`)

In `ScoreScreen.draw_scores()`, render the lives count (or heart icons if assets are available):

```python
lives_text = "LIVES: " + str(self._game_state.lives)
lives_surface = self.font.render(lives_text, True, Colors.WHITE)
self._screen.blit(lives_surface, (self.start_x + 600, self.start_y))
```
