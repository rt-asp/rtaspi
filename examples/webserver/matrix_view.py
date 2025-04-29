#!/usr/bin/env python3
"""
Example of creating a matrix view for multiple camera streams.
Demonstrates layout management and stream synchronization.
"""

import yaml
import argparse
from pathlib import Path
from typing import List, Tuple
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import rtaspi.streaming as streaming
from rtaspi.web.interface import WebInterface

app = FastAPI(title="RTASPI Matrix View Example")
web_interface = WebInterface()

# HTML template for the matrix view
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RTASPI Matrix View</title>
    <style>
        .matrix-container {
            display: grid;
            gap: 10px;
            padding: 10px;
            background: #1a1a1a;
            height: 100vh;
        }
        .stream-container {
            position: relative;
            background: #000;
            overflow: hidden;
        }
        .stream-container video {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .stream-title {
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 5px 10px;
            border-radius: 4px;
        }
        body {
            margin: 0;
            background: #000;
        }
    </style>
</head>
<body>
    <div id="matrix" class="matrix-container">
        <!-- Streams will be inserted here -->
    </div>
    <script>
        const config = {{config|tojson}};
        
        function setupMatrix() {
            const matrix = document.getElementById('matrix');
            matrix.style.gridTemplateColumns = `repeat(${config.layout.columns}, 1fr)`;
            
            config.streams.forEach(stream => {
                const container = document.createElement('div');
                container.className = 'stream-container';
                container.style.gridColumn = stream.position[1] + 1;
                container.style.gridRow = stream.position[0] + 1;
                
                const video = document.createElement('video');
                video.autoplay = true;
                video.controls = true;
                video.muted = true;
                
                const title = document.createElement('div');
                title.className = 'stream-title';
                title.textContent = stream.name;
                
                container.appendChild(video);
                container.appendChild(title);
                matrix.appendChild(container);
                
                // Connect to stream
                const ws = new WebSocket(`ws://${window.location.host}/ws/stream/${stream.name}`);
                ws.onmessage = async (event) => {
                    const blob = new Blob([event.data], {type: 'video/mp4'});
                    try {
                        const mediaSource = new MediaSource();
                        video.src = URL.createObjectURL(mediaSource);
                        mediaSource.addEventListener('sourceopen', () => {
                            const sourceBuffer = mediaSource.addSourceBuffer('video/mp4; codecs="avc1.42E01E"');
                            sourceBuffer.appendBuffer(await blob.arrayBuffer());
                        });
                    } catch (error) {
                        console.error('Error playing stream:', error);
                    }
                };
            });
        }
        
        document.addEventListener('DOMContentLoaded', setupMatrix);
    </script>
</body>
</html>
"""

class MatrixView:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.streams = {}
        
    @staticmethod
    def load_config(config_path: str) -> dict:
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    async def setup_streams(self):
        """Initialize all streams from configuration."""
        for stream_config in self.config["streams"]:
            stream = streaming.RTSPStream(stream_config["url"])
            self.streams[stream_config["name"]] = stream
            await stream.connect()
    
    async def cleanup_streams(self):
        """Cleanup all active streams."""
        for stream in self.streams.values():
            await stream.disconnect()

@app.get("/", response_class=HTMLResponse)
async def root(request):
    """Render the matrix view page."""
    return HTMLResponse(content=HTML_TEMPLATE.replace(
        "{{config|tojson}}", 
        web_interface.json_encode(matrix_view.config)
    ))

@app.websocket("/ws/stream/{stream_name}")
async def stream_endpoint(websocket: WebSocket, stream_name: str):
    """WebSocket endpoint for streaming video data."""
    await websocket.accept()
    
    if stream_name not in matrix_view.streams:
        await websocket.close(code=4000, reason=f"Stream {stream_name} not found")
        return
        
    stream = matrix_view.streams[stream_name]
    try:
        while True:
            frame = await stream.get_frame()
            if frame is not None:
                await websocket.send_bytes(frame)
            await asyncio.sleep(0.033)  # ~30 fps
    except Exception as e:
        print(f"Error in stream {stream_name}: {e}")
    finally:
        await websocket.close()

def main():
    parser = argparse.ArgumentParser(description="RTASPI Matrix View Example")
    parser.add_argument("--config", type=str, default="matrix_config.yaml",
                       help="Path to matrix configuration file")
    args = parser.parse_args()
    
    global matrix_view
    matrix_view = MatrixView(args.config)
    
    # Setup and run
    asyncio.run(matrix_view.setup_streams())
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080)
    finally:
        asyncio.run(matrix_view.cleanup_streams())

if __name__ == "__main__":
    main()
