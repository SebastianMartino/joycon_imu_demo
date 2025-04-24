import json
import argparse
import matplotlib.pyplot as plt
from collections import defaultdict

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


def plot_joycon_motion(side, motion_data):
    """Plot motion data for a given Joy-Con side."""
    timestamps = motion_data["timestamp"]
    time_sec = [(t - timestamps[0]) / 1000.0 for t in timestamps]

    accel = motion_data["accel"]
    gyro = motion_data["gyro"]

    fig, axs = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f"{side.capitalize()} Joy-Con Motion Data")

    # Accelerometer
    axs[0].plot(time_sec, accel["x"], label="Accel X", color="r")
    axs[0].plot(time_sec, accel["y"], label="Accel Y", color="g")
    axs[0].plot(time_sec, accel["z"], label="Accel Z", color="b")
    axs[0].set_ylabel("Acceleration")
    axs[0].set_title("Accelerometer")
    axs[0].legend()
    axs[0].grid(True)

    # Gyroscope
    axs[1].plot(time_sec, gyro["x"], label="Gyro X", color="r")
    axs[1].plot(time_sec, gyro["y"], label="Gyro Y", color="g")
    axs[1].plot(time_sec, gyro["z"], label="Gyro Z", color="b")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("Rotation Rate")
    axs[1].set_title("Gyroscope")
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
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