import numpy as np
from scipy.signal import butter, lfilter

try:
    from .config import LOWPASS_CUTOFF_HZ, LOWPASS_ORDER, RMS_SENSITIVITY, SAMPLE_RATE_HZ
except ImportError:
    from config import LOWPASS_CUTOFF_HZ, LOWPASS_ORDER, RMS_SENSITIVITY, SAMPLE_RATE_HZ


def _butter_lowpass_filter(data, cutoff_hz=LOWPASS_CUTOFF_HZ, fs_hz=SAMPLE_RATE_HZ, order=LOWPASS_ORDER):
    nyquist = 0.5 * float(fs_hz)
    normal_cutoff = float(cutoff_hz) / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    return lfilter(b, a, data, axis=-1)


def _rms_xyz_filtered(xyz_trials, sensitivity=RMS_SENSITIVITY):
    """Compute RMS from xyz data after low-pass filtering and sensitivity scaling.

    xyz_trials shape: (n_trials, 3, n_samples)
    returns: (n_trials, n_samples)
    """
    if xyz_trials.ndim != 3 or xyz_trials.shape[1] < 3:
        raise ValueError(f"Expected xyz trial array shaped (n_trials, 3, n_samples), got {xyz_trials.shape}")

    x_data = xyz_trials[:, 0, :]
    y_data = xyz_trials[:, 1, :]
    z_data = xyz_trials[:, 2, :]

    x_filtered = _butter_lowpass_filter(x_data)
    y_filtered = _butter_lowpass_filter(y_data)
    z_filtered = _butter_lowpass_filter(z_data)

    sensitivity = float(sensitivity)
    if sensitivity == 0:
        raise ValueError("RMS_SENSITIVITY must be non-zero")

    return np.sqrt(
        (x_filtered / sensitivity) ** 2
        + (y_filtered / sensitivity) ** 2
        + (z_filtered / sensitivity) ** 2
    )


def _to_xyz_trials(arr, trial_type):
    """Try to coerce input into (n_trials, 3, n_samples) for xyz processing.

    Returns None if data should be treated as legacy/non-xyz trial matrix.
    """
    if arr.ndim == 3:
        if arr.shape[1] == 3:
            return np.asarray(arr, dtype=float)
        if arr.shape[2] == 3:
            return np.transpose(np.asarray(arr, dtype=float), (0, 2, 1))

        # For arrays with more than 3 channels, use the first three channels
        # from the inferred channel dimension.
        if arr.shape[1] > 3 and arr.shape[2] > arr.shape[1]:
            return np.asarray(arr[:, :3, :], dtype=float)
        if arr.shape[2] > 3 and arr.shape[1] > arr.shape[2]:
            return np.transpose(np.asarray(arr[:, :, :3], dtype=float), (0, 2, 1))

        # Fallback: treat the smaller of the trailing dimensions as channels.
        if arr.shape[1] <= arr.shape[2] and arr.shape[1] >= 3:
            return np.asarray(arr[:, :3, :], dtype=float)
        if arr.shape[2] < arr.shape[1] and arr.shape[2] >= 3:
            return np.transpose(np.asarray(arr[:, :, :3], dtype=float), (0, 2, 1))

        raise ValueError(f"Expected at least 3 axes/channels for xyz data, got shape {arr.shape}")

    if arr.ndim == 2:
        # Keep legacy 2D matrix behavior when trial_type is per-trial vector.
        tt_arr = np.asarray(trial_type)
        if tt_arr.ndim != 0:
            return None

        # Single trial cases.
        if arr.shape[0] == 3:
            return np.asarray(arr[np.newaxis, :, :], dtype=float)
        if arr.shape[1] == 3:
            return np.asarray(arr.T[np.newaxis, :, :], dtype=float)

        # Handle cases like (6, n_samples) or (n_samples, 6): use first xyz channels.
        if arr.shape[0] > 3 and arr.shape[1] > arr.shape[0]:
            return np.asarray(arr[:3, :][np.newaxis, :, :], dtype=float)
        if arr.shape[1] > 3 and arr.shape[0] > arr.shape[1]:
            return np.asarray(arr[:, :3].T[np.newaxis, :, :], dtype=float)

    return None


def _extract_payload(data):
    """Normalize np.load outputs and return (raw_trials, trial_type)."""
    # np.load(dict_saved_with_np.save) often returns a 0-d object array.
    if isinstance(data, np.ndarray) and data.dtype == object and data.ndim == 0:
        try:
            data = data.item()
        except Exception:
            pass

    if isinstance(data, dict):
        raw_trials = data["data"]
        trial_type = data["gap"]
        return raw_trials, trial_type

    # Fallback: legacy format where last column stores trial_type
    raw_trials = data[:, :-1]
    trial_type = data[:, -1]
    return raw_trials, trial_type


def load_data(file_path):
    data = np.load(file_path, allow_pickle=True)
    raw_trials, trial_type = _extract_payload(data)

    arr = np.asarray(raw_trials)
    xyz_trials = _to_xyz_trials(arr, trial_type)

    if xyz_trials is not None:
        trials = _rms_xyz_filtered(xyz_trials)
        tt_arr = np.asarray(trial_type)
        if tt_arr.ndim == 0:
            trial_type = np.asarray([trial_type])
    elif arr.ndim == 2:
        # Legacy scalar-trial matrix path.
        trials = arr
    else:
        raise ValueError(f"Unsupported trial data shape: {arr.shape}")

    return np.asarray(trials), np.asarray(trial_type)
