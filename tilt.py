import freenect
import sys
import termios
import tty
import time

def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

def read_tilt(dev):
    # Refresh motor state
    freenect.update_tilt_state(dev)
    state = freenect.get_tilt_state(dev)

    # Different freenect builds store tilt differently
    if hasattr(state, "tilt_degs"):
        return state.tilt_degs
    if hasattr(state, "tilt_angle"):
        return state.tilt_angle
    return 0

def main():
    ctx = freenect.init()
    dev = freenect.open_device(ctx, 0)
    if dev is None:
        print("ERROR: Kinect not found.")
        return

    print("Kinect Tilt Test")
    print("----------------")
    print("w = tilt up")
    print("s = tilt down")
    print("r = reset to 0")
    print("q = quit\n")

    tilt = read_tilt(dev)
    print(f"Current tilt: {tilt}")

    while True:
        key = get_key()

        if key == 'q':
            freenect.set_tilt_degs(dev, 0)
            print("Exiting…")
            break

        elif key == 'w':
            tilt += 1
            tilt = min(30, tilt)
            freenect.set_tilt_degs(dev, tilt)
            print(f"Tilt → {tilt}")

        elif key == 's':
            tilt -= 1
            tilt = max(-30, tilt)
            freenect.set_tilt_degs(dev, tilt)
            print(f"Tilt → {tilt}")

        elif key == 'r':
            tilt = 0
            freenect.set_tilt_degs(dev, tilt)
            print("Tilt reset → 0")

        # Show accelerometer (optional)
        ax, ay, az = freenect.get_accel(dev)
        print(f"Accel: {ax:.2f} {ay:.2f} {az:.2f}")

        time.sleep(0.05)

    freenect.close_device(dev)
    freenect.shutdown(ctx)

if __name__ == "__main__":
    main()