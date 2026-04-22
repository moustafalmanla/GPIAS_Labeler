import pandas as pd
from datetime import datetime


class LabelManager:
    def __init__(self, file_name, expert_id):
        self.file_name = file_name
        self.expert_id = expert_id
        self.labels = []

    def add_label(self, trial_index, label, trial_type):
        entry = {
            "trial_index": trial_index,
            "label": label,
            "trial_type": trial_type,
            "expert_id": self.expert_id,
            "file_name": self.file_name,
            "timestamp": datetime.now()
        }

        self.labels.append(entry)

    def save(self, output_path="labels.csv"):
        df = pd.DataFrame(self.labels)
        df.to_csv(output_path, index=False)