import sys
import os

import pandas as pd
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox

try:
    from .data_loader import load_data
    from .label_manager import LabelManager
    from .gui import LabelGUI
except ImportError:
    from data_loader import load_data
    from label_manager import LabelManager
    from gui import LabelGUI


def main():
    app = QApplication(sys.argv)

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select NPY File",
        "",
        "NumPy Files (*.npy)"
    )

    if not file_path:
        return

    trials, trial_types = load_data(file_path)

    expert_id, ok = QInputDialog.getText(None, "Expert ID", "Enter expert ID:")
    if not ok:
        return
    expert_id = expert_id.strip() or "unknown"

    stem = os.path.splitext(file_path)[0]
    output_path = stem + "_labels.csv"

    label_manager = LabelManager(
        os.path.basename(file_path),
        expert_id,
        output_path,
    )

    initial_labels = {}
    if os.path.exists(output_path):
        reply = QMessageBox.question(
            None,
            "Previous labels found",
            f"Previous labels found for this file. Resume?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            df = pd.read_csv(output_path)
            for _, row in df.iterrows():
                idx = int(row["trial_index"])
                uncertain = bool(row["uncertain"])
                initial_labels[idx] = {"label": row["label"], "uncertain": uncertain}
                label_manager.add_label(idx, row["label"], uncertain)

    window = LabelGUI(trials, trial_types, label_manager, initial_labels)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()