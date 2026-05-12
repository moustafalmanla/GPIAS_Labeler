import pandas as pd


class LabelManager:
    def __init__(self, file_name, expert_id, output_path="labels.csv"):
        self.file_name = file_name
        self.expert_id = expert_id
        self.output_path = output_path
        self.labels = []

    def add_label(self, trial_index, label, uncertain=False):
        entry = {
            "trial_index": trial_index,
            "label": label,
            "uncertain": uncertain,
            "expert_id": self.expert_id,
        }

        self.labels.append(entry)

    def save(self):
        df = pd.DataFrame(self.labels)
        if not df.empty:
            df = df.drop_duplicates(subset=["trial_index"], keep="last")
        df.to_csv(self.output_path, index=False)