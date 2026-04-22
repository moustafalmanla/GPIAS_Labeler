import sys
import os

from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog

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

    label_manager = LabelManager(
        os.path.basename(file_path),
        expert_id
    )

    window = LabelGUI(trials, trial_types, label_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()