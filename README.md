# PyPacman

A Pacman clone written in Python using Pygame.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd PyPacman
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
.venv\Scripts\activate          # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python3 main.py
```

A 1024x768 window will open with the game.

## Controls

- **Arrow Up** - move up
- **Arrow Down** - move down
- **Arrow Left** - move left
- **Arrow Right** - move right

## Gameplay

- Eat all the dots on the map to complete a level.
- Pick up power pellets to temporarily scare ghosts - you can eat them for bonus points while they are scared.
- Five ghosts (Blinky, Pinky, Inky, Clyde, and Blue) chase Pacman using different targeting strategies.
- Ghosts alternate between scatter and chase modes throughout a level.
- There are no game overs. The level resets after you complete it, and your high score is saved between sessions.

## Project Structure

```
PyPacman/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── levels/
│   ├── level1.json          # Level layout
│   └── stats.json           # Persisted high score
├── assets/                  # Sprites and sounds
└── src/
    ├── configs.py           # Game constants
    ├── runner.py            # Main game loop
    ├── sounds.py            # Sound manager
    ├── game/                # Event and state management
    ├── gui/                 # Screen rendering
    ├── sprites/             # Pacman and ghost sprites
    └── utils/               # Movement, drawing, and graph utilities
```

## License

GPLv3 - see [LICENSE](LICENSE) for details.