import json
import time
import argparse
import os
from datetime import datetime
from pyjoycon import *


def generate_default_log_filename(log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    start_time = datetime.now()
    log_timestamp = start_time.strftime('%H_%M_%d_%m_%Y.json')
    return os.path.join(log_dir, f"joycon_log_{log_timestamp}")

def log_none(status_data, joycon_side, log_file):
    return

def log_all_data(status_data, joycon_side, log_file):
    timestamp = int(time.time() * 1000)
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
          f"Gyro: X: {gyro.get('x')}, Y: {gyro.get('y')}, Z: {gyro.get('z')}")

def parse_args():
    parser = argparse.ArgumentParser(description="Joy-Con Motion Logger")
    parser.add_argument("--log_mode", choices=["motion", "all", "none"], default="motion",
                        help="Specify what type of data to log: motion, all, or none (default: motion)")
    parser.add_argument("--log_path", default=None,
                        help="Custom log file path (default: logs/<timestamp>.json)")
    parser.add_argument("--poll_rate", type=float, default=50.0,
                        help="Polling rate in Hz for reading Joy-Con data (default: 50Hz)")
    return parser.parse_args()

def is_calibration_button_pressed(buttons, joycon_side):
    shared = buttons.get("shared", {})
    if joycon_side == "left":
        return shared.get("capture", 0) == 1
    elif joycon_side == "right":
        return shared.get("home", 0) == 1
    return False

def main():
    args = parse_args()
    log_path = args.log_path or generate_default_log_filename()

    poll_interval = 1.0 / args.poll_rate
    lamp_pattern = 1

    # Select logging function
    log_func = {
        "motion": log_motion_data,
        "all": log_all_data,
        "none": log_none
    }.get(args.log_mode, log_motion_data)

    joycons = []
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

    # Turn on Joy-Con LEDs
    for joycon_side, joycon in joycons:
        joycon.set_player_lamp_on(lamp_pattern)
        lamp_pattern += 1

    print(f"Polling Joy-Cons at {args.poll_rate:.1f} Hz")

    # Initialize debounce state
    calibration_state = {side: False for side, _ in joycons}

    try:
        while True:
            loop_start = time.perf_counter()

            for joycon_side, joycon in joycons:
                status = joycon.get_status()
                buttons = status.get("buttons", {})

                pressed = is_calibration_button_pressed(buttons, joycon_side)
                if pressed and not calibration_state[joycon_side]:
                    calibration_state[joycon_side] = True

                    print(f"Calibrating {joycon_side} Joy-Con")
                    gyro = status.get("gyro", {})
                    accel = status.get("accel", {})
                    offset_gyro = (
                        gyro.get("x", 0),
                        gyro.get("y", 0),
                        gyro.get("z", 0)
                    )
                    offset_accel = (
                        accel.get("x", 0),
                        accel.get("y", 0),
                        accel.get("z", 0)
                    )
                    joycon.set_gyro_calibration(offset_xyz=offset_gyro)
                    joycon.set_accel_calibration(offset_xyz=offset_accel)
                    print(f"{joycon_side} Joy-Con calibrated.")

                # Reset debounce state when button is released
                if not pressed and calibration_state[joycon_side]:
                    calibration_state[joycon_side] = False

                log_func(status, joycon_side, log_path)
                print_motion_data(status, joycon_side)

            elapsed = time.perf_counter() - loop_start
            sleep_time = poll_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f"Log saved to: {log_path}")


if __name__ == "__main__":
    main()