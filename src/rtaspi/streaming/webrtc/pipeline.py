"""
rtaspi - Real-Time Annotation and Stream Processing
WebRTC GStreamer pipeline generator
"""

import logging
import platform

logger = logging.getLogger(__name__)


class WebRTCPipeline:
    """Handles GStreamer pipeline generation for WebRTC streaming."""

    @staticmethod
    def create_input_pipeline(device) -> str:
        """
        Creates GStreamer input pipeline based on device type and system.

        Args:
            device: Device object with type, driver, and system_path properties.

        Returns:
            str: GStreamer input pipeline or None if unsupported.
        """
        system = platform.system().lower()

        if device.type == "video":
            return WebRTCPipeline._create_video_input_pipeline(device, system)
        elif device.type == "audio":
            return WebRTCPipeline._create_audio_input_pipeline(device, system)

        logger.error(f"Unsupported device type: {device.type}")
        return None

    @staticmethod
    def create_encoding_pipeline(device) -> str:
        """
        Creates GStreamer encoding pipeline based on device type.

        Args:
            device: Device object with type property.

        Returns:
            str: GStreamer encoding pipeline or None if unsupported.
        """
        if device.type == "video":
            return "x264enc tune=zerolatency ! rtph264pay"
        elif device.type == "audio":
            return "audioconvert ! audioresample ! opusenc ! rtpopuspay"

        logger.error(f"Unsupported device type: {device.type}")
        return None

    @staticmethod
    def create_proxy_pipeline(device, source_url: str, transcode: bool = False) -> str:
        """
        Creates GStreamer pipeline for proxying remote streams.

        Args:
            device: Device object with protocol and type properties.
            source_url (str): Source stream URL.
            transcode (bool): Whether to transcode the stream.

        Returns:
            str: GStreamer pipeline for proxying.
        """
        # Input pipeline based on protocol
        if device.protocol == "rtsp":
            input_pipeline = f"rtspsrc location={source_url} ! rtpjitterbuffer"
        elif device.protocol == "rtmp":
            input_pipeline = f"rtmpsrc location={source_url} ! flvdemux"
        else:
            input_pipeline = f"uridecodebin uri={source_url}"

        # Encoding pipeline based on device type and transcode flag
        if transcode:
            if device.type == "video":
                encoding_pipeline = (
                    "decodebin ! videoconvert ! x264enc tune=zerolatency ! rtph264pay"
                )
                if device.protocol == "rtsp":
                    # For RTSP we can use existing encoding
                    encoding_pipeline = "rtph264depay ! h264parse ! rtph264pay"
            else:
                encoding_pipeline = "decodebin ! audioconvert ! opusenc ! rtpopuspay"
                if device.protocol == "rtsp":
                    # For RTSP we can use existing encoding
                    encoding_pipeline = (
                        "rtppcmadepay ! alawdec ! audioconvert ! opusenc ! rtpopuspay"
                    )
        else:
            # Without transcoding - try to pass through
            if device.type == "video":
                if device.protocol == "rtsp":
                    encoding_pipeline = "rtph264depay ! h264parse ! rtph264pay"
                else:
                    encoding_pipeline = "h264parse ! rtph264pay"
            else:
                if device.protocol == "rtsp":
                    encoding_pipeline = (
                        "rtppcmadepay ! alawdec ! audioconvert ! opusenc ! rtpopuspay"
                    )
                else:
                    encoding_pipeline = "audioconvert ! opusenc ! rtpopuspay"

        return f"{input_pipeline} ! {encoding_pipeline}"

    @staticmethod
    def _create_video_input_pipeline(device, system: str) -> str:
        """
        Creates GStreamer input pipeline for video devices.

        Args:
            device: Device object with driver and system_path properties.
            system (str): Operating system name.

        Returns:
            str: GStreamer input pipeline or None if unsupported.
        """
        if system == "linux":
            if device.driver == "v4l2":
                return f"v4l2src device={device.system_path} ! video/x-raw,width=640,height=480 ! videoconvert"
        elif system == "darwin":  # macOS
            if device.driver == "avfoundation":
                return f"avfvideosrc device-index={device.system_path} ! video/x-raw,width=640,height=480 ! videoconvert"
        elif system == "windows":
            if device.driver == "dshow":
                return f'dshowvideosrc device-name="{device.system_path}" ! video/x-raw,width=640,height=480 ! videoconvert'

        logger.error(
            f"Unsupported platform/driver combination: {system}/{device.driver}"
        )
        return None

    @staticmethod
    def _create_audio_input_pipeline(device, system: str) -> str:
        """
        Creates GStreamer input pipeline for audio devices.

        Args:
            device: Device object with driver and system_path properties.
            system (str): Operating system name.

        Returns:
            str: GStreamer input pipeline or None if unsupported.
        """
        if system == "linux":
            if device.driver == "alsa":
                return f"alsasrc device={device.system_path} ! audioconvert"
            elif device.driver == "pulse":
                return f"pulsesrc device={device.system_path} ! audioconvert"
        elif system == "darwin":  # macOS
            if device.driver == "avfoundation":
                return f"avfaudiosrc device-index={device.system_path} ! audioconvert"
        elif system == "windows":
            if device.driver == "dshow":
                return (
                    f'dshowaudiosrc device-name="{device.system_path}" ! audioconvert'
                )

        logger.error(
            f"Unsupported platform/driver combination: {system}/{device.driver}"
        )
        return None
