import math

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, MaxNLocator
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


class ZoomableFigureCanvas(FigureCanvas):
    def __init__(self, figure, zoom_callback, pan_callback):
        super().__init__(figure)
        self._zoom_callback = zoom_callback
        self._pan_callback = pan_callback
        self._drag_active = False
        self._drag_start_x = 0.0
        self._drag_start_start_seconds = 0.0
        self._drag_button = Qt.MouseButton.NoButton

    def wheelEvent(self, event):
        if self._zoom_callback is None:
            return super().wheelEvent(event)

        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom_callback(0.8)
        elif delta < 0:
            self._zoom_callback(1.25)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pan_callback is not None:
            self._drag_active = True
            self._drag_button = event.button()
            self._drag_start_x = event.position().x()
            self._drag_start_start_seconds = self._pan_callback("get_start")
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and (event.buttons() & Qt.MouseButton.LeftButton):
            dx_pixels = event.position().x() - self._drag_start_x
            self._pan_callback("drag", dx_pixels, self._drag_start_start_seconds)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_active and event.button() == self._drag_button:
            self._drag_active = False
            self._drag_button = Qt.MouseButton.NoButton
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class LabelGUI(QWidget):
    def __init__(self, trials, trial_types, label_manager, initial_labels=None, on_load_file=None):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.on_load_file = on_load_file
        self.trials = np.asarray(trials)
        self.trial_types = np.asarray(trial_types)
        self.y_max = math.ceil(self.trials.max()) if len(self.trials) > 0 else 1
        self.label_manager = label_manager
        self.current_labels = initial_labels if initial_labels is not None else {}
        # Track randomized display order separately from original trial indices.
        self.presentation_order = np.random.permutation(len(self.trials))
        self.index = 0
        self.view_start_seconds = 0.0
        self.view_span_seconds = TRIAL_VIEW_SECONDS
        self.min_view_span_seconds = max(0.01, 50.0 / SAMPLE_RATE_HZ)

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(900, 500)

        self.layout = QVBoxLayout()
        self.info = QLabel()
        self.layout.addWidget(self.info)

        self.shortcut_hint = QLabel(
            "Shortcuts: S=startle, N=nonstartle, U=toggle uncertain, Left/Right=navigate, Q=quit; mouse wheel or zoom buttons to zoom"
        )
        self.layout.addWidget(self.shortcut_hint)

        self.label_status = QLabel()
        self.layout.addWidget(self.label_status)

        self.progress_status = QLabel()
        self.layout.addWidget(self.progress_status)

        self.figure = Figure(figsize=(9, 4), tight_layout=True)
        self.ax = self.figure.add_subplot(111)
        self.canvas = ZoomableFigureCanvas(self.figure, self.zoom_view, self.pan_view)
        self.layout.addWidget(self.canvas)

        controls = QHBoxLayout()

        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        zoom_out_btn.clicked.connect(lambda: self.zoom_view(1.25))
        controls.addWidget(zoom_out_btn)

        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        zoom_in_btn.clicked.connect(lambda: self.zoom_view(0.8))
        controls.addWidget(zoom_in_btn)

        reset_zoom_btn = QPushButton("Reset Zoom")
        reset_zoom_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        controls.addWidget(reset_zoom_btn)

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

        upload_file_btn = QPushButton("Upload New File")
        upload_file_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        upload_file_btn.clicked.connect(self.upload_new_file)
        controls.addWidget(upload_file_btn)

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
        current_label = self.current_labels.get(original_index)
        total_samples = len(trial)
        trial_duration_seconds = total_samples / float(SAMPLE_RATE_HZ)
        view_span_seconds = min(self.view_span_seconds, trial_duration_seconds)
        max_start_seconds = max(0.0, trial_duration_seconds - view_span_seconds)
        view_start_seconds = min(max(self.view_start_seconds, 0.0), max_start_seconds)
        view_end_seconds = view_start_seconds + view_span_seconds
        start_sample = max(0, int(view_start_seconds * SAMPLE_RATE_HZ))
        end_sample = min(total_samples, int(math.ceil(view_end_seconds * SAMPLE_RATE_HZ)))

        if end_sample <= start_sample:
            self.info.setText("Current trial has no samples.")
            self.label_status.setText("")
            self.progress_status.setText(f"Progress: {len(self.current_labels)}/{len(self.trials)} labeled")
            self.canvas.draw()
            return

        visible_trial = trial[start_sample:end_sample]
        time_axis = np.arange(start_sample, end_sample, dtype=float) / float(SAMPLE_RATE_HZ)
        stimulus_time_s = STIMULUS_TIME_MS / 1000.0

        self.ax.plot(time_axis, visible_trial)
        self.ax.axvline(stimulus_time_s, linestyle="--")
        self.ax.set_xlim(view_start_seconds, view_end_seconds)
        self.ax.set_ylim(0, self.y_max)
        self.ax.set_xlabel("Time (s)")
        self.ax.xaxis.set_major_locator(MaxNLocator(nbins=12))
        self.ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        self.ax.tick_params(axis="x", which="major", length=6)
        self.ax.tick_params(axis="x", which="minor", length=3)
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

    def zoom_view(self, factor):
        if len(self.trials) == 0:
            return

        trial = np.asarray(self.trials[int(self.presentation_order[self.index])]).ravel()
        if len(trial) == 0:
            return

        trial_duration_seconds = len(trial) / float(SAMPLE_RATE_HZ)
        current_span = min(self.view_span_seconds, trial_duration_seconds)
        new_span = max(self.min_view_span_seconds, min(trial_duration_seconds, current_span * factor))

        current_center = self.view_start_seconds + (current_span / 2.0)
        new_start = current_center - (new_span / 2.0)
        new_start = max(0.0, min(new_start, max(0.0, trial_duration_seconds - new_span)))

        self.view_span_seconds = new_span
        self.view_start_seconds = new_start
        self.update_plot()

    def pan_view(self, action, dx_pixels=None, drag_start_seconds=None):
        if len(self.trials) == 0:
            return 0.0

        if action == "get_start":
            return self.view_start_seconds

        if action != "drag" or dx_pixels is None or drag_start_seconds is None:
            return self.view_start_seconds

        trial = np.asarray(self.trials[int(self.presentation_order[self.index])]).ravel()
        if len(trial) == 0:
            return self.view_start_seconds

        trial_duration_seconds = len(trial) / float(SAMPLE_RATE_HZ)
        current_span = min(self.view_span_seconds, trial_duration_seconds)
        if current_span >= trial_duration_seconds:
            self.view_start_seconds = 0.0
            self.update_plot()
            return self.view_start_seconds

        pixels = max(1, self.canvas.width())
        seconds_per_pixel = current_span / float(pixels)
        new_start = drag_start_seconds - (dx_pixels * seconds_per_pixel)
        new_start = max(0.0, min(new_start, max(0.0, trial_duration_seconds - current_span)))

        self.view_start_seconds = new_start
        self.update_plot()
        return self.view_start_seconds

    def reset_zoom(self):
        self.view_start_seconds = 0.0
        self.view_span_seconds = TRIAL_VIEW_SECONDS
        self.update_plot()

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

    def upload_new_file(self):
        if self.on_load_file is not None:
            self.label_manager.save()
            self.on_load_file()

    def reset_with_new_data(self, trials, trial_types, label_manager, initial_labels=None):
        """Reset the GUI with new trial data and label manager."""
        self.trials = np.asarray(trials)
        self.trial_types = np.asarray(trial_types)
        self.y_max = math.ceil(self.trials.max()) if len(self.trials) > 0 else 1
        self.label_manager = label_manager
        self.current_labels = initial_labels if initial_labels is not None else {}
        self.presentation_order = np.random.permutation(len(self.trials))
        self.index = 0
        self.view_start_seconds = 0.0
        self.view_span_seconds = TRIAL_VIEW_SECONDS
        self.update_plot()

    def next_trial(self):
        if self.index < len(self.trials) - 1:
            self.index += 1
            self.view_start_seconds = 0.0
            self.update_plot()

    def prev_trial(self):
        if self.index > 0:
            self.index -= 1
            self.view_start_seconds = 0.0
            self.update_plot()