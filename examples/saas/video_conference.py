"""
Example of implementing a custom video conferencing system with RTASPI
Demonstrates advantages over commercial solutions like Zoom/Teams
"""

from rtaspi.core import rtaspi
from rtaspi.streaming.webrtc import WebRTCServer
from rtaspi.processing.video.pipeline import VideoPipeline
from rtaspi.processing.audio.pipeline import AudioPipeline
from rtaspi.web.interface import WebInterface

class VideoConferenceSystem:
    def __init__(self):
        # Initialize RTASPI with custom configuration
        self.app = rtaspi({
            "webrtc": {
                "stun_servers": ["stun:stun.example.com:3478"],
                "turn_servers": [{
                    "urls": "turn:turn.example.com:3478",
                    "username": "rtaspi",
                    "credential": "secure_password"
                }]
            },
            "security": {
                "encryption": "AES-256-GCM",
                "authentication": "JWT"
            }
        })

        # Initialize WebRTC server for video conferencing
        self.webrtc_server = WebRTCServer(self.app.config)
        
        # Initialize web interface
        self.web_interface = WebInterface(self.app)

    def setup_video_processing(self, user_id):
        """Configure video processing pipeline for a participant"""
        pipeline = VideoPipeline()

        # Add video processing stages
        pipeline.add_stage("background_removal", {
            "model": "selfie_segmentation",
            "blur_background": True
        })

        pipeline.add_stage("face_detection", {
            "model": "mediapipe",
            "enable_landmarks": True
        })

        pipeline.add_stage("video_enhancement", {
            "low_light_enhancement": True,
            "noise_reduction": True,
            "auto_exposure": True
        })

        # Add custom company branding
        pipeline.add_stage("overlay", {
            "logo": "assets/company_logo.png",
            "position": "bottom-right",
            "opacity": 0.8
        })

        return pipeline

    def setup_audio_processing(self, user_id):
        """Configure audio processing pipeline for a participant"""
        pipeline = AudioPipeline()

        # Add audio processing stages
        pipeline.add_stage("noise_suppression", {
            "type": "deep_learning",
            "strength": 0.8
        })

        pipeline.add_stage("echo_cancellation", {
            "type": "adaptive",
            "tail_length_ms": 200
        })

        pipeline.add_stage("voice_enhancement", {
            "clarity_boost": True,
            "volume_normalization": True
        })

        return pipeline

    def create_room(self, room_id, settings=None):
        """Create a new conference room"""
        default_settings = {
            "max_participants": 50,
            "recording_enabled": True,
            "chat_enabled": True,
            "screen_sharing_enabled": True,
            "end_to_end_encryption": True
        }
        room_settings = {**default_settings, **(settings or {})}
        
        return self.webrtc_server.create_room(room_id, room_settings)

    def join_room(self, room_id, user_id, user_name):
        """Handle participant joining a room"""
        # Setup processing pipelines
        video_pipeline = self.setup_video_processing(user_id)
        audio_pipeline = self.setup_audio_processing(user_id)

        # Create participant context
        participant = {
            "id": user_id,
            "name": user_name,
            "video_pipeline": video_pipeline,
            "audio_pipeline": audio_pipeline,
            "video_enabled": True,
            "audio_enabled": True
        }

        # Add participant to room
        self.webrtc_server.add_participant(room_id, participant)

        # Setup data channel for chat and controls
        self.webrtc_server.create_data_channel(room_id, user_id, "chat")
        self.webrtc_server.create_data_channel(room_id, user_id, "control")

        return participant

    def start_recording(self, room_id):
        """Start recording the conference"""
        recording_pipeline = VideoPipeline()
        
        # Configure recording format and quality
        recording_pipeline.add_output("file", {
            "format": "mp4",
            "video_codec": "h264",
            "audio_codec": "aac",
            "directory": f"recordings/{room_id}",
            "filename_pattern": "{timestamp}_{room}_{participant}.mp4",
            "segment_duration": 600  # Split into 10-minute segments
        })

        # Add recording pipeline to room
        self.webrtc_server.add_recording_pipeline(room_id, recording_pipeline)

    def start_server(self, host="0.0.0.0", port=8443):
        """Start the video conference server"""
        # Configure web interface
        self.web_interface.add_route("/", "conference.html")
        self.web_interface.add_route("/api/rooms", "room_api")
        self.web_interface.add_route("/api/participants", "participant_api")

        # Start WebRTC server
        self.webrtc_server.start()

        # Start web interface
        self.web_interface.start(host, port)

        print(f"Video conference server running at https://{host}:{port}")

def main():
    # Create video conference system
    conference_system = VideoConferenceSystem()

    # Create a test room
    room = conference_system.create_room("test_room", {
        "name": "Test Conference",
        "password": "secure123",
        "features": {
            "raise_hand": True,
            "breakout_rooms": True,
            "polls": True
        }
    })

    # Start the server
    try:
        conference_system.start_server()
    except KeyboardInterrupt:
        print("\nShutting down conference system...")
        conference_system.app.shutdown()

if __name__ == "__main__":
    main()
