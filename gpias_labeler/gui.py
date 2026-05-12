import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

try:
    from .config import (
        AUTO_ADVANCE,
        SAMPLE_RATE_HZ,
        STIMULUS_TIME_MS,
        TRIAL_VIEW_SECONDS,
        WINDOW_TITLE,
    )
except ImportError:
    from config import (
        AUTO_ADVANCE,
        SAMPLE_RATE_HZ,
        STIMULUS_TIME_MS,
        TRIAL_VIEW_SECONDS,
        WINDOW_TITLE,
    )


class LabelGUI(QWidget):
    def __init__(self, trials, trial_types, label_manager, initial_labels=None):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.trials = np.asarray(trials)
        self.trial_types = np.asarray(trial_types)
        self.label_manager = label_manager
        self.current_labels = initial_labels if initial_labels is not None else {}
        # Track randomized display order separately from original trial indices.
        self.presentation_order = np.random.permutation(len(self.trials))
        self.index = 0

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(900, 500)

        self.layout = QVBoxLayout()
        self.info = QLabel()
        self.layout.addWidget(self.info)

        self.shortcut_hint = QLabel(
            "Shortcuts: S=startle, N=nonstartle, U=toggle uncertain, Left/Right=navigate, Q=quit"
        )
        self.layout.addWidget(self.shortcut_hint)

        self.label_status = QLabel()
        self.layout.addWidget(self.label_status)

        self.progress_status = QLabel()
        self.layout.addWidget(self.progress_status)

        self.figure = Figure(figsize=(9, 4), tight_layout=True)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        controls = QHBoxLayout()

        startle_btn = QPushButton("Startle (S)")
        startle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        startle_btn.clicked.connect(lambda: self.label("startle"))
        controls.addWidget(startle_btn)

        nonstartle_btn = QPushButton("Nonstartle (N)")
        nonstartle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        nonstartle_btn.clicked.connect(lambda: self.label("nonstartle"))
        controls.addWidget(nonstartle_btn)

        self.uncertain_cb = QCheckBox("Uncertain (U)")
        self.uncertain_cb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.uncertain_cb.stateChanged.connect(self._on_uncertain_changed)
        controls.addWidget(self.uncertain_cb)

        prev_btn = QPushButton("Prev (←)")
        prev_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        prev_btn.clicked.connect(self.prev_trial)
        controls.addWidget(prev_btn)

        next_btn = QPushButton("Next (→)")
        next_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        next_btn.clicked.connect(self.next_trial)
        controls.addWidget(next_btn)

        save_btn = QPushButton("Save")
        save_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        save_btn.clicked.connect(self.label_manager.save)
        controls.addWidget(save_btn)

        quit_btn = QPushButton("Quit (Q)")
        quit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        quit_btn.clicked.connect(self.save_and_close)
        controls.addWidget(quit_btn)

        self.layout.addLayout(controls)

        self.setLayout(self.layout)
        self.setFocus()
        self.update_plot()

    def update_plot(self):
        self.ax.clear()

        if len(self.trials) == 0:
            self.info.setText("No trials found in selected file.")
            self.label_status.setText("")
            self.progress_status.setText("Progress: 0/0 labeled")
            self.canvas.draw()
            return

        original_index = int(self.presentation_order[self.index])
        trial = np.asarray(self.trials[original_index]).ravel()
        trial_type = self.trial_types[original_index]
        current_label = self.current_labels.get(original_index)
        max_samples = min(len(trial), int(SAMPLE_RATE_HZ * TRIAL_VIEW_SECONDS))

        if max_samples <= 0:
            self.info.setText("Current trial has no samples.")
            self.canvas.draw()
            return

        visible_trial = trial[:max_samples]
        time_axis = np.arange(max_samples, dtype=float) / float(SAMPLE_RATE_HZ)
        stimulus_time_s = STIMULUS_TIME_MS / 1000.0

        self.ax.plot(time_axis, visible_trial)
        self.ax.axvline(stimulus_time_s, linestyle="--")
        self.ax.set_xlim(0, TRIAL_VIEW_SECONDS)
        self.ax.set_xlabel("Time (s)")
        self.info.setText(
            f"Trial {self.index + 1}/{len(self.trials)} (randomized) | Original: {original_index + 1}"
        )

        self.uncertain_cb.blockSignals(True)
        if current_label:
            self.uncertain_cb.setChecked(current_label["uncertain"])
            label_text = current_label["label"]
            if current_label["uncertain"]:
                label_text += " (uncertain)"
            self.label_status.setText(f"Labeled: {label_text}")
            self.label_status.setStyleSheet("color: #1b5e20; font-weight: 600;")
        else:
            self.uncertain_cb.setChecked(False)
            self.label_status.setText("Not labeled yet")
            self.label_status.setStyleSheet("color: #b71c1c; font-weight: 600;")
        self.uncertain_cb.blockSignals(False)

        self.progress_status.setText(
            f"Progress: {len(self.current_labels)}/{len(self.trials)} labeled"
        )

        self.canvas.draw()

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key.Key_S:
            self.label("startle")
        elif key == Qt.Key.Key_N:
            self.label("nonstartle")
        elif key == Qt.Key.Key_U:
            self.uncertain_cb.setChecked(not self.uncertain_cb.isChecked())
        elif key == Qt.Key.Key_Right:
            self.next_trial()
        elif key == Qt.Key.Key_Left:
            self.prev_trial()
        elif key == Qt.Key.Key_Q:
            self.save_and_close()

    def label(self, label):
        if len(self.trials) == 0:
            return

        original_index = int(self.presentation_order[self.index])
        uncertain = self.uncertain_cb.isChecked()
        self.label_manager.add_label(original_index, label, uncertain)
        self.current_labels[original_index] = {"label": label, "uncertain": uncertain}
        self.update_plot()

        if AUTO_ADVANCE:
            self.next_trial()

    def _on_uncertain_changed(self, _state):
        if len(self.trials) == 0:
            return
        original_index = int(self.presentation_order[self.index])
        if original_index not in self.current_labels:
            return
        uncertain = self.uncertain_cb.isChecked()
        entry = self.current_labels[original_index]
        entry["uncertain"] = uncertain
        self.label_manager.add_label(original_index, entry["label"], uncertain)
        self.update_plot()

    def save_and_close(self):
        self.label_manager.save()
        self.close()

    def next_trial(self):
        if self.index < len(self.trials) - 1:
            self.index += 1
            self.update_plot()

    def prev_trial(self):
        if self.index > 0:
            self.index -= 1
            self.update_plot()