"""
Constants for camera configuration.
"""

# Default camera settings
DEFAULT_CAMERA_DEVICE = "0"
DEFAULT_CAMERA_RESOLUTION = "1280x720"
DEFAULT_CAMERA_FRAMERATE = 30

# Stream naming
STREAM_NAME_SUFFIX = "_stream"
RTSP_OUTPUT_SUFFIX = "_rtsp"
RTMP_OUTPUT_SUFFIX = "_rtmp"
WEBRTC_OUTPUT_SUFFIX = "_webrtc"

# Auto-detection settings
AUTO_DETECT_TIMEOUT = 1.0  # seconds
AUTO_DETECT_NAME_PREFIX = "camera_"

# OpenCV capture properties
CV_PROP_FRAME_WIDTH = 3  # cv2.CAP_PROP_FRAME_WIDTH
CV_PROP_FRAME_HEIGHT = 4  # cv2.CAP_PROP_FRAME_HEIGHT
CV_PROP_FPS = 5  # cv2.CAP_PROP_FPS
