# Task
Add a universal bonus system with bonuses that affect game mechanics such as Ghost or pacman speed and their sprites to a Pygame Pacman clone.

## Features
- Universal bonus system that spawns bonuses randomly on valid food cells of the map grid
- Freeze bonus - freezes ghosts for 10 seconds
- Slow bonus - halves ghost speed for 10 seconds
- Speed bonus - doubles ghost speed for 10 seconds

## Constraints
- Bonus system must be fully decoupled: no bonus logic inside Ghost, Pacman, or other entity classes. Bonuses interact only through public interfaces of those entities (e.g. set speed, freeze/unfreeze)
- Bonuses spawn only on cells that contain food, centered in the cell grid, never on walls
- Sound plays on: bonus spawn, bonus effect applied, bonus effect expired

## Implementation
Think through the problem step by step before writing any code. For each step, write your reasoning out loud, then proceed to the next. Explain all step you make before impmlement features.

1. **Examine** - What existing systems (sprites, state, rendering, sound) are involved? What public interfaces do they expose that bonuses can use without modifying internals?
2. **Design** - Based on the interfaces found, how should the bonus system be structured? How are bonuses registered, spawned, collected, and expired? What data structures are needed?
3. **Integrate** - What is the minimal set of changes to existing code to hook the bonus system in? Where in the game loop does spawning, collision checking, and expiration happen?
4. **Order** - Given dependencies between components, what must be built first? What can be built in parallel?
5. **Implement** - Wait for approve and than execute the plan. Before writing each piece of code, state what it does and why it's needed.