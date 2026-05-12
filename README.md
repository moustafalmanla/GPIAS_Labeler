# GPIAS Labeler

GPIAS Labeler is a desktop annotation tool for labeling startle-response trials from `.npy` files. It presents trials in randomized order, lets the annotator mark each one as `startle` or `nonstartle`, supports a separate `uncertain` flag, and saves progress to a CSV next to the source data file.

## What the software does

- Opens a NumPy `.npy` file selected from a file dialog.
- Prompts for an expert ID before labeling starts.
- Loads either legacy trial matrices or xyz movement data.
- For xyz data, low-pass filters the first three axes and converts them to an RMS movement trace.
- Displays one trial at a time in a Qt + Matplotlib GUI.
- Randomizes presentation order while preserving original trial indices in saved output.
- Supports resuming from an existing `<input_stem>_labels.csv` file.
- Tracks a primary label (`startle` or `nonstartle`) plus an `uncertain` checkbox.
- Saves labels without quitting, or saves and quits.

## Project structure

### `main.py`

Small launcher script that imports and runs `main()` from `gpias_labeler/Labeler_main.py`.

### `gpias_labeler/Labeler_main.py`

Application entry point:

- Creates `QApplication`.
- Prompts for the input `.npy` file.
- Loads trial data with `load_data()`.
- Prompts for the expert ID.
- Chooses an output file named `<input_stem>_labels.csv`.
- If that file already exists, offers to resume previous labels.
- Creates `LabelManager` and `LabelGUI`.

### `gpias_labeler/config.py`

Runtime settings:

- `STIMULUS_TIME_MS`: vertical marker location in the plot.
- `AUTO_ADVANCE`: automatically move to the next trial after labeling.
- `WINDOW_TITLE`: application window title.
- `SAMPLE_RATE_HZ`: sample rate used for the time axis and filtering.
- `TRIAL_VIEW_SECONDS`: visible x-axis window length.
- `RMS_SENSITIVITY`: scaling factor for xyz-to-RMS conversion.
- `LOWPASS_CUTOFF_HZ`: low-pass cutoff used before RMS conversion.
- `LOWPASS_ORDER`: Butterworth filter order.

### `gpias_labeler/data_loader.py`

Loads data from `.npy` and returns `(trials, trial_type)`.

Supported input formats:

1. Dictionary-like saved payloads with:
   - `data`: trial samples
   - `gap`: per-trial type metadata
2. Legacy 2D matrices where:
   - all columns except the last are trial samples
   - the last column stores `trial_type`
3. xyz / multichannel arrays where the first three inferred channels are treated as x, y, z and converted to a single RMS trace per trial

xyz preprocessing path:

- low-pass filters x, y, and z with SciPy Butterworth filtering
- scales by `RMS_SENSITIVITY`
- computes `sqrt((x/s)^2 + (y/s)^2 + (z/s)^2)`

### `gpias_labeler/gui.py`

Main labeling interface:

- Displays the current trial waveform and stimulus marker.
- Shows randomized trial position and original trial index.
- Shows current label state and overall progress.
- Provides buttons and keyboard shortcuts for labeling and navigation.
- Lets the user toggle `uncertain` independently of the main label.
- Supports manual save without closing the app.

### `gpias_labeler/label_manager.py`

CSV persistence helper:

- Stores labels in memory while the session is running.
- Keeps the latest entry per `trial_index` when saving.
- Writes the output CSV to the configured output path.

## Installation

### Prerequisites

- Python 3.10+
- Windows, macOS, or Linux with GUI support

### 1) Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

#### Windows PowerShell

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### macOS/Linux

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Dependencies currently used by the app:

- `numpy`
- `pandas`
- `matplotlib`
- `PySide6`
- `scipy`

### 3) Run the app

From the project root:

#### Windows PowerShell

```powershell
python main.py
```

#### macOS/Linux

```bash
python3 main.py
```

## Usage

1. Launch the app.
2. Select a `.npy` file.
3. Enter the expert ID.
4. If a matching `<input_stem>_labels.csv` already exists, choose whether to resume from it.
5. Label each trial as `startle` or `nonstartle`.
6. Toggle `uncertain` for any labeled trial that needs it.
7. Use `Save` to write progress at any time, or `Quit` to save and close.

## Controls

### Keyboard

- `S`: label as `startle`
- `N`: label as `nonstartle`
- `U`: toggle `uncertain` for the current trial
- `Left`: previous trial
- `Right`: next trial
- `Q`: save and quit

### GUI controls

- `Startle (S)`
- `Nonstartle (N)`
- `Uncertain (U)`
- `Prev`
- `Next`
- `Save`
- `Quit (Q)`

## Output format

For an input file such as `session_01.npy`, labels are written to `session_01_labels.csv`.

Saved CSV columns:

- `trial_index`: original trial index, not the randomized display position
- `label`: `startle` or `nonstartle`
- `uncertain`: boolean flag
- `expert_id`: annotator ID entered at startup

When the same trial is labeled multiple times, the last label for that `trial_index` is the one kept on save.

## Notes

- Trial presentation order is randomized separately for each run.
- Resume uses the previously saved CSV for the selected input file only.
- If the time axis looks wrong, check `SAMPLE_RATE_HZ` in `gpias_labeler/config.py`.
- If xyz input is used, only the first three inferred channels are used for RMS conversion.
