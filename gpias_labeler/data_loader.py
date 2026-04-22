import numpy as np


def load_data(file_path):
    data = np.load(file_path, allow_pickle=True)

    # Assume structure: dictionary-like npy
    # Update later if needed
    if isinstance(data, dict):
        trials = data['data']
        trial_type = data['gap']
    else:
        # fallback assumption
        trials = data[:, :-1]
        trial_type = data[:, -1]

    return trials, trial_type