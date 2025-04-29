import json
import argparse
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
from scipy.signal import butter, filtfilt

def parse_log_file(filepath):
    """Parse a Joy-Con JSON motion log file."""
    data = defaultdict(lambda: {
        "timestamp": [],
        "accel": {"x": [], "y": [], "z": []},
        "gyro": {"x": [], "y": [], "z": []},
    })

    with open(filepath, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                side = entry.get("joycon")
                motion = entry.get("motion")

                if side and motion:
                    data[side]["timestamp"].append(entry["timestamp"])
                    for axis in ['x', 'y', 'z']:
                        data[side]["accel"][axis].append(motion.get("accel", {}).get(axis, 0))
                        data[side]["gyro"][axis].append(motion.get("gyro", {}).get(axis, 0))
            except Exception as e:
                print(f"Warning: skipping line due to error: {e}")

    return data

def apply_low_pass_filter(data, fs, cutoff, filter_order):

    # Calculate the Nyquist frequency
    nyquist = 0.5 * fs# 
    # Normalize the cutoff frequency with respect to Nyquist
    normal_cutoff = cutoff / nyquist

    # Design the Butterworth low-pass filter
    b, a = butter(filter_order, normal_cutoff, btype='low', analog=False)

    # Apply filter to each column if multi-dimensional, otherwise to the whole array
    filtered_data = filtfilt(b, a, data, axis=0)

    return filtered_data

def plot_joycon_motion(side, motion_data):
    """Plot motion data for a given Joy-Con side."""
    timestamps = motion_data["timestamp"]
    time_sec = [(t - timestamps[0]) / 1000.0 for t in timestamps]
    time_sec = np.array(time_sec)
    fs = 1/np.mean(np.diff(time_sec))

    accel = motion_data["accel"]
    gyro = motion_data["gyro"]

    cal_constant = 0.0001694 * 2 * np.pi # for gyro
    acc_cal_constant = 16000 / 65536 / 1000    
    
    # filter
    filter_order = 4
    cutoff_freq = 6 #hz
    accel['x'] = apply_low_pass_filter(data= accel['x'], fs= fs, cutoff=cutoff_freq, filter_order = filter_order) * acc_cal_constant
    accel['y'] = apply_low_pass_filter(data= accel['y'], fs= fs, cutoff=cutoff_freq, filter_order = filter_order) * acc_cal_constant
    accel['z'] = apply_low_pass_filter(data= accel['z'], fs= fs, cutoff=cutoff_freq, filter_order = filter_order) * acc_cal_constant

    gyro['x'] = apply_low_pass_filter(data= gyro['x'], fs= fs, cutoff=cutoff_freq, filter_order = filter_order) * cal_constant
    gyro['y'] = apply_low_pass_filter(data= gyro['y'], fs= fs, cutoff=cutoff_freq, filter_order = filter_order) * cal_constant
    gyro['z'] = apply_low_pass_filter(data= gyro['z'], fs= fs, cutoff=cutoff_freq, filter_order = filter_order) * cal_constant

    gyro_l2 = np.sqrt(
        np.square(gyro['x']) +
        np.square(gyro['y']) +
        np.square(gyro['z'])
    )

   # Create a dictionary of sums for each axis
    axis_sums = {
        'x': np.sum(np.abs(gyro['x'])),
        'y': np.sum(np.abs(gyro['y'])),
        'z': np.sum(np.abs(gyro['z']))
    }

    # Find the axis with the maximum sum
    max_axis = max(axis_sums, key=axis_sums.get)
    target_gyro = gyro[max_axis]

    from scipy.signal import find_peaks
    peaks, _ = find_peaks(target_gyro, height=1.5, distance=fs*0.5)
    peaks = peaks.astype(int)

    fig, axs = plt.subplots(2, 1, figsize=(8, 4), sharex=True, gridspec_kw={'height_ratios': [1.5, 1]})
    fig.suptitle(f"Number of kicks: {len(peaks)}")

    # Gyroscope
    axs[0].plot(time_sec, target_gyro, label='sensor\nsignal')
    axs[0].scatter(time_sec[peaks], target_gyro[peaks], color='r', marker='o', label='peaks')
    axs[0].set_ylabel("Rad/s")
    axs[0].set_title("Leg angular velocity")
    axs[0].legend(frameon=False)
    axs[0].spines['right'].set_visible(False)
    axs[0].spines['top'].set_visible(False)

    # Get positions and normalized heights of bars
    bar_times = time_sec[peaks]
    bar_heights = (gyro_l2[peaks] / np.max(gyro_l2[peaks])) * 100
    axs[1].bar(bar_times, bar_heights, width=0.5, alpha=0.7, color='r', label='Kinetic\nEnergy')
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("Kicking \nkinetic energy (%)")
    axs[1].spines['right'].set_visible(False)
    axs[1].spines['top'].set_visible(False)
    axs[1].legend(frameon=False)

    axs[0].set_xlim([0, np.max(time_sec)+1])
    axs[1].set_xlim([0, np.max(time_sec)+1])

    offset = np.max(bar_heights) * 0.05
    for x, h in zip(bar_times, bar_heights):
        axs[1].text(x, h + offset, f"{h:.0f}%", ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot Joy-Con motion data from a log file")
    parser.add_argument("log_file", help="Path to joycon log file (.json)")
    args = parser.parse_args()

    data = parse_log_file(args.log_file)

    if not data:
        print("No motion data found in the file.")
        return

    for side in data:
        if data[side]["timestamp"]:
            plot_joycon_motion(side, data[side])
        else:
            print(f"No motion data for {side} Joy-Con.")


if __name__ == "__main__":
    main()