# Task
Implement Fog of War in a Pygame Pacman clone. Unvisited maze areas are hidden. Tiles reveal permanently as Pacman moves
near them. Ghosts under fog are invisible.

## Step 1 - Branch
Generate 3 fundamentally different solution strategies for rendering and tracking fog. Each strategy must be a complete,
independent approach - not a variation of another.

## Step 2 - Evaluate
For each strategy, score on a 1-5 scale:
- Performance at 60 FPS
- Visual quality
- Code complexity
- Integration risk with existing codebase

## Step 3 - Prune
Eliminate the weakest strategy. Explain why it loses.

## Step 4 - Deepen
Take the 2 surviving strategies and think one level deeper: what edge cases, failure modes, or hidden costs emerge when
you consider the actual implementation? Consider at minimum:
- What is the reveal radius - how many cells around Pacman get permanently uncovered?
- Does fog reset between lives or persist across deaths?
- Does fog reset on level completion/restart?
- How does fog interact with the tunnel wrap-around areas at map edges?
- Ghost den area - should it start revealed, or stay fogged until Pacman approaches?
- Dots and power pellets under fog - fully hidden, or faintly hinted to preserve playability?
- Ghosts crossing between fogged and revealed areas - when exactly do they appear/disappear?
- Does the fog edge transition look clean, or does it create jagged/torn boundaries along walls?
- How does the fog overlay interact with the score display, pause screen, and death animation?
- Performance cost of tracking revealed state for every cell across the full grid

## Step 5 - Select
Choose the winner. Justify with a direct comparison.

## Step 6 - Plan
Produce a step-by-step implementation plan from the winning strategy.