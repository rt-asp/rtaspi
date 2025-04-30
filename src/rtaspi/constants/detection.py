"""
Constants for motion and object detection settings.
"""

# Motion detection settings
MOTION_SENSITIVITY = 0.8  # Default sensitivity (0.0 to 1.0)
MOTION_MIN_AREA = 500    # Minimum area size in pixels
MOTION_BLUR_SIZE = 5     # Gaussian blur kernel size

# Motion analysis settings
MOTION_TRIGGER_THRESHOLD = 0.3  # Default trigger threshold (0.0 to 1.0)

# Default motion analysis zones
DEFAULT_ZONES = [
    {
        "name": "entrance",
        "coords": [(0, 0), (640, 0), (640, 480), (0, 480)]
    },
    {
        "name": "parking",
        "coords": [(640, 0), (1280, 0), (1280, 480), (640, 480)]
    }
]
