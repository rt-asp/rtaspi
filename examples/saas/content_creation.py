"""
Example of implementing a multimedia content creation system with RTASPI
Demonstrates advantages over solutions like OBS Studio/Streamlabs
"""

from rtaspi.core import rtaspi
from rtaspi.streaming.rtmp import RTMPServer
from rtaspi.processing.video.pipeline import VideoPipeline
from rtaspi.processing.audio.pipeline import AudioPipeline
from rtaspi.device_managers.local_devices import LocalDevicesManager

class ContentCreationStudio:
    def __init__(self):
        # Initialize RTASPI with streaming configuration
        self.app = rtaspi({
            "streaming": {
                "rtmp": {
                    "server_url": "rtmp://localhost/live",
                    "stream_key": "test_stream"
                },
                "recording": {
                    "directory": "/var/media/recordings",
                    "format": "mp4"
                }
            },
            "processing": {
                "gpu_acceleration": True,
                "hardware_encoding": True
            }
        })

        # Initialize device manager
        self.device_manager = LocalDevicesManager(self.app.config, self.app.mcp_broker)

        # Initialize RTMP server for streaming
        self.rtmp_server = RTMPServer(self.app.config)

    def setup_sources(self):
        """Setup video and audio sources"""
        # Add webcam
        self.camera = self.device_manager.add_device(
            name="Main Camera",
            type="usb",
            device_path="/dev/video0",
            settings={
                "resolution": "1920x1080",
                "framerate": 60
            }
        )

        # Add microphone
        self.microphone = self.device_manager.add_device(
            name="Main Microphone",
            type="audio",
            device_path="hw:0,0",
            settings={
                "sample_rate": 48000,
                "channels": 2,
                "format": "float32"
            }
        )

        # Add screen capture
        self.screen = self.device_manager.add_screen_capture(
            name="Screen Capture",
            display=":0.0",
            settings={
                "resolution": "1920x1080",
                "framerate": 60,
                "capture_cursor": True
            }
        )

    def create_scene(self, name, layout):
        """Create a scene with specified layout"""
        scene = {
            "name": name,
            "sources": [],
            "transitions": {
                "type": "fade",
                "duration": 500
            }
        }

        if layout == "picture_in_picture":
            scene["sources"] = [
                {
                    "type": "screen_capture",
                    "source": self.screen,
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 1920, "height": 1080}
                },
                {
                    "type": "camera",
                    "source": self.camera,
                    "position": {"x": 1520, "y": 780},
                    "size": {"width": 400, "height": 300},
                    "border": {
                        "color": "#ffffff",
                        "width": 2,
                        "radius": 10
                    }
                }
            ]
        elif layout == "split_screen":
            scene["sources"] = [
                {
                    "type": "screen_capture",
                    "source": self.screen,
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 960, "height": 1080}
                },
                {
                    "type": "camera",
                    "source": self.camera,
                    "position": {"x": 960, "y": 0},
                    "size": {"width": 960, "height": 1080}
                }
            ]

        return scene

    def setup_video_pipeline(self, scene):
        """Create video processing pipeline"""
        pipeline = VideoPipeline()

        # Scene composition
        pipeline.add_stage("scene_composer", {
            "width": 1920,
            "height": 1080,
            "sources": scene["sources"],
            "transitions": scene["transitions"]
        })

        # Add visual effects
        pipeline.add_stage("color_correction", {
            "brightness": 1.1,
            "contrast": 1.2,
            "saturation": 1.1
        })

        pipeline.add_stage("text_overlay", {
            "text": "{username} - Live Stream",
            "font": "Arial",
            "size": 32,
            "color": "#ffffff",
            "position": {"x": 10, "y": 10},
            "background": {
                "color": "#000000",
                "opacity": 0.5
            }
        })

        # Add stream stats overlay
        pipeline.add_stage("stats_overlay", {
            "position": "bottom-left",
            "show_fps": True,
            "show_bitrate": True,
            "show_viewers": True
        })

        # Configure outputs
        pipeline.add_output("rtmp", {
            "url": self.app.config["streaming"]["rtmp"]["server_url"],
            "key": self.app.config["streaming"]["rtmp"]["stream_key"],
            "video": {
                "codec": "h264",
                "bitrate": 6000000,
                "fps": 60,
                "preset": "veryfast"
            },
            "audio": {
                "codec": "aac",
                "bitrate": 160000,
                "sample_rate": 48000
            }
        })

        # Local recording
        pipeline.add_output("file", {
            "directory": self.app.config["streaming"]["recording"]["directory"],
            "format": self.app.config["streaming"]["recording"]["format"],
            "segment_duration": 3600  # Split into 1-hour segments
        })

        return pipeline

    def setup_audio_pipeline(self):
        """Create audio processing pipeline"""
        pipeline = AudioPipeline()

        # Add audio processing stages
        pipeline.add_stage("noise_suppression", {
            "type": "rnnoise",
            "strength": 0.5
        })

        pipeline.add_stage("compressor", {
            "threshold": -20,
            "ratio": 4,
            "attack": 5,
            "release": 50
        })

        pipeline.add_stage("equalizer", {
            "bands": [
                {"frequency": 100, "gain": 2},
                {"frequency": 1000, "gain": 0},
                {"frequency": 5000, "gain": 1}
            ]
        })

        pipeline.add_stage("limiter", {
            "threshold": -3,
            "release": 50
        })

        return pipeline

    def start_streaming(self, scene_name="default", layout="picture_in_picture"):
        """Start the streaming session"""
        # Setup sources
        self.setup_sources()

        # Create scene
        scene = self.create_scene(scene_name, layout)

        # Setup processing pipelines
        video_pipeline = self.setup_video_pipeline(scene)
        audio_pipeline = self.setup_audio_pipeline()

        # Start RTMP server
        self.rtmp_server.start()

        # Start processing pipelines
        self.app.run_pipeline(video_pipeline)
        self.app.run_pipeline(audio_pipeline)

        print(f"Streaming started - RTMP URL: {self.app.config['streaming']['rtmp']['server_url']}")
        print(f"Stream key: {self.app.config['streaming']['rtmp']['stream_key']}")

def main():
    # Create content creation studio
    studio = ContentCreationStudio()

    try:
        # Start streaming with picture-in-picture layout
        studio.start_streaming(
            scene_name="Gaming Stream",
            layout="picture_in_picture"
        )

        # Keep the application running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down streaming...")
        studio.app.shutdown()

if __name__ == "__main__":
    main()
