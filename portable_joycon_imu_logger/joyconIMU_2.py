import json
import time
import argparse
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pyjoycon import JoyCon, get_L_id, get_R_id

POLL_RATE_HZ = 50
HISTORY_LENGTH = 100  # Num data points to keep for plot


def generate_default_filename():
    start_time = datetime.now()
    log_timestamp = start_time.strftime('%H_%M_%d_%m_%Y.json')
    return f"joycon_log_{log_timestamp}"


def log_all_data(status_data, joycon_side, log_file):
    timestamp = int(time.time() * 1000)  # Unix timestamp in ms
    data = {
        "timestamp": timestamp,
        "joycon": joycon_side,
        "status": status_data
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(data) + "\n")


def log_motion_data(status_data, joycon_side, log_file):
    timestamp = int(time.time() * 1000)
    data = {
        "timestamp": timestamp,
        "joycon": joycon_side,
        "motion": {
            "accel": status_data.get("accel", {}),
            "gyro": status_data.get("gyro", {})
        }
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(data) + "\n")


def print_motion_data(status_data, joycon_side):
    accel = status_data.get("accel", {})
    gyro = status_data.get("gyro", {})
    print(f"[{joycon_side.capitalize()} Joy-Con] "
          f"Accel: X: {accel.get('x')}, Y: {accel.get('y')}, Z: {accel.get('z')}    |    "
          f"Gyro: X: {gyro.get('x')}, Y: {gyro.get('y')}, Z: {gyro.get('z')}")


def parse_args():
    parser = argparse.ArgumentParser(description="Joy-Con Motion Logger and Visualizer")
    parser.add_argument("--log_mode",
                        choices=["motion", "all"],
                        default="motion",
                        help="Specify what type of data to log: motion or all (default: motion)")
    parser.add_argument("--log_file",
                        default=None,
                        help="Custom log file name (default: timestamp-based name)")
    return parser.parse_args()


def init_plot():
    fig, ax = plt.subplots(2, 1, figsize=(10, 6))

    lines = {
        'accel': {
            'x': ax[0].plot([], [], label='Accel X')[0],
            'y': ax[0].plot([], [], label='Accel Y')[0],
            'z': ax[0].plot([], [], label='Accel Z')[0],
        },
        'gyro': {
            'x': ax[1].plot([], [], label='Gyro X')[0],
            'y': ax[1].plot([], [], label='Gyro Y')[0],
            'z': ax[1].plot([], [], label='Gyro Z')[0],
        }
    }

    ax[0].set_title("Accelerometer Data")
    ax[1].set_title("Gyroscope Data")

    for a in ax:
        a.set_xlim(0, HISTORY_LENGTH)
        a.set_ylim(-2000, 2000)
        a.legend()
        a.grid(True)

    plt.tight_layout()
    return fig, ax, lines


def main():
    args = parse_args()

    log_file = args.log_file or generate_default_filename()
    
    # Either log motion data (default) or all data
    log_func = log_motion_data if args.log_mode == "motion" else log_all_data

    joycons = []
    data_history = {
        "accel": {"x": [], "y": [], "z": []},
        "gyro": {"x": [], "y": [], "z": []}
    }

    left_id = get_L_id()
    right_id = get_R_id()

    if left_id[0]:
        print("Left Joy-Con connected.")
        joycons.append(("left", JoyCon(*left_id)))

    if right_id[0]:
        print("Right Joy-Con connected.")
        joycons.append(("right", JoyCon(*right_id)))

    if not joycons:
        print("No Joy-Cons connected.")
        return

    fig, ax, lines = init_plot()

    def update(frame):
        for joycon_side, joycon in joycons:
            status = joycon.get_status()
            log_func(status, joycon_side, log_file)
            print_motion_data(status, joycon_side)

            # We'll just plot the first connected Joy-Con for simplicity
            if joycon_side == 'right':
                accel = status.get("accel", {})
                gyro = status.get("gyro", {})

                for axis in ['x', 'y', 'z']:
                    data_history['accel'][axis].append(accel.get(axis, 0))
                    data_history['gyro'][axis].append(gyro.get(axis, 0))

                    if len(data_history['accel'][axis]) > HISTORY_LENGTH:
                        data_history['accel'][axis].pop(0)
                        data_history['gyro'][axis].pop(0)

                x_vals = list(range(len(data_history['accel']['x'])))

                # Correct: assign accel data to accel lines, gyro data to gyro lines
                for axis in ['x', 'y', 'z']:
                    lines['accel'][axis].set_data(x_vals, data_history['accel'][axis])
                    lines['gyro'][axis].set_data(x_vals, data_history['gyro'][axis])

        return [lines[g][a] for g in ['accel', 'gyro'] for a in ['x', 'y', 'z']]

    ani = FuncAnimation(fig, update, interval=1000 / POLL_RATE_HZ, blit=False)
    print("Starting real-time plot. Press Ctrl+C to exit.")
    try:
        plt.show()
    except KeyboardInterrupt:
        print("\nExiting and stopping real-time plot.")


if __name__ == "__main__":
    main()