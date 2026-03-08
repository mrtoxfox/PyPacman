# CoT prompt
You are an elite software engineer specializing in structured, transparent bug fixing using Chain of Thought (CoT)       
reasoning. You work on a Pacman game built with pygame-ce, following a classic game loop architecture with centralized   
state management. Describe each step you take in detail, narrating your thought process explicitly before acting. Always 
start by confirming git branch strategy with the user. Then, for each bug fix, follow a structured CoT approach:
       
1. Bug Reproduction & Localization                        
2. Codebase Impact Analysis
3. Root Cause Identification
4. Edge Cases & Risks
5. Fix Plan (presented to user for confirmation before coding)

Bug: When a ghost wraps through the side tunnel, its sprite visually flies across the full screen width instead of
appearing instantly on the other side.

# Data flow explanation prompt
In src/sprites/ghosts.py, _boundary_check() wraps next_tile to the
opposite tunnel side but doesn't update the lerp source:

    def _boundary_check(self):
        if self.next_tile[1] >= self.num_cols:
            self.next_tile = (self.next_tile[0], 0)
            return
        if self.next_tile[1] < 0:
            self.next_tile = (self.next_tile[0], self.num_cols - 1)

In move_ghost(), the lerp goes from coords(self.prev) to
coords(self.next_tile). After a wrap, prev is still on the original side
so the lerp animates a cross-screen flight.

Fix: after wrapping next_tile, also update self.prev to the wrapped
destination and immediately set self.rect_x / self.rect_y to the
destination screen coordinates (teleport the sprite, don't lerp across).

Only fix _boundary_check() and the immediate screen position update.
Do not change move_ghost()'s lerp logic.