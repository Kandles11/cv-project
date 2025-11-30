# drawer_logic.py

def _map_depth_value(d: int) -> str:
    # keep mapping identical to your previous logic (ranges inclusive/exclusive tuned)
    try:
        d = int(d)
    except Exception:
        return "unknown"

    if 891 < d < 920:
        return "no drawer open"
    if 861 < d <= 890:
        return "bin 1"
    if 841 < d <= 860:
        return "bin 2"
    if 826 < d <= 840:
        return "bin 3"
    if 801 < d <= 825:
        return "bin 4"
    if 780 < d <= 800:
        return "bin 5"
    return "unknown"

def detect_drawer(depth_frame):
    """
    depth_frame - numpy 2D array. Uses the same hard-coded points you had.
    Returns {"left": "...", "right": "..."}
    """
    h, w = depth_frame.shape[:2]
    # clamp coordinates to array bounds (avoids IndexError)
    left_pt = (485, 367)
    right_pt = (243, 385)

    def safe_get(x, y):
        if 0 <= y < h and 0 <= x < w:
            return int(depth_frame[y, x])
        return None

    left_val = safe_get(*left_pt)
    right_val = safe_get(*right_pt)

    return {
        "left": _map_depth_value(left_val) if left_val is not None else "unknown",
        "right": _map_depth_value(right_val) if right_val is not None else "unknown",
        "left_raw": left_val,
        "right_raw": right_val
    }