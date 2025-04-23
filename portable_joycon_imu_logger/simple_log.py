import time
from pyjoycon import *

def main():
    # Get the ID of the right Joy-Con (you can also use get_L_id() for the left)
    joycon_id = get_R_id()
    if not joycon_id:
        print("Could not find a connected Joy-Con (Right).")
        return

    joycon = GyroTrackingJoyCon(*joycon_id)

    print("Tracking Joy-Con gyroscope (Ctrl+C to stop)...\n")

    try:
        while True:
            print("Gyro Pointer:   ", joycon.pointer)
            print("Gyro Rotation:  ", joycon.rotation)
            print("Gyro Direction: ", joycon.direction)
            print()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Optional cleanup if needed
        pass


if __name__ == "__main__":
    main()


