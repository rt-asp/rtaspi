"""
Basic examples demonstrating core RTASPI functionality.
"""
import time
from rtaspi import RTASPI

def webcam_stream_example():
    """Example of streaming from a USB webcam."""
    # Initialize RTASPI
    rtaspi = RTASPI()
    
    # List available devices
    devices = rtaspi.devices.list()
    print("Available devices:", devices)
    
    # Start RTSP stream from webcam
    stream = rtaspi.streams.start(
        device_id="video0",
        protocol="rtsp",
        path="/webcam",
        settings={
            "video": {
                "codec": "h264",
                "bitrate": "2M"
            }
        }
    )
    
    print(f"Stream available at: rtsp://localhost:8554{stream.path}")
    return stream

def ip_camera_example():
    """Example of connecting to an IP camera."""
    rtaspi = RTASPI()
    
    # Add network camera
    device = rtaspi.devices.add(
        type="network",
        protocol="rtsp",
        address="192.168.1.100",
        port=554,
        username="admin",
        password="secret"
    )
    
    # Start WebRTC stream
    stream = rtaspi.streams.start(
        device_id=device.id,
        protocol="webrtc",
        path="/camera1"
    )
    
    print(f"Stream available at: http://localhost:8080/webrtc{stream.path}")
    return stream

def audio_recording_example():
    """Example of recording audio from a microphone."""
    rtaspi = RTASPI()
    
    # Start RTMP stream from microphone
    stream = rtaspi.streams.start(
        device_id="audio0",
        protocol="rtmp",
        path="/mic",
        settings={
            "audio": {
                "codec": "aac",
                "bitrate": "128k"
            }
        }
    )
    
    # Create recording pipeline
    pipeline = rtaspi.pipelines.create(
        input_stream=stream.id,
        config={
            "output": [{
                "type": "record",
                "format": "mp3",
                "path": "recordings/"
            }]
        }
    )
    
    print(f"Recording to: {pipeline.output[0].path}")
    return pipeline

if __name__ == "__main__":
    # Example usage
    try:
        # Start webcam stream
        webcam = webcam_stream_example()
        print("Webcam stream started")
        
        # Start IP camera stream
        ipcam = ip_camera_example()
        print("IP camera stream started")
        
        # Start audio recording
        recording = audio_recording_example()
        print("Audio recording started")
        
        # Keep streams running for a while
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("Examples stopped by user")
    finally:
        # Cleanup
        rtaspi = RTASPI()
        rtaspi.cleanup()
