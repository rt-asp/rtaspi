#!/usr/bin/env python3
"""
Example of WebRTC streaming with RTASPI.
Demonstrates browser-based streaming, peer connections, and media constraints.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import rtaspi.streaming.webrtc as webrtc
from rtaspi.streaming.webrtc.pipeline import WebRTCPipeline
from rtaspi.streaming.webrtc.server import WebRTCServer

# Initialize FastAPI app
app = FastAPI(title="RTASPI WebRTC Streaming Example")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML template for the streaming page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RTASPI WebRTC Streaming</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .video-container {
            position: relative;
            width: 100%;
            background: #000;
            margin-bottom: 20px;
        }
        video {
            width: 100%;
            max-height: 80vh;
        }
        .controls {
            padding: 10px;
            background: rgba(0,0,0,0.8);
            border-radius: 4px;
        }
        button {
            padding: 8px 16px;
            margin: 0 5px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            background: rgba(0,0,0,0.5);
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>RTASPI WebRTC Streaming</h1>
        <div class="video-container">
            <video id="videoElement" autoplay playsinline></video>
        </div>
        <div class="controls">
            <button id="startButton">Start Streaming</button>
            <button id="stopButton">Stop Streaming</button>
        </div>
        <div class="status" id="statusElement"></div>
    </div>

    <script>
        const videoElement = document.getElementById('videoElement');
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        const statusElement = document.getElementById('statusElement');
        let peerConnection = null;
        let ws = null;

        const config = {
            iceServers: [{urls: '{{stun_server}}'}]
        };

        function setStatus(message) {
            statusElement.textContent = message;
        }

        async function startStreaming() {
            try {
                ws = new WebSocket(`ws://${window.location.host}/ws`);
                
                ws.onmessage = async (event) => {
                    const message = JSON.parse(event.data);
                    
                    if (message.type === 'offer') {
                        peerConnection = new RTCPeerConnection(config);
                        
                        peerConnection.ontrack = (event) => {
                            if (event.streams && event.streams[0]) {
                                videoElement.srcObject = event.streams[0];
                            }
                        };
                        
                        peerConnection.onicecandidate = (event) => {
                            if (event.candidate) {
                                ws.send(JSON.stringify({
                                    type: 'ice',
                                    candidate: event.candidate
                                }));
                            }
                        };
                        
                        await peerConnection.setRemoteDescription(message);
                        const answer = await peerConnection.createAnswer();
                        await peerConnection.setLocalDescription(answer);
                        
                        ws.send(JSON.stringify({
                            type: 'answer',
                            sdp: answer
                        }));
                        
                        setStatus('Connected to stream');
                    } else if (message.type === 'ice') {
                        if (peerConnection) {
                            await peerConnection.addIceCandidate(message.candidate);
                        }
                    }
                };
                
                ws.onopen = () => {
                    setStatus('WebSocket connected, waiting for stream...');
                    ws.send(JSON.stringify({type: 'start'}));
                };
                
                ws.onerror = (error) => {
                    setStatus(`WebSocket error: ${error.message}`);
                };
                
                ws.onclose = () => {
                    setStatus('WebSocket connection closed');
                    stopStreaming();
                };
                
            } catch (error) {
                setStatus(`Error: ${error.message}`);
                console.error('Error:', error);
            }
        }

        function stopStreaming() {
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            if (ws) {
                ws.close();
                ws = null;
            }
            videoElement.srcObject = null;
            setStatus('Streaming stopped');
        }

        startButton.onclick = startStreaming;
        stopButton.onclick = stopStreaming;
    </script>
</body>
</html>
"""

class RTSPtoWebRTC:
    def __init__(self, stun_server: str):
        self.stun_server = stun_server
        self.webrtc_server = WebRTCServer()
        self.active_peers: Dict[str, WebRTCPipeline] = {}
    
    async def setup(self):
        """Initialize the WebRTC server."""
        await self.webrtc_server.start()
    
    async def cleanup(self):
        """Cleanup resources."""
        for peer_id in list(self.active_peers.keys()):
            await self.stop_stream(peer_id)
        await self.webrtc_server.stop()
    
    async def start_stream(self, peer_id: str) -> WebRTCPipeline:
        """Start a new WebRTC stream."""
        if peer_id in self.active_peers:
            await self.stop_stream(peer_id)
        
        pipeline = WebRTCPipeline()
        await pipeline.setup()
        self.active_peers[peer_id] = pipeline
        return pipeline
    
    async def stop_stream(self, peer_id: str):
        """Stop an active stream."""
        if peer_id in self.active_peers:
            pipeline = self.active_peers.pop(peer_id)
            await pipeline.cleanup()

# WebSocket connection handler
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    peer_id = str(id(websocket))
    pipeline: Optional[WebRTCPipeline] = None
    
    try:
        while True:
            message = await websocket.receive_json()
            
            if message["type"] == "start":
                pipeline = await rtsp_webrtc.start_stream(peer_id)
                offer = await pipeline.create_offer()
                await websocket.send_json({
                    "type": "offer",
                    "sdp": offer
                })
            
            elif message["type"] == "answer":
                if pipeline:
                    await pipeline.set_remote_description(message["sdp"])
            
            elif message["type"] == "ice":
                if pipeline:
                    await pipeline.add_ice_candidate(message["candidate"])
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    
    finally:
        if peer_id in rtsp_webrtc.active_peers:
            await rtsp_webrtc.stop_stream(peer_id)
        try:
            await websocket.close()
        except:
            pass

@app.get("/")
async def root():
    """Render the streaming page."""
    return HTMLResponse(content=HTML_TEMPLATE.replace(
        "{{stun_server}}", 
        rtsp_webrtc.stun_server
    ))

async def startup():
    """Initialize the application."""
    await rtsp_webrtc.setup()

async def shutdown():
    """Cleanup application resources."""
    await rtsp_webrtc.cleanup()

def main():
    parser = argparse.ArgumentParser(description="RTASPI WebRTC Streaming Example")
    parser.add_argument("--stun", type=str, default="stun.l.google.com:19302",
                       help="STUN server address")
    args = parser.parse_args()
    
    global rtsp_webrtc
    rtsp_webrtc = RTSPtoWebRTC(args.stun)
    
    app.add_event_handler("startup", startup)
    app.add_event_handler("shutdown", shutdown)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
