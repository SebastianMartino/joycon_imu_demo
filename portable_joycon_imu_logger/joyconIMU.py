import json
import time
from datetime import datetime, timezone
from pyjoycon import JoyCon, get_R_id, get_L_id

POLL_RATE_HZ = 50

# Create log filename with current timestamp
start_time = datetime.now()
log_timestamp = start_time.strftime('%H_%M_%d_%m_%Y.json')
LOG_FILE = f"joycon_log_{log_timestamp}.json"


def log_all_data(status_data, joycon_side):
    timestamp = int(time.time() * 1000)  # Unix timestamp
    #timestamp = datetime.now(timezone.utc).isoformat()
    imu_data = {
        "timestamp": timestamp,
        "joycon": joycon_side,
        "status": status_data
    }

    with open(LOG_FILE, "w+") as f:
        f.write(json.dumps(imu_data) + "\n")

def log_motion_data(status_data, joycon_side):
    timestamp = int(time.time() * 1000)  # Unix timestamp
    #timestamp = datetime.now(timezone.utc).isoformat()
    imu_data = {
        "timestamp": timestamp,
        "joycon": joycon_side,
        "motion": {
            "accel": status_data.get("accel", {}),
            "gyro": status_data.get("gyro", {})
        }
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(imu_data) + "\n")


def print_motion_data(status_data, joycon_side):
    accel = status_data.get("accel", {})
    gyro = status_data.get("gyro", {})
    print(f"[{joycon_side.capitalize()} Joy-Con] "
          f"Gyro: X: {gyro.get('x')}, Y: {gyro.get('y')}, Z: {gyro.get('z')}")
          f"Accel: X: {accel.get('x')}, Y: {accel.get('y')}, Z: {accel.get('z')}    |    "


def main():
    joycons = []

    left_id = get_L_id()
    right_id = get_R_id()

    if left_id[0] != None:
        print("Left Joy-Con connected.")
        joycons.append(("left", JoyCon(*left_id)))

    if right_id[0] != None:
        print("Right Joy-Con connected.")
        joycons.append(("right", JoyCon(*right_id)))

    if not joycons:
        print("No Joy-Cons connected")
        return

    interval = 1.0 / POLL_RATE_HZ
    next_time = time.perf_counter()

    try:
        while True:
            for joycon_side, joycon in joycons:
                status = joycon.get_status()
                #log_all_data(status, joycon_side)
                log_motion_data(status, joycon_side)
                print_motion_data(status, joycon_side)

            next_time += interval
            sleep_time = next_time - time.perf_counter()

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_time = time.perf_counter()
    except KeyboardInterrupt:
        print("\nLogging stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()


