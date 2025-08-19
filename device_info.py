import cv2
import platform
import psutil
import socket


def is_internet_available(timeout: float = 2.0) -> bool:
    """Return True if internet looks reachable (free, no external services)."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


def get_device_info():
    """Fetch system/device info dynamically"""
    device_name = "Unknown Camera"
    device_model = platform.node()   # System hostname
    connectivity = "Unknown"
    status = "Not Connected"  # camera connection status

    # Try detecting webcam
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)   # Windows में stale issue कम करता है
    if cap is not None and cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:   # ✅ extra check कि frame मिल रहा है
            device_name = "Web Camera"
            status = "Connected"
        else:
            status = "Not Connected"
    else:
        status = "Not Connected"
    if cap is not None:
        cap.release()

    # Network interfaces (USB/LAN/WiFi etc.)
    if_addrs = psutil.net_if_addrs()
    keys = [k.lower() for k in if_addrs.keys()]
    if any("wi-fi" in k or "wlan" in k for k in keys):
        connectivity = "WiFi"
    elif any("eth" in k or "ethernet" in k for k in keys):
        connectivity = "LAN"
    else:
        connectivity = "Integrated/USB"

    return {
        "device_name": device_name,
        "device_model": device_model,
        "connectivity": connectivity,
        "status": status,  # camera status (kept for backward-compat)
        "internet_status": "Online" if is_internet_available() else "Offline",
    }
