Write me a Tree of Thought (ToT) prompt for brainstorming the best implementation options, simple math, and edge cases for the flashlight mechanics in this game, and save it in `prompts/flashlight.md`. All map in the dark, and Pac-Man has a flashlight that illuminates the directions Pac-Man is looking.
The light must be physically plausible and not penetrate walls. The flashlight illuminates the space in front of Pac-Man in the shape of a cone and slightly behind him in the form of residual dimmer lighting. The range of the flashlight should be limited to the radius around Pac-Man.
Don't describe implementation details, just task and prompt technique.

# Task
Implement a flashlight mechanic in a Pygame Pacman clone. The entire map is in the dark. Pacman
carries a flashlight that illuminates a cone-shaped area in front of him (the direction he faces)
and casts dimmer residual light slightly behind him. The flashlight has a limited radius. Light is
physically plausible - it does not penetrate or pass through walls.

## Step 1 - Branch
Generate 3 fundamentally different solution strategies for rendering and tracking the flashlight
visibility. Each strategy must be a complete, independent approach - not a variation of another.

## Step 2 - Evaluate
For each strategy, score on a 1-5 scale:
- Performance at 60 FPS
- Visual quality (smooth cone, natural falloff, no artifacts)
- Wall occlusion accuracy (light stops at walls, no leaks)
- Code complexity
- Integration risk with existing codebase

## Step 3 - Prune
Eliminate the weakest strategy. Explain why it loses.

## Step 4 - Deepen
Take the 2 surviving strategies and think one level deeper: what edge cases, failure modes, or
hidden costs emerge when you consider the actual implementation? Consider at minimum:
- The math for cone shape, brightness falloff, and wall blocking
- Behavior in narrow corridors, corners, and intersections
- Performance cost per frame (show rough numbers)
- Interaction with existing overlays (score, pause, death animation)
- Whether ghosts/dots outside the lit area should be fully hidden or faintly visible
- Dots and power pellets must remain fully visible inside the lit area but must NOT affect or alter illumination rendering
- The floor (corridor background) color must be distinct from black so it is readable under the shadow overlay
- Pacman himself must always be fully visible - use a fixed halo circle around him regardless of facing direction
- Wall boundaries in the lit area must appear as clean, solid, continuous lines - not jagged or torn at cone edges or occlusion boundaries
- The shadow compositing approach must use a colorkey (not SRCALPHA) to punch transparent holes for lit areas, because pygame's polygon draw ignores alpha on SRCALPHA surfaces

## Step 5 - Select
Choose the winner. Justify with a direct comparison. Recommend concrete values for the cone angle,
forward radius, rear radius, and falloff curve.

## Step 6 - Plan
Produce a step-by-step implementation plan from the winning strategy.
