"""
Advanced examples demonstrating RTASPI's more complex features.
"""
from rtaspi import RTASPI

def motion_detection_pipeline():
    """Example of creating a motion detection pipeline with object detection."""
    rtaspi = RTASPI()
    
    # Create pipeline configuration
    pipeline_config = {
        "id": "security_cam",
        "input": {
            "stream_id": "camera1"
        },
        "stages": [
            {
                "type": "motion_detector",
                "sensitivity": 0.8,
                "region": [0, 0, 1920, 1080],
                "min_area": 1000
            },
            {
                "type": "object_detector",
                "model": "yolov3",
                "confidence": 0.5,
                "classes": ["person", "car"]
            },
            {
                "type": "event_trigger",
                "conditions": [
                    {
                        "type": "motion",
                        "duration": 5
                    },
                    {
                        "type": "object",
                        "classes": ["person"]
                    }
                ]
            }
        ],
        "output": [
            {
                "type": "webhook",
                "url": "http://localhost:8000/alerts"
            },
            {
                "type": "record",
                "format": "mp4",
                "duration": 30,
                "pre_buffer": 5
            }
        ]
    }
    
    # Create and start the pipeline
    pipeline = rtaspi.pipelines.create(config=pipeline_config)
    print(f"Motion detection pipeline '{pipeline.id}' created")
    return pipeline

def multi_camera_setup():
    """Example of setting up multiple cameras with different configurations."""
    rtaspi = RTASPI()
    
    # Configure multiple streams
    streams_config = {
        "streams": [
            {
                "id": "entrance_cam",
                "device_id": "ipcam1",
                "protocol": "rtsp",
                "path": "/entrance",
                "settings": {
                    "video": {
                        "codec": "h264",
                        "bitrate": "2M",
                        "framerate": 30
                    },
                    "audio": {
                        "enabled": False
                    }
                }
            },
            {
                "id": "parking_cam",
                "device_id": "ipcam2",
                "protocol": "rtmp",
                "path": "/parking",
                "settings": {
                    "video": {
                        "codec": "h264",
                        "bitrate": "1M",
                        "framerate": 15
                    },
                    "audio": {
                        "enabled": False
                    }
                }
            },
            {
                "id": "reception_cam",
                "device_id": "video0",
                "protocol": "webrtc",
                "path": "/reception",
                "settings": {
                    "video": {
                        "codec": "vp8",
                        "bitrate": "1.5M"
                    },
                    "audio": {
                        "enabled": True,
                        "codec": "opus"
                    }
                }
            }
        ]
    }
    
    # Start all streams
    active_streams = []
    for stream_config in streams_config["streams"]:
        stream = rtaspi.streams.start(
            device_id=stream_config["device_id"],
            protocol=stream_config["protocol"],
            path=stream_config["path"],
            settings=stream_config["settings"]
        )
        active_streams.append(stream)
        print(f"Started stream: {stream.id}")
    
    return active_streams

def video_processing_pipeline():
    """Example of creating a video processing pipeline with multiple effects."""
    rtaspi = RTASPI()
    
    pipeline_config = {
        "id": "video_effects",
        "input": {
            "stream_id": "webcam_stream"
        },
        "stages": [
            {
                "type": "resize",
                "width": 1280,
                "height": 720
            },
            {
                "type": "color_correction",
                "brightness": 1.2,
                "contrast": 1.1,
                "saturation": 1.1
            },
            {
                "type": "overlay",
                "text": "%timestamp%",
                "position": [10, 10],
                "font": "Arial",
                "size": 24
            },
            {
                "type": "face_detection",
                "model": "face_detection_v1",
                "blur_faces": True
            }
        ],
        "output": [
            {
                "type": "rtmp",
                "url": "rtmp://localhost/live/processed"
            },
            {
                "type": "webrtc",
                "path": "/processed"
            }
        ]
    }
    
    # Create and start the pipeline
    pipeline = rtaspi.pipelines.create(config=pipeline_config)
    print(f"Video processing pipeline '{pipeline.id}' created")
    return pipeline

def audio_processing_pipeline():
    """Example of creating an audio processing pipeline with effects."""
    rtaspi = RTASPI()
    
    pipeline_config = {
        "id": "audio_effects",
        "input": {
            "stream_id": "mic_stream"
        },
        "stages": [
            {
                "type": "noise_reduction",
                "strength": 0.7
            },
            {
                "type": "equalizer",
                "bands": [
                    {"frequency": 100, "gain": -3},
                    {"frequency": 1000, "gain": 2},
                    {"frequency": 8000, "gain": 1}
                ]
            },
            {
                "type": "compressor",
                "threshold": -20,
                "ratio": 4,
                "attack": 5,
                "release": 50
            },
            {
                "type": "speech_detection",
                "language": "en",
                "output_format": "srt"
            }
        ],
        "output": [
            {
                "type": "rtmp",
                "url": "rtmp://localhost/live/processed_audio"
            },
            {
                "type": "file",
                "path": "subtitles.srt"
            }
        ]
    }
    
    # Create and start the pipeline
    pipeline = rtaspi.pipelines.create(config=pipeline_config)
    print(f"Audio processing pipeline '{pipeline.id}' created")
    return pipeline

if __name__ == "__main__":
    try:
        # Setup motion detection
        motion_pipeline = motion_detection_pipeline()
        
        # Setup multiple cameras
        camera_streams = multi_camera_setup()
        
        # Setup video processing
        video_pipeline = video_processing_pipeline()
        
        # Setup audio processing
        audio_pipeline = audio_processing_pipeline()
        
        print("\nAll pipelines and streams are running.")
        print("Press Ctrl+C to stop...")
        
        # Keep the script running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all pipelines and streams...")
    finally:
        # Cleanup
        rtaspi = RTASPI()
        rtaspi.cleanup()
