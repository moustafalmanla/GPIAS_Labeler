# GPIAS Labeler

GPIAS Labeler is a desktop annotation tool for labeling startle-response trials loaded from `.npy` files.
It displays one trial at a time, lets you label each trial as `startle`, `nonstartle`, or `uncertain`, and saves labels to `labels.csv`.

## What the software does

- Opens a NumPy data file (`.npy`) selected from a file dialog.
- Prompts for an expert ID to track who performed the annotation.
- Displays each trial waveform in a Qt + Matplotlib GUI.
- Shows trials in randomized order for labeling.
- Supports keyboard shortcuts and mouse buttons for labeling/navigation.
- Shows per-trial label state and overall progress (`labeled / total`).
- Saves all label entries (with timestamps) to CSV.

## Project structure and file overview

### `main.py`
Small launcher script. Imports and runs `main()` from `gpias_labeler/Labeler_main.py`.

### `gpias_labeler/Labeler_main.py`
Application entry point:

- Creates `QApplication`.
- Opens file picker for `.npy` input.
- Loads trial data via `load_data()`.
- Prompts for expert ID.
- Creates `LabelManager` and `LabelGUI`.
- Starts the Qt event loop.

### `gpias_labeler/config.py`
Centralized runtime constants:

- `STIMULUS_TIME_MS`: vertical marker time in plot.
- `AUTO_ADVANCE`: move to next trial after labeling.
- `WINDOW_TITLE`: GUI window title.
- `SAMPLE_RATE_HZ`: sample rate used to build time axis.
- `TRIAL_VIEW_SECONDS`: x-axis window length.

### `gpias_labeler/data_loader.py`
Loads trial data from `.npy` and returns `(trials, trial_type)`.

Current assumptions:

1. If loaded object is dict-like: use `data['data']` and `data['gap']`.
2. Otherwise fallback assumes a 2D array where the last column is `trial_type` and all previous columns are signal samples.

### `gpias_labeler/gui.py`
Main labeling interface (`LabelGUI`):

- Plots selected trial waveform.
- Draws stimulus-time marker.
- Displays trial info, label state, and overall progress.
- Randomizes presentation order while preserving original trial index for saved labels.
- Handles keyboard shortcuts and clickable buttons.
- Calls `LabelManager` to record labels and save output.

### `gpias_labeler/label_manager.py`
Label persistence helper:

- `add_label(...)` stores annotation entries in memory.
- `save(...)` writes entries to CSV (`labels.csv` by default).
- Each row includes trial index, label, trial type, expert ID, file name, and timestamp.

## Installation

## Prerequisites

- Python 3.10+
- Windows, macOS, or Linux with GUI support

## 1) Create and activate a virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

### Windows PowerShell

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 3) Run the app

From the project root:

### Windows PowerShell

```powershell
python main.py
```

### macOS/Linux

```bash
python3 main.py
```

## Usage

1. Select a `.npy` file when prompted.
2. Enter your expert ID.
3. Label each trial.
4. Save and quit to generate `labels.csv` in the current working directory.

## Controls

### Keyboard

- `S`: label as `startle`
- `N`: label as `nonstartle`
- `U`: label as `uncertain`
- `Left`: previous trial
- `Right`: next trial
- `Q`: save and quit

### Mouse buttons

- `Startle (S)`
- `Nonstartle (N)`
- `Uncertain (U)`
- `Prev (←)`
- `Next (→)`
- `Save + Quit (Q)`

## Output format

Saved CSV columns:

- `trial_index` (original index, not randomized display position)
- `label`
- `trial_type`
- `expert_id`
- `file_name`
- `timestamp`

## Notes

- If plots look time-compressed or zoomed, verify `SAMPLE_RATE_HZ` in `gpias_labeler/config.py` matches acquisition sampling rate.
- Randomized trial order changes each run.


