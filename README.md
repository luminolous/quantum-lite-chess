# Quantum Lite Chess

A Pygame-based chess game that adds a **“quantum-lite”** layer on top of standard chess rules:
pieces can **split into two destinations**, the game can maintain **multiple classical branches** at once,
and some events behave like **probabilistic measurement/collapse**.

<p align="center">
  <img src="assets\preview.png" alt="QLC Preview" width="720" />
</p>

This project uses:
- **python-chess** for classical legality (legal moves, check rules, castling, en passant, promotion)
- **Pygame** for UI and input
- **CairoSVG** to render SVG boards/pieces into Pygame surfaces

---

## Features

- Standard chess rules enforced by python-chess (move legality, checks, etc.)
- “Quantum-lite” state represented as a **set of board branches**
- **Split move**: create a superposition of two quiet moves (UI-assisted)
- Basic **branch merging** (identical positions) and **pruning** (branch limit)
- Simple bot (random legal move selection, sometimes attempts split)
- UI hints, move log, game-over overlay

---

## Quick Start

### 1) Create and activate a virtual environment

#### Windows (PowerShell)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

#### Recommended (clean install)
```bash
pip install -U pip
pip install pygame cairosvg chess pillow
```

#### Using `requirements.txt`
```bash
pip install -r requirements.txt
```

> Note: if your `requirements.txt` is saved as UTF-16 and `pip` fails to read it, convert it to UTF-8 first (macOS/Linux):
```bash
iconv -f utf-16 -t utf-8 requirements.txt > requirements.utf8.txt
pip install -r requirements.utf8.txt
```

---

## Run the Game

From the repository root:

```bash
python main.py
```

A window titled **“Quantum Lite Chess”** should appear.

---

## Controls

### Main Menu
- Press **W** to play as White
- Press **B** to play as Black

### In-Game
- **Click** one of your pieces to select
- **Click** a highlighted square to make a normal move
- Press **Q** to toggle *Quantum Mode* ON/OFF
- **Quantum split move (when Quantum Mode is ON)**:
  1) Select your piece  
  2) Hold **SHIFT** and click an **empty** highlighted square to set **Target A**  
  3) Click a different highlighted square to set **Target B**  
- Press **ESC**:
  - If game is over: return to menu
  - If game is running: cancel selection / cancel split Target A

---

## How “Quantum-Lite” Works (High-Level)

Internally, the game maintains multiple classical boards (“branches”) at once.
A move can:
- Apply to all branches (when legal),
- Apply only to some branches (others may become “null moves”),
- Trigger measurement-like collapse for special cases (e.g., capture/no-capture outcomes),
- Merge branches when they become identical again.

This is intentionally “lite”: it aims to be playable and easy to reason about, not a physically rigorous model.

---

## Project Structure

```text
.
├─ main.py                    # Entry point
├─ app/
│  ├─ game.py                 # Main loop, input handling, menus
│  ├─ assets.py               # Asset loading (SVG -> PNG via CairoSVG)
│  └─ config.py               # Screen/board config + asset paths
├─ render/
│  └─ renderer.py             # Drawing board, pieces, HUD, highlights
├─ quantum/
│  └─ quantum_board.py        # Quantum-lite engine (branches + amplitudes)
├─ qlc/
│  ├─ board.py                # Legacy weighted-branch board implementation
│  ├─ rules.py                # Move generation helpers
│  └─ piece.py                # Piece representation used by renderer
├─ ai/
│  └─ bot.py                  # Simple bot logic
├─ assets/
│  ├─ boards/                 # SVG boards
│  └─ p1/                     # Piece SVGs + background images
└─ requirements.txt
```

---

## Platform Notes (Important)

### macOS / Linux path fix
`app/config.py` currently uses Windows-style paths (for example `assets\p1`).
On macOS/Linux, these may not resolve correctly. Prefer using `os.path.join(...)` or forward slashes.

### CairoSVG / Cairo dependency issues
If you see errors like:
- `OSError: no library called "cairo" was found`

It usually means the Cairo system library is missing. Install Cairo for your OS, then retry.

---

## Troubleshooting

### Black screen / missing pieces
- Confirm files exist under `assets/p1/`
- Check the asset paths in `app/config.py` (especially on macOS/Linux)
- Ensure `cairosvg` can load SVGs (see Cairo dependency note above)

### `ImportError` / chess module conflicts
This project expects **python-chess** (import name: `chess`).
If your environment also has a different package that provides `chess`, remove it and reinstall the correct one.