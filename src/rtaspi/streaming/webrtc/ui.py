"""
rtaspi - Real-Time Annotation and Stream Processing
WebRTC client interface generator
"""

import logging

logger = logging.getLogger(__name__)


class WebRTCUI:
    """Generates HTML/JavaScript UI for WebRTC streaming."""

    @staticmethod
    def generate_client_page(stream_id: str, port: int, stun_server: str) -> str:
        """
        Generate HTML page for WebRTC client.

        Args:
            stream_id (str): Stream identifier.
            port (int): WebSocket port for signaling.
            stun_server (str): STUN server URL.

        Returns:
            str: HTML content for WebRTC client page.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>rtaspi WebRTC Stream {stream_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                video {{ max-width: 100%; max-height: 80vh; }}
                audio {{ width: 100%; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>rtaspi WebRTC Stream</h1>
                <p>Stream ID: {stream_id}</p>

                <div id="mediaContainer">
                    <!-- Media stream container -->
                </div>

                <div>
                    <button id="startButton">Start</button>
                    <button id="stopButton" disabled>Stop</button>
                </div>
            </div>

            <script>
                {WebRTCUI._generate_client_script(stream_id, port, stun_server)}
            </script>
        </body>
        </html>
        """

    @staticmethod
    def _generate_client_script(stream_id: str, port: int, stun_server: str) -> str:
        """
        Generate JavaScript code for WebRTC client.

        Args:
            stream_id (str): Stream identifier.
            port (int): WebSocket port for signaling.
            stun_server (str): STUN server URL.

        Returns:
            str: JavaScript code.
        """
        return f"""
                const mediaContainer = document.getElementById('mediaContainer');
                const startButton = document.getElementById('startButton');
                const stopButton = document.getElementById('stopButton');
                let peerConnection = null;

                async function start() {{
                    startButton.disabled = true;

                    // Get URL parameters
                    const urlParams = new URLSearchParams(window.location.search);
                    const streamId = urlParams.get('stream') || '{stream_id}';

                    try {{
                        // Create video or audio element
                        const mediaType = "{stream_id}".includes('video') ? 'video' : 'audio';
                        const mediaElement = document.createElement(mediaType);
                        mediaElement.controls = true;
                        mediaElement.autoplay = true;
                        mediaElement.id = 'stream';
                        mediaContainer.appendChild(mediaElement);

                        // WebRTC configuration
                        const configuration = {{
                            iceServers: [
                                {{ urls: '{stun_server.replace("stun://", "stun:")}' }}
                            ]
                        }};

                        peerConnection = new RTCPeerConnection(configuration);

                        // Handle incoming streams
                        peerConnection.ontrack = (event) => {{
                            console.log('Received stream', event);
                            mediaElement.srcObject = event.streams[0];
                        }};

                        // Connect to signaling server
                        const wsUrl = `ws://localhost:{port}/rtc/${{streamId}}`;
                        const ws = new WebSocket(wsUrl);

                        ws.onopen = async () => {{
                            console.log('Connected to signaling server');

                            // Create SDP offer
                            const offer = await peerConnection.createOffer();
                            await peerConnection.setLocalDescription(offer);

                            // Send offer to server
                            ws.send(JSON.stringify({{
                                type: 'offer',
                                sdp: peerConnection.localDescription
                            }}));
                        }};

                        ws.onmessage = async (event) => {{
                            const message = JSON.parse(event.data);

                            if (message.type === 'answer') {{
                                // Received SDP answer
                                await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
                            }} else if (message.type === 'candidate') {{
                                // Received ICE candidate
                                await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
                            }}
                        }};

                        // Handle WebSocket errors
                        ws.onerror = (error) => {{
                            console.error('WebSocket error:', error);
                            alert('Cannot connect to signaling server');
                        }};

                        stopButton.disabled = false;
                    }} catch (error) {{
                        console.error('Error starting WebRTC stream:', error);
                        alert('Error starting WebRTC stream: ' + error.message);
                        startButton.disabled = false;
                    }}
                }}

                function stop() {{
                    if (peerConnection) {{
                        peerConnection.close();
                        peerConnection = null;
                    }}

                    const mediaElement = document.getElementById('stream');
                    if (mediaElement) {{
                        mediaElement.remove();
                    }}

                    startButton.disabled = false;
                    stopButton.disabled = true;
                }}

                startButton.addEventListener('click', start);
                stopButton.addEventListener('click', stop);

                // Auto-start stream
                window.addEventListener('load', start);
        """
