"""
Integration examples demonstrating how to integrate RTASPI with other systems.
"""
import json
import asyncio
import websockets
import requests
from typing import Dict, List, Optional

class RTASPIClient:
    """Client for interacting with RTASPI's REST API."""
    
    def __init__(self, base_url: str, token: str):
        """Initialize the RTASPI client.
        
        Args:
            base_url: Base URL of the RTASPI API
            token: Authentication token
        """
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def list_devices(self) -> List[Dict]:
        """Get list of all devices."""
        response = requests.get(
            f'{self.base_url}/api/devices',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['devices']
    
    def start_stream(
        self,
        device_id: str,
        protocol: str,
        path: str,
        settings: Optional[Dict] = None
    ) -> Dict:
        """Start a new stream.
        
        Args:
            device_id: ID of the source device
            protocol: Streaming protocol to use
            path: Stream path/endpoint
            settings: Optional stream settings
            
        Returns:
            Stream information
        """
        response = requests.post(
            f'{self.base_url}/api/streams',
            headers=self.headers,
            json={
                'device_id': device_id,
                'protocol': protocol,
                'path': path,
                'settings': settings or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def create_pipeline(self, config: Dict) -> Dict:
        """Create a new processing pipeline.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Pipeline information
        """
        response = requests.post(
            f'{self.base_url}/api/pipelines',
            headers=self.headers,
            json=config
        )
        response.raise_for_status()
        return response.json()

class RTASPIWebSocket:
    """Client for RTASPI's WebSocket API."""
    
    def __init__(self, ws_url: str):
        """Initialize the WebSocket client.
        
        Args:
            ws_url: WebSocket URL
        """
        self.ws_url = ws_url
        self.websocket = None
    
    async def connect(self):
        """Connect to the WebSocket server."""
        self.websocket = await websockets.connect(self.ws_url)
    
    async def subscribe(self, topics: List[str]):
        """Subscribe to event topics.
        
        Args:
            topics: List of topics to subscribe to
        """
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        await self.websocket.send(json.dumps({
            'type': 'subscribe',
            'topics': topics
        }))
    
    async def listen(self):
        """Listen for WebSocket messages."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle different event types
                if data['type'] == 'device_status':
                    print(f"Device status update: {data}")
                elif data['type'] == 'stream_status':
                    print(f"Stream status update: {data}")
                elif data['type'] == 'pipeline_event':
                    print(f"Pipeline event: {data}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")

async def websocket_example():
    """Example of using the WebSocket API."""
    # Create WebSocket client
    ws_client = RTASPIWebSocket('ws://localhost:8081/api/ws')
    
    try:
        # Connect to WebSocket
        await ws_client.connect()
        
        # Subscribe to topics
        await ws_client.subscribe([
            'devices/status',
            'streams/status',
            'pipelines/events'
        ])
        
        # Listen for events
        await ws_client.listen()
        
    except Exception as e:
        print(f"WebSocket error: {e}")

def rest_api_example():
    """Example of using the REST API."""
    # Create REST API client
    client = RTASPIClient('http://localhost:8081', 'your-token')
    
    try:
        # List all devices
        devices = client.list_devices()
        print("Available devices:", devices)
        
        # Start a stream
        stream = client.start_stream(
            device_id='video0',
            protocol='rtsp',
            path='/webcam',
            settings={
                'video': {
                    'codec': 'h264',
                    'bitrate': '2M'
                }
            }
        )
        print("Stream started:", stream)
        
        # Create a pipeline
        pipeline = client.create_pipeline({
            'id': 'motion_detection',
            'input': {'stream_id': stream['id']},
            'stages': [
                {
                    'type': 'motion_detector',
                    'sensitivity': 0.8
                }
            ],
            'output': [
                {
                    'type': 'webhook',
                    'url': 'http://localhost:8000/events'
                }
            ]
        })
        print("Pipeline created:", pipeline)
        
    except requests.exceptions.RequestException as e:
        print(f"API error: {e}")

def web_app_integration():
    """Example of integrating with a web application."""
    # This would typically be in your web application's JavaScript code
    javascript_example = """
    // Connect to WebSocket API
    const ws = new WebSocket('ws://localhost:8081/api/ws');

    // Subscribe to events
    ws.send(JSON.stringify({
        type: 'subscribe',
        topics: ['devices/status', 'streams/status']
    }));

    // Handle events
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch(data.type) {
            case 'device_status':
                updateDeviceStatus(data);
                break;
            case 'stream_status':
                updateStreamStatus(data);
                break;
        }
    };

    // Start WebRTC stream
    async function startStream(deviceId) {
        const response = await fetch('http://localhost:8081/api/streams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                device_id: deviceId,
                protocol: 'webrtc',
                path: '/stream1'
            })
        });
        
        const data = await response.json();
        const player = new RTCPeerConnection();
        // ... WebRTC setup code ...
    }
    """
    print("JavaScript integration example:")
    print(javascript_example)

if __name__ == "__main__":
    # REST API example
    print("\nRunning REST API example...")
    rest_api_example()
    
    # WebSocket example
    print("\nRunning WebSocket example...")
    asyncio.get_event_loop().run_until_complete(websocket_example())
    
    # Web app integration example
    print("\nWeb application integration example...")
    web_app_integration()
